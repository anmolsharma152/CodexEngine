import os
from langchain_groq import ChatGroq
from src.state import AgentState
from dotenv import load_dotenv

load_dotenv()

# Using 70b for the final synthesis to ensure the "Why" is handled with nuance
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)

def generate_answer(state: AgentState) -> dict:
    # Logic Lean: Match the tone to the query
    is_academic = any(term in state.query.lower() for term in ["framework", "define", "concept", "theory", "ssl", "error rate"])
    
    role = "Technical Analyst" if is_academic else "Narrative Analyst"
    focus = "technical accuracy and definitions" if is_academic else "character motivation and plot triggers"

    prompt = f"""
    You are a {role} for the CodexEngine.
    
    QUERY: {state.query}
    CONTEXT: {" ".join(state.context)}
    
    INSTRUCTIONS:
    - Focus on {focus}.
    - Do NOT apologize for a lack of characters if the query is technical.
    - Provide a direct answer based ONLY on the provided context.
    """
        
    response = llm.invoke(prompt)
    
    return {
        "answer": response.content,
        "next_step": "__end__"
    }