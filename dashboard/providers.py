"""
LLM Provider 抽象層。
- Anthropic：使用 anthropic SDK
- OpenAI / NVIDIA / Ollama / Gemini：全部走 OpenAI 相容端點（openai SDK）
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

# ── Provider 設定表 ──────────────────────────────────────────────────────────
PROVIDERS_CONFIG: dict[str, dict] = {
    "anthropic": {
        "name": "Anthropic",
        "icon": "🟠",
        "models": [
            "claude-opus-4-7",
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
        ],
        "default_model": "claude-sonnet-4-6",
        "needs_api_key": True,
        "needs_base_url": False,
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": None,
    },
    "openai": {
        "name": "OpenAI",
        "icon": "🟢",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini"],
        "default_model": "gpt-4o",
        "needs_api_key": True,
        "needs_base_url": False,
        "env_key": "OPENAI_API_KEY",
        "base_url": None,
    },
    "gemini": {
        "name": "Google Gemini",
        "icon": "🔵",
        "models": [
            "gemini-2.0-flash",
            "gemini-2.5-pro-preview-05-06",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
        "default_model": "gemini-2.0-flash",
        "needs_api_key": True,
        "needs_base_url": False,
        "env_key": "GEMINI_API_KEY",
        # Gemini 的 OpenAI 相容端點
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "ollama": {
        "name": "Ollama（本地）",
        "icon": "🦙",
        "models": [],  # 使用者自填
        "default_model": "gemini-3-flash-preview:latest",
        "needs_api_key": False,
        "needs_base_url": True,
        "env_key": "",
        "default_base_url": "http://localhost:11434/v1",
        "base_url": "http://localhost:11434/v1",
    },
    "nvidia": {
        "name": "NVIDIA NIM",
        "icon": "🟩",
        "models": [
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "meta/llama-3.3-70b-instruct",
            "meta/llama-3.1-405b-instruct",
            "mistralai/mixtral-8x22b-instruct-v0.1",
            "microsoft/phi-3-medium-128k-instruct",
        ],
        "default_model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "needs_api_key": True,
        "needs_base_url": False,
        "env_key": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
    },
}


# ── 抽象基類 ──────────────────────────────────────────────────────────────────
class BaseLLMProvider(ABC):
    @abstractmethod
    def chat(self, system: str, messages: list[dict], model: str) -> str:
        """
        發送對話請求並回傳回覆文字。
        messages 格式：[{"role": "user"|"assistant", "content": "..."}]
        """


# ── Anthropic ─────────────────────────────────────────────────────────────────
class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("請先安裝：pip install anthropic")

    def chat(self, system: str, messages: list[dict], model: str) -> str:
        filtered = [m for m in messages if m["role"] in ("user", "assistant")]
        resp = self.client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=filtered,
        )
        return resp.content[0].text


# ── OpenAI 相容（OpenAI / Gemini / Ollama / NVIDIA）────────────────────────
class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key or "ollama",
                base_url=base_url if base_url else None,
            )
        except ImportError:
            raise ImportError("請先安裝：pip install openai")

    def chat(self, system: str, messages: list[dict], model: str) -> str:
        all_messages = [{"role": "system", "content": system}] + [
            m for m in messages if m["role"] in ("user", "assistant")
        ]
        resp = self.client.chat.completions.create(
            model=model,
            messages=all_messages,
            max_tokens=4096,
        )
        return resp.choices[0].message.content


# ── 工廠函式 ─────────────────────────────────────────────────────────────────
def create_provider(
    provider_key: str,
    api_key: str = "",
    base_url: str = "",
) -> BaseLLMProvider:
    cfg = PROVIDERS_CONFIG[provider_key]

    if provider_key == "anthropic":
        if not api_key:
            raise ValueError("Anthropic 需要 API Key")
        return AnthropicProvider(api_key=api_key)

    if provider_key == "ollama":
        url = base_url or cfg.get("default_base_url", "http://localhost:11434/v1")
        return OpenAICompatibleProvider(api_key="ollama", base_url=url)

    if provider_key == "gemini":
        if not api_key:
            raise ValueError("Gemini 需要 API Key")
        return OpenAICompatibleProvider(api_key=api_key, base_url=cfg["base_url"])

    if provider_key == "nvidia":
        if not api_key:
            raise ValueError("NVIDIA NIM 需要 API Key")
        return OpenAICompatibleProvider(api_key=api_key, base_url=cfg["base_url"])

    if provider_key == "openai":
        if not api_key:
            raise ValueError("OpenAI 需要 API Key")
        return OpenAICompatibleProvider(api_key=api_key)

    raise ValueError(f"未知的 Provider：{provider_key}")
