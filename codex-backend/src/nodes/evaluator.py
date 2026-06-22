import json

from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState
from src.log_utils import logger
from src.llm import get_chat_model

llm = get_chat_model(temperature=0, max_retries=3)


def parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        nl = content.find("\n")
        if nl != -1:
            content = content[nl:]
        if content.endswith("```"):
            content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except Exception as e:
        logger.error(f"JSON parse error: {e}. Raw: {content}")
        return {
            "relevant": False,
            "sufficient": False,
            "grounded": False,
            "confidence": 0.0,
            "retry_needed": True,
        }


async def evaluate_retrieval(state: AgentState):
    query = state["search_query"]
    context = state["context"]

    if not context.strip():
        logger.info("Context is empty (Failed retrieval thresholding)")
        evaluation = {
            "relevant": False,
            "sufficient": False,
            "grounded": False,
            "confidence": 0.0,
            "retry_needed": True,
        }
        next_step = "actor" if state["revision_count"] >= 3 else "rewrite"
        return {"critic_score": 0.0, "evaluation": evaluation, "next_step": next_step}

    query_sample = query[:1500] + "\n[Truncated for Evaluation...]" if len(query) > 1500 else query

    prompt = f"""
    Evaluate the retrieved context's ability to answer the search query.
    QUERY: {query_sample}
    CONTEXT: {context}

    Respond strictly in raw JSON format with the following fields:
    - "relevant": boolean (true if the context contains information directly related to the query)
    - "sufficient": boolean (true if the context contains enough details to fully answer the query without external knowledge)
    - "grounded": boolean (true if the context is factual and not contradictory to general knowledge)
    - "confidence": float between 0.0 and 1.0 (rating the overall quality of the source context)
    - "retry_needed": boolean (true if the context is irrelevant or insufficient AND we should rewrite and try retrieving again)

    Output ONLY the raw JSON block. Do not include any markdown styling, explanation, or other text.
    """

    response = await llm.ainvoke(prompt)
    evaluation = parse_json_response(response.content)

    score = evaluation.get("confidence", 0.5)

    if evaluation.get("retry_needed") and state["revision_count"] < 3:
        next_step = "rewrite"
    elif not evaluation.get("sufficient"):
        next_step = "web_search"
    else:
        next_step = "actor"

    logger.info(f"Evaluation: {evaluation} | Next: {next_step}")
    return {"critic_score": score, "evaluation": evaluation, "next_step": next_step}
