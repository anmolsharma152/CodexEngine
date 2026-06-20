"""
Flexible agent loop: LLM decides tool calls vs. direct response.

Pattern:
  User Message
       |
       v
  +------------------------------+
  |        Agent Loop            |
  |  LLM -> tool_call -> execute |-- loop
  |  LLM -> respond       -> emit|-- done
  +------------------------------+

The LLM is given tool definitions and decides per-turn whether to:
- Call one or more tools (results appended to message history, loop continues)
- Produce a final response (streamed to user, loop exits)
"""

import json
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from src.llm import get_chat_model
from src.agent.tool_registry import get_registry
from src.log_utils import logger

MAX_ITERATIONS = 10
GENERATION_MODEL = "llama-3.3-70b-versatile"

BASE_SYSTEM_PROMPT = """You are CodexEngine, an elite AI knowledge agent.

You have access to tools that help you answer the user's question. Use them as needed:

1. **analyze_intent(query)** — Classify a query as `direct_casual`, `direct_parametric`, or `retrieval_required`.
   - Call this first to decide your strategy.
   - `direct_casual`: greeting/small-talk — answer warmly without tools.
   - `direct_parametric`: general knowledge you know internally — prefix with "[Source: Internal AI Knowledge]".
   - `retrieval_required`: needs document search — use vector_search/web_search.

2. **vector_search(query, thread_id, user_id)** — Search documents via vector similarity + BM25.

3. **web_search(query)** — Search the web for current info.

4. **evaluate_retrieval(query, context, revision_count)** — Check if retrieved context is sufficient.

5. **rewrite_query(query, context)** — Improve a search query that yielded poor results.

CRITICAL FORMATTING RULES FOR YOUR FINAL ANSWER:
1. Short paragraphs (2-3 sentences max). Use bullet lists extensively.
2. Blank lines between paragraphs and list items.
3. No speaker labels — begin your response immediately.
4. If you used retrieved context, attach citations like `[p. 5]`, `[doc]`, `[web]` after sentences. Do not invent citations.
5. If you used ZERO facts from retrieved context, append "[Source: Internal AI Knowledge]" at the end.
6. Only use the `analyze_intent`, `vector_search`, `web_search`, `evaluate_retrieval`, and `rewrite_query` tools — do NOT call any other functions.
7. You may call multiple tools in a single step when they are independent (e.g., `vector_search` + `web_search` simultaneously).
"""


async def agent_loop(
    user_message: str,
    thread_id: str,
    user_id: str,
    messages: list | None = None,
    system_prompt: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Run the agent loop.

    Yields SSE JSON strings with types:
    - 'status': node/tool status updates
    - 'tool_call': tool was invoked
    - 'tool_result': tool returned a result
    - 'token': answer token stream
    - 'evaluation': final evaluation + context metadata
    - 'done': loop complete
    - 'error': unrecoverable error
    """
    registry = get_registry()
    llm = get_chat_model(model=GENERATION_MODEL, temperature=0.3, max_retries=3)

    # Build message list
    lc_messages = []
    lc_messages.append(SystemMessage(content=system_prompt or BASE_SYSTEM_PROMPT))

    if messages:
        for msg in messages:
            role = msg.get("role", "user") if isinstance(msg, dict) else getattr(msg, "role", "user")
            content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))

    lc_messages.append(HumanMessage(content=user_message))

    tool_defs = registry.get_definitions()
    llm_with_tools = llm.bind_tools(tool_defs, tool_choice="auto")

    intent = "retrieval_required"
    context = ""
    evaluation = {}

    yield json.dumps({"type": "status", "content": "Analyzing your request..."})

    for iteration in range(MAX_ITERATIONS):
        logger.info(f"Agent iteration {iteration + 1}/{MAX_ITERATIONS}")

        response = await llm_with_tools.ainvoke(lc_messages)

        if not response.tool_calls:
            answer = response.content
            if answer:
                yield json.dumps({"type": "token", "content": answer})

            yield json.dumps({"type": "evaluation", "content": {
                "intent": intent,
                "context_preview": context[:500] if context else "",
                "evaluation": evaluation,
            }})
            yield json.dumps({"type": "done"})
            return

        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("args", {})
            tool_call_id = tc.get("id", f"call_{iteration}_{tool_name}")

            logger.info(f"Tool call: {tool_name}({tool_args})")
            yield json.dumps({"type": "tool_call", "content": {"name": tool_name, "args": tool_args}})

            try:
                result = await registry.execute(tool_name, **tool_args)
                result_str = str(result) if not isinstance(result, str) else result

                if tool_name == "analyze_intent":
                    intent = result_str
                elif tool_name in ("vector_search", "web_search"):
                    context = result_str
                elif tool_name == "evaluate_retrieval":
                    try:
                        evaluation = json.loads(result_str) if isinstance(result_str, str) else result_str
                    except (json.JSONDecodeError, TypeError):
                        evaluation = {}

                yield json.dumps({"type": "tool_result", "content": {"name": tool_name, "result": result_str[:500]}})
            except Exception as e:
                result_str = f"Error: {e}"
                logger.error(f"Tool {tool_name} failed: {e}")
                yield json.dumps({"type": "tool_result", "content": {"name": tool_name, "error": str(e)}})

            lc_messages.append(AIMessage(content="", tool_calls=[{
                "name": tool_name, "args": tool_args, "id": tool_call_id,
            }]))
            lc_messages.append(ToolMessage(content=result_str, tool_call_id=tool_call_id))

    # Max iterations exceeded — force final response
    yield json.dumps({"type": "status", "content": "Reached maximum iterations, generating final answer..."})
    llm_no_tools = get_chat_model(model=GENERATION_MODEL, temperature=0.3, max_retries=3)
    force_response = await llm_no_tools.ainvoke(
        lc_messages + [SystemMessage(content="You have reached the maximum number of tool calls. Provide your best final answer now using everything you have learned.")]
    )
    if force_response.content:
        yield json.dumps({"type": "token", "content": force_response.content})

    yield json.dumps({"type": "evaluation", "content": {
        "intent": intent,
        "context_preview": context[:500] if context else "",
        "evaluation": evaluation,
    }})
    yield json.dumps({"type": "done"})
