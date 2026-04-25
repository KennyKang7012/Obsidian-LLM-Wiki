---
title: Xiao Tan
type: entity
tags: [researcher, author, claude-code, reverse-engineering]
created: 2026-04-25
updated: 2026-04-25
sources: [2026-04-25_claude-code-architecture-v2.md]
related: [Claude-Code-Architecture.md, Agent-System.md, Claude.md]
---

## 概述

Xiao Tan 是一位 AI 系統研究者，以逆向工程方式對 Claude Code 源碼進行深度分析，發布了系列研究報告。

---

## 關鍵事實
- X（Twitter）：[@tvytlx](https://x.com/tvytlx)
- 微信公眾號：Xiao Tan AI
- 小紅書：tvytlx
- 研究方法：從 Claude Code 的 npm 包中提取 `cli.js.map` 的 `sourcesContent`，還原出約 4,756 個 TypeScript 原始文件進行分析
- 在本知識庫中的代表性作品：
  - `ai-agent-deep-dive-report.pdf`（V1）— Claude Code 源碼深度研究報告
  - `ai-agent-deep-dive-v2.pdf`（V2）— Claude Code 源碼架構深度解析（從 4756 個文件里讀懂 Agent 系統工程）

---

## 在本知識庫的角色

本知識庫的「Claude Code 技術理解」層面主要依賴 Xiao Tan 的逆向研究，與 [[Anthropic.md]] 官方視角形成互補：官方視角告訴你「如何使用」，Xiao Tan 的研究告訴你「內部如何運作」。

---

## 相關頁面
- [[Claude-Code-Architecture.md]]
- [[Agent-System.md]]
- [[Anthropic.md]]
