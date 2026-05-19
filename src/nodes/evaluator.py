import os
from langchain_groq import ChatGroq
from src.state import AgentState
from dotenv import load_dotenv

# 1. Ensure the API key is actually in memory for this process
load_dotenv()

# 2. Use the standard 8b-instant
llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)


def evaluate_retrieval(state: AgentState):
    # Dictionary access is CORRECT here for V3
    query = state["search_query"]
    context = state["context"]

    prompt = f"""
    Grade this context based on its ability to answer the query.
    QUERY: {query}
    CONTEXT: {context}

    TASK: Return ONLY a numerical score between 0.0 and 1.0.
    1.0 = Perfect match.
    0.0 = Totally irrelevant.
    Do NOT include any text or explanation, just the number.
    """

    response = llm.invoke(prompt)

    try:
        # Clean up possible whitespace or quotes from the LLM
        score_str = response.content.strip().replace('"', "").replace("'", "")
        score = float(score_str)
    except Exception as e:
        print(f"--- [EVALUATOR ERROR] Fallback to 0.5: {e} ---")
        score = 0.5

    # Logic Check: Dictionary access for revision_count is CORRECT
    next_step = "actor" if score > 0.7 or state["revision_count"] >= 3 else "rewrite"

    print(f"--- [EVALUATING] Score: {score} | Next: {next_step} ---")

    return {"critic_score": score, "next_step": next_step}
