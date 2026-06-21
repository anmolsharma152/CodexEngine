"""
Agent loop: plain dicts, raw API, no framework.

Messages are plain dicts with role/content/tool_calls.
Tool definitions go in the API call, not the system prompt.
"""

import json
import time
import uuid

from sqlalchemy import text
from src.llm import create_provider, ToolCall
from src.agent.tool_registry import get_registry
from src.db import async_engine
from src.log_utils import logger

MAX_ITERATIONS = 10

SYSTEM_PROMPT = """You are CodexEngine, a knowledge workspace agent.

YOU HAVE TWO KINDS OF CAPABILITIES:

1. Research — search_documents and search_web to find information.
2. Production — write_document to create persistent artifacts, read_document to consume them, list_documents to discover them.

WHEN SOMEONE ASKS YOU TO ANALYZE, SUMMARIZE, PLAN, OR PRODUCE ANY OUTPUT:
- Use write_document to save the result as a persistent artifact.
- Tell the user what you wrote and where.
- You can read your own artifacts later with read_document.
- The path convention is: analysis/<topic>.md, summary/<topic>.md, plans/<topic>.md, etc.

This means your work persists beyond this conversation. You can build on previous work by reading what you wrote earlier.

Use search_documents and search_web as needed for research before writing."""


_WORKSPACE_TOOLS = {"read_document", "write_document", "list_documents"}


async def agent_loop(
    user_message: str,
    thread_id: str,
    user_id: str,
    project_id: str = "default",
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

                if tc.name in _WORKSPACE_TOOLS and "project_id" not in args:
                    args["project_id"] = project_id

                yield json.dumps({"type": "tool_call", "content": {"name": tc.name, "args": args}})

                t0 = time.time()
                error: str | None = None
                try:
                    fn_result = await registry.execute(tc.name, **args)
                    duration = int((time.time() - t0) * 1000)
                    result_str = str(fn_result) if not isinstance(fn_result, str) else fn_result
                    yield json.dumps({"type": "tool_result", "content": {"name": tc.name, "result": result_str[:500]}})
                except Exception as e:
                    duration = int((time.time() - t0) * 1000)
                    result_str = f"Error: {e}"
                    error = str(e)
                    logger.error(f"Tool {tc.name} failed: {e}")
                    yield json.dumps({"type": "tool_result", "content": {"name": tc.name, "error": str(e)}})

                try:
                    sql = text("""
                        INSERT INTO tool_invocations (id, thread_id, user_id, tool_name, arguments, result, error, duration_ms)
                        VALUES (:id, :thread_id, :user_id, :tool_name, :arguments, :result, :error, :duration_ms);
                    """)
                    async with async_engine.connect() as conn:
                        await conn.execute(sql, {
                            "id": str(uuid.uuid4()),
                            "thread_id": thread_id,
                            "user_id": user_id,
                            "tool_name": tc.name,
                            "arguments": json.dumps(args),
                            "result": result_str,
                            "error": error,
                            "duration_ms": duration,
                        })
                        await conn.commit()
                except Exception as log_err:
                    logger.error(f"Failed to log tool invocation: {log_err}")

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
