---
title: Claude Skills
type: concept
tags: [claude, skills, workflow, automation]
created: 2026-04-25
updated: 2026-04-25
sources: [2026-04-25_claude-skills-complete-guide.md]
related: [MCP-Model-Context-Protocol.md, Progressive-Disclosure.md, Anthropic.md, Claude.md]
---

## 定義

Claude Skill 是一個**以資料夾為單位的可攜帶工作流程套件**，包含 Markdown 指令與可選的腳本，用來教 Claude 如何處理特定任務或工作流程。使用者教一次，往後每次對話 Claude 都會自動套用。

---

## 運作原理

### 資料夾結構
```
your-skill-name/
├── SKILL.md          # 必要：Markdown 格式的主指令
├── scripts/          # 可選：Python/Bash 等執行程式碼
├── references/       # 可選：詳細技術文件
└── assets/           # 可選：模板、圖示、字型等
```

### 載入機制（三層漸進式揭露）
見 [[Progressive-Disclosure.md]]。

### YAML frontmatter 必填規則
- `name`：kebab-case，無空格無大寫，與資料夾同名
- `description`：1024 字元以內，包含「做什麼 + 何時觸發 + 關鍵能力」

description 的黃金公式：
> `[做什麼] + [何時使用] + [關鍵能力]`

**好的範例**：
```yaml
description: Analyzes Figma design files and generates developer handoff documentation.
  Use when user uploads .fig files, asks for "design specs" or "design-to-code handoff".
```

**不好的範例**：
```yaml
description: Helps with projects.  # 太模糊，永遠不觸發
description: Implements the Project entity model with hierarchical relationships.  # 太技術，無觸發語句
```

---

## 三大使用案例類別

| 類別 | 用途 | 特點 |
|------|------|------|
| Document & Asset Creation | 產生文件、簡報、程式碼 | 不需 MCP，使用 Claude 內建能力 |
| Workflow Automation | 多步驟、跨系統的自動化 | 通常搭配 MCP，有驗證閘門 |
| MCP Enhancement | 強化既有 MCP 連線體驗 | 提供領域知識與最佳實踐 |

---

## 五大實作模式

1. **Sequential workflow orchestration**：有固定順序的多步驟流程，含依賴關係與回滾指令
2. **Multi-MCP coordination**：跨多個服務（如 Figma → Drive → Linear → Slack），有明確的 phase 分隔
3. **Iterative refinement**：含 Quality Check 與 Refinement Loop，直到達到品質門檻
4. **Context-aware tool selection**：決策樹式工具選擇（如依檔案大小選儲存位置）
5. **Domain-specific intelligence**：將合規規則、業務邏輯等領域知識嵌入 skill 邏輯

---

## 優點與限制

**優點**
- 一次建立，每次對話自動生效，無需重複解釋
- 跨平台可攜（Claude.ai、Claude Code、API）
- 開放標準，設計上與平台無關
- 與 MCP 互補，形成完整的「工具 + 知識」組合

**限制**
- SKILL.md 建議控制在 5,000 字以內，否則可能拖慢回應
- 同時啟用超過 20–50 個 skills 可能造成 context 負擔
- 觸發邏輯完全依賴 description 欄位，撰寫不當就無法自動載入
- API 使用需搭配 Code Execution Tool beta（尚在早期階段）

---

## 從源碼視角看 Skill（[[2026-04-25_claude-code-architecture-v2.md]]）

Claude Code 源碼（`src/skills/`）包含 17 個 bundled skills，包括：`verify`、`commit`、`loop`、`simplify`、`stuck`、`debug` 等。

關鍵實作細節：
- **按需注入**：Skill 匹配到才注入進上下文，不會在啟動時全部塞進去——這正是 [[Progressive-Disclosure.md]] 的實踐
- **系統強制**：系統要求模型在任務匹配到某個 skill 時必須調用 Skill tool 執行，不能只是提到這個 skill 而不執行
- **Skill 可聲明** `allowed-tools`、`model`、`effort hints`，在注入當前上下文時生效

Skill 的形態是帶 frontmatter metadata 的 markdown 文件，與 Anthropic 官方指南的說明一致。

## 在本知識庫的應用

本知識庫的 CLAUDE.md Schema 本身即是一種 Skill 的應用——透過結構化指令告訴 LLM 如何維護 wiki，概念上與 Skill 的「固化最佳工作流程」完全一致。

---

## 相關頁面
- [[MCP-Model-Context-Protocol.md]]
- [[Progressive-Disclosure.md]]
- [[Anthropic.md]]
- [[Claude.md]]
