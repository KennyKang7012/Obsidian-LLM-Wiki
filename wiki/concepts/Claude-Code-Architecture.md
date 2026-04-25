---
title: Claude Code 架構
type: concept
tags: [claude-code, architecture, agent-system, source-code]
created: 2026-04-25
updated: 2026-04-25
sources: [2026-04-25_claude-code-architecture-v2.md]
related: [Agent-System.md, Claude-Skills.md, MCP-Model-Context-Protocol.md, Progressive-Disclosure.md, Claude.md]
---

## 定義

Claude Code 的本質是一個 **Agent Operating System**，而非只是一個 CLI 工具。其源碼約 4,756 個 TypeScript 文件，頂層有超過 50 個模組目錄，包含完整的主循環、多 Agent 調度、工具治理、安全防護、上下文壓縮，以及產品化生命周期管理。

---

## 運作原理

### 一個請求的完整生命週期

```
cli.tsx（fast-path 分發）
  → main.tsx（初始化狀態、注冊工具、構造 ToolUseContext）
    → query()
      → queryLoop() [while(true) 狀態機]
        → 上下文壓縮 → 調用 API → 流式處理 → 工具執行 → 下一輪
```

### 主循環：query.ts（1,729 行狀態機）

`query.ts` 是整個系統的心臟，使用 `while(true)` + state 物件取代遞歸（早期版本遞歸調用，長對話會爆棧）。每次迭代 10 個步驟：

| 步驟 | 說明 |
|------|------|
| 1. 上下文預處理 | 四道壓縮機制依序執行 |
| 2. Token 預算檢查 | 若關閉 auto compact 則檢查是否快撞硬限制 |
| 3. 調用模型 API | 把消息、system prompt、工具定義發給模型 |
| 4. 流式處理響應 | 邊收邊處理，已完成的 tool_use block 立刻執行 |
| 5. 錯誤恢復 | 413 → reactive compact；輸出超限 → 注入恢復消息 |
| 6. Stop hooks | 模型停止輸出後，運行 stop hooks |
| 7. Token budget | 有 budget 設定則檢查是否繼續 |
| 8. 工具執行 | 批量執行，通過 `runTools()` 或 `StreamingToolExecutor` |
| 9. 附件注入 | memory attachments、skill discovery、queued commands |
| 10. 下一輪 | 把結果組裝成新消息列表，回到循環開頭 |

### Streaming Tool Execution（邊收邊跑）

傳統做法：等模型輸出完整 → 收齊所有 `tool_use` block → 串行或並行執行。

Claude Code 做法：`StreamingToolExecutor` — 模型還在輸出時，已完成的 `tool_use` block 就開始執行。一次 turn 裡有 5 個工具調用，傳統做法要等 5–30 秒模型輸出完，Claude Code 在模型還在生成第二個工具時第一個工具就跑完了。

### Prompt 組裝（prompts.ts，914 行）

系統提示詞分兩大塊，由 `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` 標記分隔：

**靜態部分**（可緩存，不應隨意修改）：
- `getSimpleIntroSection()` — 身份定位
- `getSimpleSystemSection()` — 系統運行規範
- `getSimpleDoingTasksSection()` — **行為規範（整個 prompt 最有價值的部分）**
- `getActionsSection()` — 風險動作規範
- `getUsingYourToolsSection()` — 工具使用語法
- `getSimpleToneAndStyleSection()` — 語氣風格
- `getOutputEfficiencySection()` — 輸出效率

**動態部分**（按會話狀態注入）：
- Session guidance（當前啟用了哪些工具）
- Memory（CLAUDE.md 內容）
- 環境信息（OS、shell、cwd、模型名稱）
- MCP server instructions
- Token budget 說明

### 工具執行 14 步流水線（toolExecution.ts，1,745 行）

不是「模型說要調就調」，中間有完整的治理：

1. 找工具 → 2. 解析 MCP 元數據 → 3. Zod schema 校驗 → 4. validateInput() → 5. **Speculative Classifier**（BashTool 提前預判風險，並行運行）→ 6. **PreToolUse hooks** → 7. 解析 Hook 權限結果 → 8. **權限決策** → 9. 修正輸入 → 10. 執行 tool.call() → 11. 記錄 analytics/tracing → 12. **PostToolUse hooks** → 13. 處理結果 → 14. **PostToolUseFailure hooks**

### 三層安全防護網

| 層 | 機制 | 關鍵特性 |
|----|------|----------|
| 第一層 | Speculative Classifier | 提前預判，並行運行，不阻塞主流程 |
| 第二層 | Hook Policy Layer | 可做決策、修改輸入、阻斷流程，但不能繞過 settings deny |
| 第三層 | Permission Decision | 最終決策，綜合 Hook 結果 + 規則配置 + 用戶交互 |

**核心規則**：`Hook allow ≠ 繞過 settings deny`。任何一層出問題，整體安全性不崩潰。

### 四道上下文壓縮機制

| 機制 | 觸發 | 作用 |
|------|------|------|
| Snip Compact | 主動 | 裁剪過長的歷史消息 |
| Micro Compact | 主動 | 基於 tool_use_id 的細粒度壓縮 |
| Context Collapse | 主動 | 把不活躍的上下文折疊成摘要 |
| Auto Compact | Token 近閾值 | 全量壓縮 |
| Reactive Compact | API 413 | 緊急壓縮後重試，有防循環設計 |

輕量壓縮（snip、micro）優先；若能壓到閾值以下，重量壓縮就不需要跑。

### Prompt Cache 經濟學

API 層可以對 system prompt 做前綴緩存——如果兩次請求的 system prompt 前綴完全一樣（字節級一致），第二次可以跳過對前綴部分的處理。

`SYSTEM_PROMPT_DYNAMIC_BOUNDARY` 的存在，說明 Anthropic 在設計 system prompt 時已將緩存成本納入考量：**把不變的放前面，把會變的放後面**，緩存命中率就上去了。源碼注釋寫得很直白：不要隨意修改 boundary 之前的內容，否則會破壞緩存。

---

## 優點與限制

**優點**
- 架構清晰，每個模組職責明確
- fail-closed 默認值（忘記聲明安全性 → 系統默認不安全，走更嚴格的權限檢查）
- Streaming 執行大幅降低用戶感知延遲
- 緩存意識深入到架構設計層面

**限制**
- 複雜度高，4,756 個文件對外部理解和維護來說門檻高
- 工具執行 14 步 pipeline 每次都要走，overhead 不可忽視
- 靜態 prompt 部分一旦修改就破壞緩存，維護有約束

---

## 在本知識庫的應用

本 wiki 系統本身就是一個 Agent 系統的具體應用：LLM Wiki Agent 有明確的行為規範（CLAUDE.md），使用 [[Progressive-Disclosure.md]] 分層讀取信息，通過 index.md 和 log.md 維護狀態——這與 Claude Code 的 prompt 組裝（靜態規則 + 動態狀態注入）、主循環設計（每次迭代讀取上下文再決策）在思路上高度一致。

---

## 相關頁面
- [[Agent-System.md]]
- [[Claude-Skills.md]]
- [[MCP-Model-Context-Protocol.md]]
- [[Progressive-Disclosure.md]]
- [[Claude.md]]
