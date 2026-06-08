from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.state import AgentState

load_dotenv()

# Blazing-fast 8B model with 0.0 temperature for deterministic routing
router_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.0, max_retries=3)


async def analyze_intent(state: AgentState):
    print("\n--- [ROUTER] Analyzing User Intent ---")

    raw_query = state["user_query"]
    # Truncate to prevent token burn on large pasted payloads (e.g. logs)
    query_sample = raw_query[:1500] + "\n[Truncated for Routing...]" if len(raw_query) > 1500 else raw_query

    prompt = f"""
    You are a highly efficient routing system for an AI assistant. Classify the user query into exactly ONE of the following routing decisions:

    1. 'direct_casual': Greetings, small talk, pleasantries, questions about assistant capabilities (e.g. "Can you help me?"), or questions purely about the user's/assistant's identity. These can be answered directly without search.
    2. 'direct_parametric': General coding/programming syntax queries, general mathematical/logical proofs, or broad world knowledge queries that the AI can answer confidently and completely using its internal pre-trained knowledge without needing local documents.
    3. 'retrieval_required': Specific factual queries about literature, custom documents, DBeaver truststore settings, quantum physics, AI papers, or any specific topic that requires retrieval of indexed context to be grounded and accurate.

    EXAMPLES:
    - User Query: "hi there" -> output: direct_casual
    - User Query: "Can you help me search through my documents?" -> output: direct_casual
    - User Query: "what is your name?" -> output: direct_casual
    - User Query: "how to write a binary search in python" -> output: direct_parametric
    - User Query: "Explain distance vs logical error rate in surface codes" -> output: retrieval_required
    - User Query: "What was Kelsier's plan?" -> output: retrieval_required

    User Query: "{query_sample}"

    Output ONLY the routing decision name in lowercase (direct_casual, direct_parametric, or retrieval_required). Do not add any punctuation, intro, or explanation.
    """

    response = await router_llm.ainvoke(prompt)
    intent = response.content.strip().lower()

    # The ultimate safety net: If it hallucinates or gets confused, force it to check the database.
    if intent not in ["direct_casual", "direct_parametric", "retrieval_required"]:
        intent = "retrieval_required"

    print(f"--- [ROUTER] Intent Classified: {intent.upper()} ---")
    return {"intent": intent}
