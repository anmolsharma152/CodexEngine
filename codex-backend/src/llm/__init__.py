"""
LLM provider abstraction.

Usage:
    from src.llm import create_provider

    llm = create_provider("groq")
    result = await llm.complete(messages=[{"role": "user", "content": "Hi"}], tools=tool_defs)
"""

from .providers import LLMProvider, LLMResult, ToolCall, create_provider

__all__ = ["LLMProvider", "LLMResult", "ToolCall", "create_provider"]
