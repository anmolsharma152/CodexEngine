"""
Provider-agnostic LLM layer.

Each adapter converts our canonical tool format to the provider's native format
and translates responses back.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI


# ── Canonical types ──────────────────────────────────────────────────

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON string


@dataclass
class LLMResult:
    content: str | None = None
    tool_calls: list[ToolCall] | None = None


def tool_choice_from_str(s: str) -> Any:
    """Parse tool_choice from 'auto', 'required', 'none', or a tool name."""
    if s == "auto":
        return "auto"
    if s == "required" or s == "any":
        return "required"
    if s == "none" or s is None:
        return "none"
    return {"type": "function", "function": {"name": s}}


# ── Abstract base ────────────────────────────────────────────────────

class LLMProvider(ABC):
    model: str

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        temperature: float = 0.3,
    ) -> LLMResult: ...

    @abstractmethod
    async def complete_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        temperature: float = 0.3,
    ): ...


# ── OpenAI-compatible (OpenAI, Groq, Together, etc.) ────────────────

class OpenAICompatible(LLMProvider):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        max_retries: int = 2,
    ):
        self.model = model
        self._client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            max_retries=max_retries,
        )

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        temperature: float = 0.3,
    ) -> LLMResult:
        kwargs = dict(model=self.model, messages=messages, temperature=temperature)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice_from_str(tool_choice)

        resp = await self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        msg = choice.message

        result = LLMResult(content=msg.content or None)
        if msg.tool_calls:
            result.tool_calls = [
                ToolCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments)
                for tc in msg.tool_calls
            ]
        return result

    async def complete_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        temperature: float = 0.3,
    ):
        kwargs = dict(model=self.model, messages=messages, temperature=temperature, stream=True)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice_from_str(tool_choice)

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue
            yield {
                "content": delta.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                    for tc in (delta.tool_calls or [])
                ],
                "finish_reason": chunk.choices[0].finish_reason,
            }


# ── Factory ──────────────────────────────────────────────────────────

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAICompatible,
    "groq": OpenAICompatible,
    "together": OpenAICompatible,
}

def create_provider(
    provider: str = "groq",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """Factory: returns a configured provider."""
    provider = provider.lower()

    if provider in ("groq",):
        cls = _PROVIDERS["groq"]
        return cls(
            model=model or os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant"),
            api_key=api_key or os.getenv("GROQ_API_KEY"),
            base_url=base_url or "https://api.groq.com/openai/v1",
        )

    if provider in ("openai",):
        cls = _PROVIDERS["openai"]
        return cls(
            model=model or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )

    if provider in ("together", "together-ai"):
        cls = _PROVIDERS["together"]
        return cls(
            model=model or os.getenv("TOGETHER_MODEL_NAME", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
            api_key=api_key or os.getenv("TOGETHER_API_KEY"),
            base_url=base_url or "https://api.together.xyz/v1",
        )

    raise ValueError(f"Unknown provider: {provider}. Supported: {list(_PROVIDERS.keys())}")
