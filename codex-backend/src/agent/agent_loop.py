"""
Agent loop: plain dicts, raw API, no framework.

Messages are plain dicts with role/content/tool_calls.
Tool definitions go in the API call, not the system prompt.
"""

import json

from src.llm import create_provider, ToolCall
from src.agent.tool_registry import get_registry
from src.log_utils import logger

MAX_ITERATIONS = 10

SYSTEM_PROMPT = "You are CodexEngine, a research assistant. Answer using the user's documents and web search when helpful."


async def agent_loop(
    user_message: str,
    thread_id: str,
    user_id: str,
    messages: list | None = None,
    system_prompt: str | None = None,
    provider: str = "groq",
    model: str | None = None,
):
    """Yield SSE JSON lines."""
    registry = get_registry()
    tool_defs = registry.get_definitions()
    llm = create_provider(provider=provider, model=model)

    lc = [{"role": "system", "content": system_prompt or SYSTEM_PROMPT}]

    if messages:
        for m in messages:
            if isinstance(m, dict) and "role" in m:
                lc.append(m)

    lc.append({"role": "user", "content": user_message})
    yield json.dumps({"type": "status", "content": "Thinking..."})

    for iteration in range(MAX_ITERATIONS):
        logger.info(f"Iteration {iteration + 1}/{MAX_ITERATIONS}")
        result = await llm.complete(lc, tools=tool_defs)

        if result.tool_calls:
            for tc in result.tool_calls:
                try:
                    args = json.loads(tc.arguments)
                except json.JSONDecodeError:
                    args = {}

                yield json.dumps({"type": "tool_call", "content": {"name": tc.name, "args": args}})

                try:
                    fn_result = await registry.execute(tc.name, **args)
                    result_str = str(fn_result) if not isinstance(fn_result, str) else fn_result
                    yield json.dumps({"type": "tool_result", "content": {"name": tc.name, "result": result_str[:500]}})
                except Exception as e:
                    result_str = f"Error: {e}"
                    logger.error(f"Tool {tc.name} failed: {e}")
                    yield json.dumps({"type": "tool_result", "content": {"name": tc.name, "error": str(e)}})

                lc.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": tc.arguments}}],
                })
                lc.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})
            continue

        if result.content:
            yield json.dumps({"type": "token", "content": result.content})
        yield json.dumps({"type": "done"})
        return

    yield json.dumps({"type": "status", "content": "Max iterations reached."})
    fallback = await llm.complete(lc + [{"role": "system", "content": "Provide your best final answer now."}])
    if fallback.content:
        yield json.dumps({"type": "token", "content": fallback.content})
    yield json.dumps({"type": "done"})
