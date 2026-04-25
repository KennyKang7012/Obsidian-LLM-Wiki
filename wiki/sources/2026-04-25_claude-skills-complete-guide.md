---
title: The Complete Guide to Building Skills for Claude
type: source
tags: [claude, skills, MCP, anthropic, AI-agent]
created: 2026-04-25
updated: 2026-04-25
sources: [The-Complete-Guide-to-Building-Skill-for-Claude.pdf]
related: [Claude-Skills.md, MCP-Model-Context-Protocol.md, Progressive-Disclosure.md, Anthropic.md, Claude.md]
---

## 來源資訊
- **原始檔案**：`raw/The-Complete-Guide-to-Building-Skill-for-Claude.pdf`
- **類型**：官方技術指南
- **作者**：Anthropic
- **頁數**：30 頁
- **日期**：2026 年初（文中提及 January 2026 的分發模型）

---

## 核心論點

Claude Skills 是一種以資料夾為單位的「可攜帶工作流程套件」，讓使用者只需教一次特定的流程與領域知識，Claude 往後就能自動套用，不需在每次對話中重新解釋。Skills 和 MCP 的關係是互補的：MCP 提供工具連線能力（What Claude can do），Skills 提供最佳工作流程知識（How Claude should do it）。

---

## 關鍵洞見

- **Skills 的本質是「固化的 Prompt 工程」**：把一次性花時間找到的最佳對話方式，封裝成永久的技能，讓 Claude 每次都能複現。
- **三層漸進式揭露（Progressive Disclosure）是核心設計**：YAML frontmatter 永遠載入（用於觸發判斷），SKILL.md 主體在相關時載入，linked files 按需讀取。此設計最小化 token 消耗。
- **description 欄位是成敗關鍵**：格式為「做什麼 + 何時使用 + 關鍵能力」，需在 1024 字元內，必須包含使用者真實會說的觸發語句。太模糊（如 "Helps with projects"）會導致 skill 永遠不被觸發。
- **Skill 是開放標準**：Anthropic 已將 Agent Skills 發布為開放標準，設計上跨平台可攜，不綁定 Claude。
- **最有效的開發路徑**：先在單一困難任務上反覆迭代直到成功，再將成功的方法提取成 Skill，最後才擴展到多個測試案例。
- **`skill-creator` 工具**：內建的 skill，可在 15–30 分鐘內生成第一個可用的 skill 草稿。

---

## 重要資料與細節

### Skill 的資料夾結構
```
your-skill-name/
├── SKILL.md          # 必要，大小寫敏感
├── scripts/          # 可選，Python/Bash 等執行程式碼
├── references/       # 可選，詳細文件
└── assets/           # 可選，模板、圖示等
```

### YAML frontmatter 必填欄位
| 欄位 | 規則 |
|------|------|
| `name` | kebab-case，無空格無大寫，需與資料夾名稱一致 |
| `description` | 1024 字元以內，含觸發語句，無 XML 標籤 |

### 三大使用案例類別
1. **Document & Asset Creation**：產生文件、簡報、程式碼（不需 MCP）
2. **Workflow Automation**：跨多步驟、多 MCP 的自動化流程
3. **MCP Enhancement**：強化既有 MCP 連線的使用體驗

### 五大實作模式
| 模式 | 適用場景 |
|------|----------|
| Sequential workflow orchestration | 有固定順序的多步驟流程 |
| Multi-MCP coordination | 需要跨多個服務協作 |
| Iterative refinement | 輸出品質需要迭代改善 |
| Context-aware tool selection | 相同目標、依上下文選不同工具 |
| Domain-specific intelligence | Skill 本身就是領域知識的載體 |

### 測試的三個維度
- **Triggering tests**：確保 skill 在對的時機被載入（目標：90% 相關 query 觸發）
- **Functional tests**：驗證輸出正確、API 呼叫成功、錯誤處理有效
- **Performance comparison**：與無 skill 的基準比較（token 消耗、往返次數）

### 分發方式（2026 年 1 月現況）
- 個人：下載資料夾 → 上傳至 Claude.ai Settings > Capabilities > Skills 或放入 Claude Code skills 目錄
- 組織：Admin 統一部署至 workspace（2025 年 12 月起支援）
- API：透過 `container.skills` 參數，需搭配 Code Execution Tool beta

---

## 與既有知識的關聯

此為知識庫的**第一份來源**，建立了幾個基礎概念頁面：
- [[Claude-Skills.md]]：Skill 的完整定義與機制
- [[MCP-Model-Context-Protocol.md]]：與 Skill 互補的連線層
- [[Progressive-Disclosure.md]]：核心設計哲學，在本知識庫的 CLAUDE.md 架構設計中也有體現

---

## 尚待釐清的問題

- Skill 在 Claude Code 的觸發機制與 Claude.ai 是否完全相同？
- `compatibility` 欄位的具體撰寫方式與跨平台測試流程為何？
- 「Skills in the Agent SDK」的實際整合方式？
- 開放標準在非 Anthropic 平台（如 OpenAI）的採用現況？
