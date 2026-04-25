# LLM Wiki — 個人知識庫系統

> 以 LLM 為核心的持續累積型個人知識庫，而非一次性的 RAG 查詢工具。

## 概念

大多數人用 LLM 處理文件的方式是 **RAG**：上傳文件，查詢時檢索相關片段，LLM 生成回答。這個流程沒有記憶，沒有累積——每次問問題都從零開始推導。

這個系統的做法不同：LLM 扮演**知識庫程式設計師**的角色，在你每次加入新來源時，主動讀取、整合、更新一份持久的 Markdown Wiki。Wiki 會隨著每次 ingest 越來越豐富：交叉引用已經就緒，矛盾已被標記，合成已反映所有你讀過的東西。

```
傳統 RAG                           LLM Wiki
───────────────────────────────    ───────────────────────────────────
來源 → 索引 ──┐                   來源 → LLM 整合 → Wiki（持久化）
              ↓ 每次查詢重算           ↓ 一次建立，持續累積
         LLM 回答                  LLM 回答（引用既有 Wiki）
```

---

## 目錄結構

```
Obsidian-Wiki/
│
├── CLAUDE.md              # 核心 Schema：LLM Agent 的完整操作規則
├── README.md              # 本文件
├── index.md               # Wiki 全站目錄（Agent 自動維護）
├── log.md                 # 操作日誌，只增不減（Agent 自動維護）
│
├── raw/                   # 原始來源（不可修改）
│   ├── assets/            # 從文章下載的附件圖片
│   └── *.pdf / *.md       # 論文、報告、文章等原始資料
│
├── wiki/                  # LLM 維護的知識庫（唯一寫入者：LLM Agent）
│   ├── sources/           # 每份來源各一頁摘要
│   ├── entities/          # 人物、組織、產品、工具
│   ├── concepts/          # 概念、方法論、框架
│   └── analyses/          # 查詢結果、比較分析、儲存的洞見
│
└── dashboard/             # 查詢儀表板（Streamlit App）
    ├── app.py
    ├── providers.py       # LLM Provider 抽象層
    ├── wiki_search.py     # 本地搜尋引擎
    ├── requirements.txt
    └── .env.example
```

---

## 快速開始

### 1. 前置需求

- [Obsidian](https://obsidian.md/)（選用，但強烈推薦用來瀏覽 Wiki）
- [Claude Code](https://claude.ai/code)（或其他支援此 Schema 的 LLM CLI）
- Python 3.10+（儀表板用）

### 2. 在 Claude Code 中使用

在這個目錄中開啟 Claude Code。Agent 會自動讀取 `CLAUDE.md` 取得完整操作規範。

```bash
cd /path/to/Obsidian-Wiki
claude  # 開啟 Claude Code
```

### 3. 啟動查詢儀表板

```bash
# 安裝相依套件
pip install -r dashboard/requirements.txt

# 設定 API Key（選擇性，純檢索模式不需要）
cp dashboard/.env.example dashboard/.env
# 編輯 .env，填入你的 API Key

# 啟動
streamlit run dashboard/app.py
```

瀏覽器開啟後預設在 `http://localhost:8501`。

---

## 三種操作模式

### Ingest（消化新來源）

把新文件放入 `raw/`，然後告訴 Agent：

```
消化這份文件：raw/your-article.pdf
```

Agent 會：
1. 讀取來源並與你討論關鍵洞見
2. 在 `wiki/sources/` 建立來源摘要頁
3. 更新或新建相關的 entity 和 concept 頁面
4. 更新 `index.md` 和 `log.md`

單份來源通常觸及 5–15 個 wiki 頁面。

### Query（查詢知識庫）

直接向 Agent 提問：

```
Claude Skills 和 MCP 的主要差異是什麼？
Claude Code 的主循環是如何運作的？
```

Agent 讀取 `index.md` 找到相關頁面，整合後回答並附上引用。回答值得保留時，可存入 `wiki/analyses/`。

### Lint（健檢）

定期執行，保持 Wiki 品質：

```
請對 Wiki 進行健檢
```

Agent 會掃描並回報：互相矛盾的說法、孤兒頁、缺乏獨立頁面的重要概念、格式問題，以及建議的新研究方向。

---

## 查詢儀表板

儀表板提供兩種模式，可在左側切換：

| 模式 | 說明 | 需要 API Key |
|------|------|:---:|
| **📖 純檢索** | 即時搜尋本地 Wiki，顯示匹配頁面與高亮摘要 | 否 |
| **🤖 LLM 查詢** | 搜尋 Wiki 後由 LLM 整合成自然語言回答，支援多輪對話 | 是 |

### 支援的 LLM Provider

| Provider | 圖示 | 需要 Key | 說明 |
|----------|:----:|:--------:|------|
| Anthropic | 🟠 | 是 | claude-sonnet-4-6 等 |
| OpenAI | 🟢 | 是 | gpt-4o 等 |
| Google Gemini | 🔵 | 是 | gemini-2.0-flash 等，走 OpenAI 相容端點 |
| Ollama（本地） | 🦙 | 否 | llama3.2、qwen2.5 等本地模型 |
| NVIDIA NIM | 🟩 | 是 | llama-3.1-nemotron-70b 等 |

### API Key 設定

**方式一：環境變數（推薦）**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="AIza..."
export NVIDIA_API_KEY="nvapi-..."
```

**方式二：`.env` 檔案**

```bash
cp dashboard/.env.example dashboard/.env
# 編輯 .env 填入你的 Key
```

**方式三：在儀表板介面直接輸入**（不存檔，關閉後失效）

---

## Schema 規範（`CLAUDE.md`）

`CLAUDE.md` 是整個系統的核心，定義了：

- **目錄結構與命名規範**：每個資料夾的用途、檔案命名格式
- **Frontmatter 格式**：每頁的 YAML metadata 規範
- **三種操作流程**：Ingest / Query / Lint 的詳細步驟
- **寫作規範**：來源摘要頁、Entity 頁、Concept 頁各自的格式模板
- **交叉引用規範**：Obsidian `[[內部連結]]` 的使用方式
- **Log 格式**：操作記錄的標準格式

每次開啟新對話時，Agent 應先讀取 `CLAUDE.md` 確保操作一致性。

---

## Wiki 頁面格式

所有 Wiki 頁面都包含 YAML frontmatter：

```yaml
---
title: 頁面標題
type: source | entity | concept | analysis
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [來源檔名]
related: [相關頁面.md]
---
```

交叉引用使用 Obsidian 格式：`[[頁面名稱]]`

---

## 建議的 Obsidian 設定

1. **附件資料夾**：Settings → Files and links → Attachment folder path → `raw/assets/`
2. **下載附件快捷鍵**：Settings → Hotkeys → 搜尋「Download attachments」→ 綁定 `Ctrl+Shift+D`
3. **推薦插件**：
   - Graph view（查看知識圖譜）
   - Dataview（查詢 frontmatter 建立動態表格）
   - Marp（從 Wiki 直接生成簡報）

---

## 工作流程範例

```
你（提供來源）        LLM Agent（維護 Wiki）      Obsidian（瀏覽）
      │                        │                        │
      │── 新增 raw/paper.pdf ──▶│                        │
      │                        │── 讀取、整合、寫入 ──▶ │
      │◀── 摘要 + 討論 ─────── │   wiki/sources/        │
      │                        │   wiki/concepts/       │
      │                        │   wiki/entities/       │
      │                        │── 更新 index.md ──────▶│
      │                        │── 更新 log.md ────────▶│
      │                        │                        │
      │── 問：「X 和 Y 的差異？」│                        │
      │                        │── 讀取相關頁面 ─────── │
      │◀── 整合回答 + 引用 ─── │                        │
      │── 儲存到 analyses/ ───▶│── 建立分析頁面 ───────▶│
```

---

## 授權

本知識庫為個人使用，wiki 內容著作權歸原始來源作者所有。
