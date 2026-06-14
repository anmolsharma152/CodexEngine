from src.state import AgentState
from src.log_utils import logger
from src.llm import get_chat_model

llm = get_chat_model(temperature=0.2, max_retries=3)


async def rewrite_query(state: AgentState):
    current_search = state["search_query"]
    context_samples = (
        state["context"][:500] if state["context"] else "No context found yet."
    )

    is_academic = any(
        term in current_search.lower()
        for term in ["framework", "define", "concept", "theory", "axiology"]
    )

    logger.info(f"Mode: {'Academic' if is_academic else 'Narrative'} (Pass {state['revision_count'] + 1})")

    prompt = f"""
    The previous search for "{current_search}" was insufficient.

    CONTEXT SAMPLES: {context_samples}

    TASK: Generate a single, highly-targeted search query to find the missing info.
    Return ONLY the new search string without quotes.
    """

    response = await llm.ainvoke(prompt)
    new_query = response.content.strip().replace('"', "")

    return {
        "search_query": new_query,
        "revision_count": state["revision_count"] + 1,
        "next_step": "retrieve",
    }
