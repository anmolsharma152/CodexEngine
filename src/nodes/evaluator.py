import os
from langchain_groq import ChatGroq
from src.state import AgentState
from dotenv import load_dotenv

load_dotenv()

# Initialize the 'Judge' model
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)

def evaluate_retrieval(state: AgentState) -> dict:
    """
    Evaluates if the retrieved prose chunks contain the 'Why'.
    """
    print(f"\n--- [EVALUATING] Scoring {len(state.context)} chunks ---")
    
    context_str = "\n\n".join(state.context)
    
    prompt = f"""
    You are a Narrative Critic. Grade the following context based on its ability 
    to answer the user's specific query.
    
    QUERY: {state.query}
    CONTEXT: {context_str}
    
    Provide a deterministic score between 0.0 and 1.0.
    1.0 = Explicitly answers the 'Why' and 'Event Trigger'.
    0.5 = Mentions the characters/setting but lacks motivation.
    0.0 = Totally irrelevant noise.
    
    Return ONLY the numerical score.
    """
    
    response = llm.invoke(prompt)

    try:
        score = float(response.content.strip())
    except:
        score = 0.5 

    # Determine the natural next step based on quality
    next_step = "actor" if score > 0.7 else "rewrite"
    
    # OVERRIDE: If we've looped 3 times, stop the madness
    if state.revision_count >= 3:
        return {
            "critic_score": score, 
            "next_step": "actor"
        }
    
    return {
        "critic_score": score, 
        "next_step": next_step
    }