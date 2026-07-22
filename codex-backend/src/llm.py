import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "qwen/qwen3.6-27b")

# Groq free tier: 30 RPM → 1 request per 2 seconds
_rate_limiter = asyncio.Semaphore(1)
_last_request_time = 0.0


async def _rate_limited():
    global _last_request_time
    async with _rate_limiter:
        now = asyncio.get_event_loop().time()
        since_last = now - _last_request_time
        if since_last < 2.0:
            await asyncio.sleep(2.0 - since_last)
        _last_request_time = asyncio.get_event_loop().time()


class RateLimitedGroq(ChatGroq):
    async def ainvoke(self, *args, **kwargs):
        await _rate_limited()
        return await super().ainvoke(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        raise RuntimeError("Only async invoke is supported")


def get_chat_model(model: str | None = None, temperature: float = 0, max_retries: int = 3) -> RateLimitedGroq:
    return RateLimitedGroq(
        model=model or GROQ_MODEL_NAME,
        temperature=temperature,
        max_retries=max_retries,
    )
