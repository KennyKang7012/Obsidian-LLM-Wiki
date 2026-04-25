---
title: MCP（Model Context Protocol）
type: concept
tags: [MCP, protocol, tools, integration]
created: 2026-04-25
updated: 2026-04-25
sources: [2026-04-25_claude-skills-complete-guide.md]
related: [Claude-Skills.md, Claude.md, Anthropic.md]
---

## 定義

MCP（Model Context Protocol）是讓 Claude 連接到外部服務與工具的協定層，提供即時的資料存取與工具呼叫能力。

---

## 運作原理

MCP 扮演「專業廚房」的角色，提供食材（資料）與設備（工具）；[[Claude-Skills.md]] 則扮演「食譜」的角色，告訴 Claude 如何使用這些工具。

| 維度 | MCP（連線層） | Skills（知識層） |
|------|--------------|-----------------|
| 提供什麼 | 工具連線、即時資料 | 工作流程、最佳實踐 |
| 回答問題 | Claude 能做什麼 | Claude 應該怎麼做 |
| 舉例 | 連接到 Notion/Linear/Figma | 教 Claude 如何做 sprint planning |

---

## 優點與限制

**優點**
- 提供 Claude 即時存取外部系統的能力
- 工具調用標準化，跨對話可複現

**限制**
- MCP 本身不包含工作流程知識：沒有 Skills 的情況下，使用者必須每次手動引導 Claude 如何使用工具
- 每次對話從零開始，知識不累積

---

## MCP 的隱藏能力：行為說明注入

從 Claude Code 源碼（[[2026-04-25_claude-code-architecture-v2.md]]）揭示了一個 Anthropic 官方文件未強調的細節：

> 當 MCP server 連接時，如果 server 提供了 `instructions`，這些 instructions 會被拼進 system prompt。

這意味著一個 MCP server 能同時給模型兩樣東西：
1. **新工具**（透過 MCP 協定注冊）
2. **怎麼用這些工具的說明**（透過 instructions 注入 prompt）

模型不只知道「有這個工具」，還知道「什麼時候該用、怎麼用」。這讓 MCP 的價值遠高於一個簡單的工具注冊表。

## 在本知識庫的應用

本知識庫目前使用 Google Drive、Gmail、Google Calendar 等 MCP 工具。MCP 提供存取能力，而 CLAUDE.md Schema 提供操作知識——正好體現了 MCP + Skills 的互補架構。

---

## 相關頁面
- [[Claude-Skills.md]]
- [[Progressive-Disclosure.md]]
- [[Claude.md]]
