---
title: Progressive Disclosure（漸進式揭露）
type: concept
tags: [design-pattern, context-management, token-efficiency]
created: 2026-04-25
updated: 2026-04-25
sources: [2026-04-25_claude-skills-complete-guide.md]
related: [Claude-Skills.md, MCP-Model-Context-Protocol.md]
---

## 定義

Progressive Disclosure 是一種資訊分層載入的設計模式：只在需要時才提供對應層級的資訊，避免一次性將所有內容塞入 context，以最小化 token 消耗同時維持完整功能。

---

## 運作原理

在 [[Claude-Skills.md]] 中，這套機制分三層：

| 層級 | 位置 | 何時載入 | 目的 |
|------|------|----------|------|
| **第一層** | YAML frontmatter | 永遠載入（系統提示詞） | 讓 Claude 判斷是否該使用此 skill |
| **第二層** | SKILL.md 主體 | Claude 認為 skill 相關時 | 完整的指令與工作流程 |
| **第三層** | 連結的附屬檔案 | Claude 認為需要更多細節時 | 詳細技術文件、模板、範例 |

第一層的 YAML frontmatter 永遠在系統提示詞中，負責觸發判斷；第二、三層依需求動態載入，維持 context 效率。

---

## 優點與限制

**優點**
- Token 效率高：不需要的資訊不佔用 context
- 擴展性好：skill 可成長而不影響基礎載入成本
- 邏輯清晰：每層職責明確分離

**限制**
- 第一層（description）的品質決定一切——寫得不好 skill 就不會被觸發
- 需要作者主動設計哪些內容放哪一層
- Claude 判斷是否載入第二層有一定的不確定性

---

## 在本知識庫的應用

本知識庫的 `index.md` 設計也體現了 Progressive Disclosure 的精神：
- **第一層**：`index.md` 的頁面列表與一行摘要（快速定位）
- **第二層**：個別 wiki 頁面的完整內容（詳細閱讀）
- **第三層**：原始來源文件（驗證細節）

查詢時先讀 index，確認相關頁面後再鑽入——這正是漸進式揭露的精神。

---

## 相關頁面
- [[Claude-Skills.md]]
- [[MCP-Model-Context-Protocol.md]]
