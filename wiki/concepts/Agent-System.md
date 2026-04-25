---
title: 多 Agent 系統設計
type: concept
tags: [multi-agent, agent-design, verification, role-separation]
created: 2026-04-25
updated: 2026-04-25
sources: [2026-04-25_claude-code-architecture-v2.md]
related: [Claude-Code-Architecture.md, Claude-Skills.md, Claude.md]
---

## 定義

多 Agent 系統是將不同職責分配給不同 Agent 的架構設計。核心出發點：讓一個 Agent 同時負責研究、規劃、實現、驗證，每件事都做不好。職責拆開之後，每個 Agent 可以有針對性的工具集、權限模式和系統提示詞。

---

## 運作原理

### Claude Code 的 6 個內建 Agent

| Agent | 核心職責 | 關鍵限制 |
|-------|----------|----------|
| **General Purpose Agent** | 通用任務執行 | 主力 Agent |
| **Explore Agent** | 代碼庫探索 | 純只讀：禁止創建/修改/刪除文件，禁止任何改變系統狀態的命令；只能用 Glob、Grep、FileRead，Bash 只允許 `ls`/`git status`/`git log` |
| **Plan Agent** | 制定計劃 | 只規劃，不執行任何代碼 |
| **Verification Agent** | 對抗性驗證 | 「try to break it」，130 行 prompt，輸出 VERDICT: PASS/FAIL/PARTIAL |
| **Claude Code Guide Agent** | 使用指引 | - |
| **Statusline Setup Agent** | 狀態欄配置 | - |

### Explore Agent 的設計邏輯

Explore Agent 被設計得「極端只讀」，原因直接：探索階段如果不小心改了東西，後面實現階段就會出問題。把權限徹底隔離，是一個樸素但有效的安全設計。

性能優化：外部用戶默認使用 Haiku 模型（更快更便宜）。探索不需要最強的推理能力，速度更重要。

### Verification Agent：最精心設計的 prompt

Verification Agent 的 130 行 prompt 是整個源碼裡最精心設計的一段文本。它核心方向只有一件事：「想辦法搞壞它」（try to break it）。

它專門對抗兩種常見的驗證失敗模式：
1. **Verification avoidance**：只看代碼，不跑測試，寫個 PASS 就走了
2. **被前 80% 迷惑**：UI 看著不錯、測試也過了，就忽略剩下 20% 的問題

prompt 還列出了驗證者常見的逃避藉口，然後要求「識別你自己的合理化傾向」：
- 「代碼看起來是對的」→ 看是不是驗證。跑一下。
- 「實現者的測試已經通過了」→ 實現者也是 LLM。獨立驗證。
- 「大概沒問題」→ 大概不是驗證。跑一下。
- 「這個太費時間了」→ 不是你說了算的。

每個檢查項必須包含實際執行的命令和觀察到的輸出。

### Fork path vs. Normal path

子 Agent 啟動時有兩條路徑：

- **Fork path**：繼承主線程的 system prompt、完整對話上下文、工具集，盡量保持字節級一致。目的是讓 API 請求的前綴一樣，從而復用主線程的 prompt cache。源碼注釋明確：fork 不應該換模型，因為換模型會改變 system prompt 裡的模型描述字段，破壞 cache 前綴匹配。
- **Normal path**：全新的上下文，適合需要乾淨起點的任務。

設計哲學差異：
> 普通人做子 Agent 調度，想的是「子任務能跑起來就行」。Claude Code 想的是「子任務能跑起來，**而且盡量復用主線程的緩存**」。

### 任務系統（tasks/）

5 種任務類型，支持完整的生命週期管理：

| 任務類型 | 說明 |
|----------|------|
| DreamTask | 自主後台任務 |
| LocalAgentTask | 本地 Agent 任務（前台/後台/異步） |
| RemoteAgentTask | 遠程 Agent 任務 |
| InProcessTeammateTask | 進程內 teammate |
| LocalShellTask | Shell 任務 |

後台 Agent 有獨立的 abort controller，完成後通過 notification 回到主線程。前台 Agent 可以在執行過程中被轉成後台。

---

## 優點與限制

**優點**
- 角色拆開後每個 Agent 可以有針對性的工具集和權限，不需要給所有 Agent 最高權限
- Verification Agent 的對抗性設計有效對抗「自己寫的代碼自己驗收」的偏見問題
- Fork path 的 cache 優化讓子任務不需要重新付出 cache miss 的代價

**限制**
- 多 Agent 增加了系統複雜度和調試難度
- Verification Agent 需要很具體的驗證指令（前端要啟 dev server + 瀏覽器自動化；後端要 curl；CLI 要看 stdout/stderr/exit code）——泛用性依賴 prompt 品質
- Agent 間的狀態同步和生命週期管理是「產品化的難點」（第二天問題）

---

## 在本知識庫的應用

「把角色拆開」這個設計原則直接影響了本 wiki 的操作模式：
- **使用者**：負責提供來源（Explore 的角色）和方向決策（Plan 的角色）
- **LLM Wiki Agent**：負責消化、整合、維護（Implementation 的角色）
- 未來可考慮加入「健檢（lint）」作為獨立操作，讓 Agent 扮演 Verification 的角色

---

## 相關頁面
- [[Claude-Code-Architecture.md]]
- [[Claude-Skills.md]]
- [[Claude.md]]
