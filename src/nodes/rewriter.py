import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.state import AgentState

# Load environment variables
load_dotenv()

# Standardize on the 8b-instant for the rewriter
llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.2)

def rewrite_query(state: AgentState):
    # 1. Dictionary access for V3 State
    current_search = state["search_query"]
    context_samples = state["context"][:500] if state["context"] else "No context found yet."
    
    # 2. Categorical Intent Detection (Fixed to use dictionary access)
    is_academic = any(term in current_search.lower() for term in ["framework", "define", "concept", "theory", "axiology"])
    
    print(f"\n--- [REWRITING] Mode: {'Academic' if is_academic else 'Narrative'} (Pass {state['revision_count'] + 1}) ---")
    
    # 3. Targeted Prompt
    prompt = f"""
    The previous search for "{current_search}" was insufficient.
    
    CONTEXT SAMPLES: {context_samples}
    
    TASK: Generate a single, highly-targeted search query to find the missing info.
    Return ONLY the new search string without quotes.
    """
    
    response = llm.invoke(prompt)
    new_query = response.content.strip().replace('"', '')
    
    return {
        "search_query": new_query, 
        "revision_count": state["revision_count"] + 1,
        "next_step": "retrieve"
    }