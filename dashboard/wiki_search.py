"""
Wiki 知識庫搜尋引擎。
不依賴外部向量 DB，使用關鍵字加權評分（適合中小型 wiki）。
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# 每個頁面傳給 LLM 的最大字元數（避免超出 context window）
MAX_PAGE_CHARS = 4000


class WikiPage:
    def __init__(self, path: Path, content: str, frontmatter: dict, body: str):
        self.path = path
        self.content = content
        self.frontmatter = frontmatter
        self.body = body

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def title(self) -> str:
        return str(self.frontmatter.get("title", self.path.stem))

    @property
    def tags(self) -> list[str]:
        return [str(t) for t in self.frontmatter.get("tags", [])]

    @property
    def page_type(self) -> str:
        return str(self.frontmatter.get("type", ""))

    def truncated_content(self, max_chars: int = MAX_PAGE_CHARS) -> str:
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars] + "\n\n…（內容過長，已截斷）"


class WikiSearcher:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root
        self.wiki_dir = wiki_root / "wiki"

    # ── 基本讀取 ──────────────────────────────────────────────────────────────
    def load_index(self) -> str:
        p = self.wiki_root / "index.md"
        return p.read_text(encoding="utf-8") if p.exists() else "（index.md 不存在）"

    def load_log(self, last_n: int = 10) -> str:
        p = self.wiki_root / "log.md"
        if not p.exists():
            return "（log.md 不存在）"
        lines = p.read_text(encoding="utf-8").splitlines()
        entries = [l for l in lines if l.startswith("## [")]
        return "\n".join(entries[-last_n:])

    def get_all_page_paths(self) -> list[Path]:
        if not self.wiki_dir.exists():
            return []
        return sorted(self.wiki_dir.rglob("*.md"))

    def get_stats(self) -> dict:
        paths = self.get_all_page_paths()
        by_type: dict[str, int] = {}
        for p in paths:
            folder = p.parent.name
            by_type[folder] = by_type.get(folder, 0) + 1
        return {
            "total_pages": len(paths),
            "sources": by_type.get("sources", 0),
            "entities": by_type.get("entities", 0),
            "concepts": by_type.get("concepts", 0),
            "analyses": by_type.get("analyses", 0),
        }

    # ── Frontmatter 解析 ──────────────────────────────────────────────────────
    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[dict, str]:
        if not content.startswith("---"):
            return {}, content
        end = content.find("---", 3)
        if end == -1:
            return {}, content
        fm_text = content[3:end]
        body = content[end + 3:].strip()
        if _HAS_YAML:
            try:
                return yaml.safe_load(fm_text) or {}, body
            except Exception:
                pass
        return {}, body

    def _load_page(self, path: Path) -> Optional[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8")
            fm, body = self._parse_frontmatter(content)
            return WikiPage(path=path, content=content, frontmatter=fm, body=body)
        except Exception:
            return None

    # ── 評分算法 ──────────────────────────────────────────────────────────────
    @staticmethod
    def _score(page: WikiPage, query: str) -> float:
        q = query.lower()
        # 合併標題、標籤、內文
        haystack = f"{page.title} {' '.join(page.tags)} {page.body}".lower()

        score = 0.0

        # 完整 query 子字串命中（高權重）
        if q in haystack:
            score += 25.0

        # 英文詞匹配
        words = re.findall(r"[a-z0-9\-_]{2,}", q)
        for w in words:
            score += haystack.count(w) * 1.5

        # 中文字元匹配
        zh_chars = [c for c in q if "一" <= c <= "鿿"]
        for c in zh_chars:
            score += haystack.count(c) * 0.8

        # 標題命中加成
        if q in page.title.lower():
            score += 15.0

        # 標籤命中加成
        for tag in page.tags:
            if q in tag.lower() or tag.lower() in q:
                score += 5.0

        return score

    # ── 搜尋入口 ──────────────────────────────────────────────────────────────
    def search(self, query: str, top_k: int = 5) -> list[tuple[WikiPage, float]]:
        """回傳 [(WikiPage, score), ...] 依相關度排序。"""
        results = []
        for path in self.get_all_page_paths():
            page = self._load_page(path)
            if page is None:
                continue
            score = self._score(page, query)
            if score > 0:
                results.append((page, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def build_context(
        self,
        results: list[tuple[WikiPage, float]],
        max_chars_per_page: int = MAX_PAGE_CHARS,
    ) -> str:
        """把搜尋結果拼成 LLM 用的 context 字串。"""
        if not results:
            return "（未找到相關頁面）"
        parts = []
        for page, score in results:
            rel = page.path.relative_to(self.wiki_root)
            header = f"### [{page.title}] — `{rel}`  （相關度 {score:.1f}）"
            parts.append(f"{header}\n\n{page.truncated_content(max_chars_per_page)}")
        return "\n\n---\n\n".join(parts)
