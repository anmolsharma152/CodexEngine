from langchain_groq import ChatGroq
from src.state import AgentState

llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.2)

def rewrite_query(state: AgentState) -> dict:
    # 1. Categorical Intent Detection
    is_academic = any(term in state.query.lower() for term in ["framework", "define", "concept", "theory", "axiology"])
    
    # 2. Dynamic Strategy Injection
    if is_academic:
        strategy = "ACADEMIC: Focus on definitions, formal terminology, and specific conceptual frameworks. Use keywords like 'ontology' or 'paradigm'."
    else:
        strategy = "NARRATIVE: Focus on triggering events, character motivations, and sensory descriptions. Use action words like 'decided', 'departed', or 'witnessed'."

    print(f"\n--- [REWRITING] Mode: {'Academic' if is_academic else 'Narrative'} (Pass {state.revision_count + 1}) ---")
    
    # 3. Unified Universal Prompt
    prompt = f"""
    The previous search for "{state.query}" was insufficient.
    
    FAILED CONTEXT SAMPLES: {str(state.context)[:500]}...
    
    CURRENT STRATEGY: {strategy}
    
    TASK: Generate a single, highly-targeted search query that will find the 
    missing information in a 1500-character prose chunk. 
    - If Academic: Target the core definition.
    - If Narrative: Target the specific action or decision.
    
    Return ONLY the new search string.
    """
    
    response = llm.invoke(prompt)
    new_query = response.content.strip().replace('"', '') # Clean up quotes
    
    return {
        "query": new_query,
        "revision_count": state.revision_count + 1,
        "next_step": "retrieve"
    }