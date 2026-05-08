import os
from langchain_groq import ChatGroq
from src.state import AgentState
from dotenv import load_dotenv

load_dotenv()

# Get model from env, fallback to 8b
model = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
llm = ChatGroq(model_name=model, temperature=0.3)

def generate_answer(state: AgentState) -> dict:
    # Logic Lean: Match the tone to the query
    is_academic = any(term in state.query.lower() for term in ["framework", "define", "concept", "theory", "ssl", "error rate"])
    
    role = "Technical Analyst" if is_academic else "Narrative Analyst"
    focus = "technical accuracy and definitions" if is_academic else "character motivation and plot triggers"

    prompt = f"""
    You are a {role} for the CodexEngine.
    
    QUERY: {state.query}
    CONTEXT: {"\n\n".join(state.context)}
    
    INSTRUCTIONS:
    - Focus on {focus}.
    - Every claim must be followed by its source name in brackets, e.g., [Source: filename.pdf].
    - Provide a direct answer based ONLY on the provided context.
    """
        
    response = llm.invoke(prompt)
    return {"answer": response.content, "next_step": "__end__"}