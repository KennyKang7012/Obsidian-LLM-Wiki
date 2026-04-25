"""
Wiki 知識庫查詢儀表板
執行方式：streamlit run dashboard/app.py
"""
from __future__ import annotations
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from providers import PROVIDERS_CONFIG, create_provider
from wiki_search import WikiSearcher

WIKI_ROOT = Path(__file__).parent.parent

# ── 頁面設定 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wiki 知識庫查詢",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { max-width: 980px; }
    .result-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        background: #fafafa;
    }
    .score-badge {
        background: #e8f4f8;
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 0.75em;
        color: #1a6b8a;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
DEFAULTS = {
    "llm_messages": [],
    "saved_files": set(),
    "retrieval_results": [],
    "retrieval_query": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

searcher = WikiSearcher(WIKI_ROOT)
stats = searcher.get_stats()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("📚 Wiki 查詢")

    # ── 模式選擇 ──────────────────────────────────────────────────────────────
    st.subheader("查詢模式")
    mode = st.radio(
        "選擇模式",
        options=["retrieval", "llm"],
        format_func=lambda m: "📖  純檢索（無需 API Key）" if m == "retrieval" else "🤖  LLM 查詢",
        label_visibility="collapsed",
    )

    st.divider()

    # ── LLM 設定（純檢索模式下摺疊）────────────────────────────────────────
    if mode == "llm":
        st.subheader("LLM Provider 設定")

        provider_key = st.selectbox(
            "Provider",
            options=list(PROVIDERS_CONFIG.keys()),
            format_func=lambda k: f"{PROVIDERS_CONFIG[k]['icon']}  {PROVIDERS_CONFIG[k]['name']}",
        )
        cfg = PROVIDERS_CONFIG[provider_key]

        if cfg["models"]:
            model = st.selectbox("模型", options=cfg["models"])
        else:
            model = st.text_input(
                "模型名稱",
                value=cfg["default_model"],
                placeholder="llama3.2 / qwen2.5 …",
            )

        api_key = ""
        if cfg["needs_api_key"]:
            env_val = os.environ.get(cfg.get("env_key", ""), "")
            api_key = st.text_input(
                f"API Key",
                type="password",
                value=env_val,
                placeholder=cfg.get("env_key", "API_KEY"),
                help=f"環境變數：{cfg.get('env_key', '')}",
            )
            if not api_key and not env_val:
                st.warning("⚠️ 尚未設定 API Key", icon="🔑")

        base_url = cfg.get("base_url") or ""
        if cfg["needs_base_url"]:
            base_url = st.text_input(
                "Base URL",
                value=cfg.get("default_base_url", ""),
            )

        st.divider()
        show_context = st.toggle("顯示傳給 LLM 的 Context", value=False)

    else:
        # 純檢索模式：Provider 設定不需要
        provider_key = "anthropic"
        cfg = PROVIDERS_CONFIG[provider_key]
        model = ""
        api_key = ""
        base_url = ""
        show_context = False
        st.info("純檢索模式不需要 API Key，直接搜尋本地 Wiki。", icon="📖")

    # ── 搜尋設定（兩個模式都有）──────────────────────────────────────────────
    st.subheader("🔍 搜尋設定")
    top_k = st.slider("最多顯示頁面數", min_value=1, max_value=15, value=5)

    # ── Wiki 統計 ─────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 知識庫狀態")
    c1, c2 = st.columns(2)
    c1.metric("總頁面", stats["total_pages"])
    c2.metric("來源", stats["sources"])
    c3, c4 = st.columns(2)
    c3.metric("概念", stats["concepts"])
    c4.metric("分析", stats["analyses"])

    with st.expander("📂 Wiki 索引預覽"):
        st.text_area(
            label="",
            value=searcher.load_index(),
            height=160,
            disabled=True,
            label_visibility="collapsed",
        )

    with st.expander("📋 最近操作"):
        st.text(searcher.load_log(last_n=6))

    # ── 清除 ──────────────────────────────────────────────────────────────────
    st.divider()
    if st.button("🗑️ 清除記錄", use_container_width=True, type="secondary"):
        st.session_state.llm_messages = []
        st.session_state.saved_files = set()
        st.session_state.retrieval_results = []
        st.session_state.retrieval_query = ""
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 輔助函式
# ══════════════════════════════════════════════════════════════════════════════
def highlight_query(text: str, query: str, max_chars: int = 600) -> str:
    """截取包含 query 的段落，回傳 Markdown 格式。"""
    idx = text.lower().find(query.lower())
    if idx == -1:
        snippet = text[:max_chars]
    else:
        start = max(0, idx - 100)
        end = min(len(text), idx + max_chars)
        snippet = ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")

    # 高亮關鍵字（簡單替換）
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    snippet = pattern.sub(lambda m: f"**{m.group()}**", snippet)
    return snippet


def save_analysis(query: str, answer: str, pages: list[tuple[str, float]]) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^\w一-鿿]", "-", query[:40]).strip("-")
    filename = f"{today}_{slug}.md"
    save_path = WIKI_ROOT / "wiki" / "analyses" / filename
    sources_str = ", ".join(p for p, _ in pages)
    page_list = "\n".join(f"- [[{p}]] （相關度 {s:.1f}）" for p, s in pages)
    content = f"""---
title: {query[:100]}
type: analysis
tags: [query, auto-generated]
created: {today}
updated: {today}
sources: [{sources_str}]
related: []
---

## 查詢問題

{query}

## 回答

{answer}

## 參考頁面

{page_list}
"""
    save_path.write_text(content, encoding="utf-8")
    return save_path


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — 標題
# ══════════════════════════════════════════════════════════════════════════════
if mode == "retrieval":
    st.title("📖 Wiki 純檢索")
    st.caption(f"本地搜尋 · Wiki 路徑：`{WIKI_ROOT}` · 共 {stats['total_pages']} 頁")
else:
    st.title("🤖 Wiki LLM 查詢")
    st.caption(
        f"{cfg['icon']} **{cfg['name']}** · 模型：`{model}` · "
        f"Wiki：`{WIKI_ROOT}`"
    )


# ══════════════════════════════════════════════════════════════════════════════
# 模式 A：純檢索
# ══════════════════════════════════════════════════════════════════════════════
if mode == "retrieval":

    # ── 搜尋框 ────────────────────────────────────────────────────────────────
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        retrieval_query = st.text_input(
            "搜尋關鍵字",
            value=st.session_state.retrieval_query,
            placeholder="輸入關鍵字搜尋 Wiki，例如：Progressive Disclosure",
            label_visibility="collapsed",
        )
    with col_btn:
        do_search = st.button("🔍 搜尋", use_container_width=True, type="primary")

    if do_search and retrieval_query:
        st.session_state.retrieval_query = retrieval_query
        with st.spinner("搜尋中..."):
            results = searcher.search(retrieval_query, top_k=top_k)
        st.session_state.retrieval_results = [
            (str(page.path), page.title, page.page_type, page.tags,
             page.content, page.body, score)
            for page, score in results
        ]

    # ── 結果展示 ──────────────────────────────────────────────────────────────
    results_data = st.session_state.retrieval_results
    query_str = st.session_state.retrieval_query

    if results_data:
        st.markdown(f"#### 找到 {len(results_data)} 個相關頁面（關鍵字：`{query_str}`）")
        st.divider()

        for path_str, title, ptype, tags, content, body, score in results_data:
            path = Path(path_str)
            rel = path.relative_to(WIKI_ROOT)
            tag_badges = "  ".join(f"`{t}`" for t in tags[:5])

            # 頁面卡片
            with st.container(border=True):
                header_col, score_col = st.columns([4, 1])
                with header_col:
                    st.markdown(f"**{title}**  —  `{rel}`")
                    if tag_badges:
                        st.caption(f"標籤：{tag_badges}")
                with score_col:
                    st.metric("相關度", f"{score:.1f}")

                # 摘要片段（高亮）
                snippet = highlight_query(body, query_str, max_chars=500)
                st.markdown(snippet)

                # 完整內容
                with st.expander("📄 查看完整頁面內容"):
                    st.markdown(content)

    elif query_str and not results_data:
        st.info("🔍 未找到相關頁面，請嘗試其他關鍵字。")

    else:
        st.markdown("""
> **提示**：輸入關鍵字後按「搜尋」，系統會掃描所有 Wiki 頁面並依相關度排序。
>
> 支援中文、英文關鍵字，也可以輸入概念名稱（如 `MCP`、`Skills`、`主循環`）。
        """)


# ══════════════════════════════════════════════════════════════════════════════
# 模式 B：LLM 查詢（對話介面）
# ══════════════════════════════════════════════════════════════════════════════
else:
    # ── 空狀態 ────────────────────────────────────────────────────────────────
    if not st.session_state.llm_messages:
        with st.container(border=True):
            st.markdown("""
#### 👋 使用說明

1. 在左側選擇 **LLM Provider** 並填入 API Key（Ollama 本地無需 Key）
2. 在下方輸入問題，Agent 自動搜尋 Wiki 並用 LLM 整合回答
3. 每則回答可選擇 **💾 儲存到 Wiki**，歸檔到 `wiki/analyses/`

**範例問題：**
- Claude Skills 和 MCP 的主要差異是什麼？
- Claude Code 的主循環（query.ts）如何運作？
- 三層安全防護網各自的職責是什麼？
            """)

    # ── 渲染對話歷史 ──────────────────────────────────────────────────────────
    for i, msg in enumerate(st.session_state.llm_messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg.get("pages"):
                with st.expander(f"📄 參考了 {len(msg['pages'])} 個 Wiki 頁面"):
                    for pname, score in msg["pages"]:
                        st.write(f"• `{pname}` — 相關度 **{score:.1f}**")

            if show_context and msg.get("context_preview"):
                with st.expander("🔬 Context 預覽（前 2000 字）"):
                    st.code(msg["context_preview"][:2000], language="markdown")

            # 儲存按鈕（只對 assistant）
            if msg["role"] == "assistant" and msg.get("query"):
                save_id = f"save_{i}"
                if save_id not in st.session_state.saved_files:
                    if st.button("💾 儲存此回答到 Wiki", key=f"btn_{i}", type="secondary"):
                        saved_path = save_analysis(
                            query=msg["query"],
                            answer=msg["content"],
                            pages=msg.get("pages", []),
                        )
                        st.session_state.saved_files.add(save_id)
                        st.success(f"✅ 已儲存至 `{saved_path.relative_to(WIKI_ROOT)}`")
                else:
                    st.caption("✅ 已儲存到 Wiki")

    # ── Chat Input ────────────────────────────────────────────────────────────
    if prompt := st.chat_input("輸入你的問題..."):

        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.llm_messages.append({"role": "user", "content": prompt})

        # 搜尋 Wiki
        with st.spinner("🔍 搜尋知識庫..."):
            results = searcher.search(prompt, top_k=top_k)
            index_content = searcher.load_index()
            pages_context = searcher.build_context(results)

        page_refs = [(r.name, s) for r, s in results]

        system_prompt = f"""你是一個 Wiki 知識庫查詢助手。
根據以下提供的知識庫頁面內容，以**繁體中文**回答使用者的問題。

## Wiki 索引
{index_content}

## 相關頁面內容
{pages_context}

## 回答規範
- 引用頁面時使用 [[頁面名稱]] 格式（Obsidian 內部連結）
- 若知識庫中沒有足夠資訊，請明確說明並區分「知識庫記載」與「推測」
- 以繁體中文回答，語氣清晰專業"""

        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.llm_messages
        ]

        with st.spinner(f"⏳ 向 {cfg['name']} 查詢中..."):
            try:
                provider = create_provider(provider_key, api_key=api_key, base_url=base_url)
                answer = provider.chat(system=system_prompt, messages=history, model=model)
            except Exception as exc:
                answer = (
                    f"❌ **呼叫失敗**：{exc}\n\n"
                    "請確認 API Key 是否正確、Provider 端點是否可連線。\n\n"
                    "💡 提示：若沒有 API Key，可切換到左側的「📖 純檢索」模式。"
                )

        with st.chat_message("assistant"):
            st.markdown(answer)
            if page_refs:
                with st.expander(f"📄 參考了 {len(page_refs)} 個 Wiki 頁面"):
                    for pname, score in page_refs:
                        st.write(f"• `{pname}` — 相關度 **{score:.1f}**")
            if show_context:
                with st.expander("🔬 Context 預覽（前 2000 字）"):
                    st.code(pages_context[:2000], language="markdown")

        st.session_state.llm_messages.append({
            "role": "assistant",
            "content": answer,
            "pages": page_refs,
            "query": prompt,
            "context_preview": pages_context,
        })

        st.rerun()
