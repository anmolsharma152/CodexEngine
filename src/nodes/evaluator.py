from langchain_groq import ChatGroq
from src.state import AgentState

llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)

def evaluate_retrieval(state: AgentState):
    prompt = f"""
    Grade this context based on its ability to answer the query.
    QUERY: {state['search_query']}
    CONTEXT: {state['context']}
    Return ONLY a score between 0.0 and 1.0.
    """
    response = llm.invoke(prompt)
    try:
        score = float(response.content.strip())
    except:
        score = 0.5

    next_step = "actor" if score > 0.7 or state["revision_count"] >= 3 else "rewrite"
    return {"critic_score": score, "next_step": next_step}