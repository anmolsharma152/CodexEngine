from src.state import AgentState
from src.log_utils import logger
from src.llm import get_chat_model

router_llm = get_chat_model(temperature=0.0, max_retries=3)


async def analyze_intent(state: AgentState):
    logger.info("Analyzing User Intent")

    raw_query = state["user_query"]
    query_sample = raw_query[:1500] + "\n[Truncated for Routing...]" if len(raw_query) > 1500 else raw_query

    prompt = f"""
    You are a highly efficient routing system for an AI assistant. Classify the user query into exactly ONE of the following routing decisions:

    1. 'direct_casual': Greetings, small talk, pleasantries, questions about assistant capabilities (e.g. "Can you help me?"), or questions purely about the user's/assistant's identity. These can be answered directly without search.
    2. 'direct_parametric': General coding/programming syntax queries, general mathematical/logical proofs, or broad world knowledge queries that the AI can answer confidently and completely using its internal pre-trained knowledge without needing local documents.
    3. 'meta_conversational': Questions asking about the AI's own previous responses in this chat, asking why it answered a certain way, or referring back to its own performance.
    4. 'retrieval_required': Specific factual queries about literature, custom documents, DBeaver truststore settings, quantum physics, AI papers, or any specific topic that requires retrieval of indexed context to be grounded and accurate.

    EXAMPLES:
    - User Query: "hi there" -> output: direct_casual
    - User Query: "Can you help me search through my documents?" -> output: direct_casual
    - User Query: "what is your name?" -> output: direct_casual
    - User Query: "how to write a binary search in python" -> output: direct_parametric
    - User Query: "Explain distance vs logical error rate in surface codes" -> output: retrieval_required
    - User Query: "What was Kelsier's plan?" -> output: retrieval_required
    - User Query: "why did you say that?" -> output: meta_conversational
    - User Query: "why did you not answer well earlier?" -> output: meta_conversational

    User Query: "{query_sample}"

    Output ONLY the routing decision name in lowercase (direct_casual, direct_parametric, meta_conversational, or retrieval_required). Do not add any punctuation, intro, or explanation.
    """

    response = await router_llm.ainvoke(prompt)
    intent = response.content.strip().lower()

    if intent not in ["direct_casual", "direct_parametric", "meta_conversational", "retrieval_required"]:
        intent = "retrieval_required"

    logger.info(f"Intent Classified: {intent.upper()}")
    return {"intent": intent}
