---
title: Claude Code 源碼架構深度解析 V2.0
type: source
tags: [claude-code, architecture, source-code, agent-system, reverse-engineering]
created: 2026-04-25
updated: 2026-04-25
sources: [ai-agent-deep-dive-v2.pdf]
related: [Claude-Code-Architecture.md, Agent-System.md, Claude-Skills.md, MCP-Model-Context-Protocol.md, Claude.md, Xiao-Tan.md]
---

## 來源資訊
- **原始檔案**：`raw/ai-agent-deep-dive-v2.pdf`
- **類型**：獨立研究報告（逆向工程分析）
- **作者**：Xiao Tan（[@tvytlx](https://x.com/tvytlx)，微信公眾號 Xiao Tan AI）
- **頁數**：21 頁
- **日期**：April 1, 2026
- **分析素材**：Claude Code 的 npm 包，從 `cli.js.map` 的 `sourcesContent` 中提取出約 4,756 個 TypeScript 原始文件

---

## 核心論點

Claude Code 表面是一個 CLI 工具，但從源碼規模和架構來看，它是一個完整的 **Agent Operating System**：擁有主循環、多 Agent 調度、工具治理流水線、三層安全防護、四道上下文壓縮機制，以及完整的產品化生命周期管理。理解它的架構，等於理解了下一代 AI Agent 系統工程的設計方式。

---

## 關鍵洞見

- **規模即訊號**：市面上大多數開源 coding agent 的 `src/` 只有一個 main、一個 prompt、幾個 tool、一個 utils。Claude Code 的 `src/` 頂層有超過 50 個模組目錄。這個差距不是功能差距，是工程成熟度的差距。
- **query.ts 是整個系統的心臟**：1,729 行的狀態機，用 `while(true)` 取代遞歸（早期版本遞歸調用，長對話會爆棧），每次 continue 就是一次狀態轉換，9 個不同的 continue 點。
- **Streaming Tool Execution**：傳統做法等模型輸出完整再執行工具。Claude Code 的 `StreamingToolExecutor` 在模型還在輸出時，已完成的 `tool_use` block 就開始執行——這讓用戶感知延遲大幅下降。
- **Prompt Cache 經濟學**：`SYSTEM_PROMPT_DYNAMIC_BOUNDARY` 把系統提示詞切成靜態前半（可緩存）和動態後半（每次重算），明確的成本意識設計。
- **Verification Agent 是「整個系統最狠的 prompt」**：130 行專門設計來「try to break it」，列出驗證者常見的逃避藉口，強制要求輸出 VERDICT: PASS/FAIL/PARTIAL。
- **Hook 強大但受控**：Hook 有足夠表達力做運行時策略調整，但不能繞過核心安全模型——Hook allow 不能繞過 settings deny。這種「強大但受控」是工程成熟度的標誌。
- **MCP 不只是工具橋**：當 MCP server 連接時，如果 server 提供了 `instructions`，這些 instructions 會被拼進 system prompt。模型不只知道「有這個工具」，還知道「什麼時候該用、怎麼用」。

---

## 重要資料與細節

### 代碼庫規模
| 模組 | 文件數 |
|------|--------|
| utils/ | 564 |
| components/ | 389 |
| commands/ | 207 |
| tools/ | 184 |
| services/ | 130 |
| hooks/ | 104 |
| ink/ (TUI) | 96 |
| bridge/ (遠程/IDE) | 31 |
| skills/ | 20 |
| tasks/ | 12 |

| 關鍵文件 | 行數 |
|----------|------|
| main.tsx | 4,683 |
| toolExecution.ts | 1,745 |
| query.ts（主循環） | 1,729 |
| AgentTool.tsx | 1,397 |
| QueryEngine.ts | 1,295 |
| runAgent.ts | 973 |
| prompts.ts | 914 |
| Tool.ts（工具基類） | 792 |

### 主循環每次迭代的 10 個步驟（query.ts）
1. 上下文預處理（四道壓縮）
2. Token 預算檢查
3. 調用模型 API
4. 流式處理響應
5. 錯誤恢復（413 觸發 reactive compact，輸出超限注入恢復消息）
6. Stop hooks
7. Token budget 檢查
8. 工具執行（`runTools()` 或 `StreamingToolExecutor`）
9. 附件注入（memory、skill discovery、queued commands）
10. 回到循環開頭

### 四道上下文壓縮機制（依優先順序）
1. **Snip Compact**：裁剪歷史消息中過長的部分
2. **Micro Compact**：基於 `tool_use_id` 的細粒度壓縮
3. **Context Collapse**：把不活躍的上下文區域折疊成摘要
4. **Auto Compact**：Token 總量近閾值時觸發全量壓縮
- 備用：**Reactive Compact**：收到 API 413 後立即觸發緊急壓縮，有防循環設計

### 工具執行 14 步流水線
1. 找工具（名稱/別名）→ 2. 解析 MCP 元數據 → 3. Zod schema 校驗 → 4. validateInput() → 5. Speculative classifier（BashTool 提前預判風險）→ 6. PreToolUse hooks → 7. 解析 Hook 權限結果 → 8. 走權限決策 → 9. 修正輸入 → 10. 執行 tool.call() → 11. Analytics/tracing/OTel → 12. PostToolUse hooks → 13. 處理結果 → 14. PostToolUseFailure hooks

### 三層安全防護網
| 層 | 機制 | 職責 |
|----|------|------|
| 第一層 | Speculative Classifier | BashTool 提前預判命令風險等級，並行運行不阻塞 |
| 第二層 | Hook Policy Layer | PreToolUse hooks 可做權限決策、修改輸入、阻斷流程 |
| 第三層 | Permission Decision | 綜合規則配置和用戶交互的最終決策 |
三層互相配合但互不繞過。

### 六個內建 Agent
| Agent | 職責 | 特點 |
|-------|------|------|
| General Purpose Agent | 通用任務執行 | 主力 |
| Explore Agent | 代碼探索 | 純只讀，外部用戶默認 Haiku 模型 |
| Plan Agent | 規劃 | 只規劃，不執行 |
| Verification Agent | 對抗性驗證 | 130 行 prompt，「try to break it」 |
| Claude Code Guide Agent | 使用指引 | - |
| Statusline Setup Agent | 狀態欄配置 | - |

### 從源碼提煉出的 7 個設計原則
1. **不信任模型的自覺性** → 行為寫進 prompt，不靠臨場發揮
2. **把角色拆開** → 至少把「做事的人」和「驗收的人」分開
3. **工具調用要治理** → 14 步 pipeline，不是「模型說要調就調」
4. **上下文是預算** → 能緩存要緩存，能按需加載不要一開始就塞進去
5. **安全層要互不繞過** → 任何一層出問題，整體安全性不會崩潰
6. **生態的關鍵是模型感知** → 插件再多，模型不知道有什麼，等於沒有
7. **產品化在於處理第二天** → 任務中斷恢復、狀態清理、進程泄漏處理

---

## 與既有知識的關聯

- **補充** [[Claude-Skills.md]]：從源碼確認 skills/ 下有 17 個 bundled skills（verify、commit、loop、simplify 等），且 Skill 按需注入——匹配到才注入，不會在啟動時全部塞進上下文。
- **補充** [[MCP-Model-Context-Protocol.md]]：揭示了 MCP 的隱藏能力——除了工具連線，MCP server 還可以注入 behavior instructions 進 system prompt，讓模型知道「什麼時候用這個工具、怎麼用」。
- **新建** [[Claude-Code-Architecture.md]]：此報告是該頁面的主要來源。
- **新建** [[Agent-System.md]]：多 Agent 設計的詳細說明。
- **對比** [[2026-04-25_claude-skills-complete-guide.md]]（Anthropic 官方指南）：官方指南說的是外部使用者如何建立 Skill；此報告看的是 Claude Code 內部如何實作 Skill 系統——兩者視角互補，無矛盾。

---

## 尚待釐清的問題

- Fork path 與 normal path 的具體觸發條件是什麼？（什麼情況下子 Agent 會 fork vs. 走 normal path？）
- Plugin 和 Skill 的邊界：Plugin 是更底層的擴展（影響 prompt、工具、權限規則），Skill 是上層工作流——但兩者如何共存？
- Verification Agent 的 130 行 prompt 具體內容是否已被公開？
- `tasks/` 下的 5 種任務類型（DreamTask、LocalAgentTask、RemoteAgentTask、InProcessTeammateTask、LocalShellTask）的適用場景？
