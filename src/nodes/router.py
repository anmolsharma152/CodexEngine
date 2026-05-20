import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.state import AgentState

load_dotenv()

# Blazing-fast 8B model with 0.0 temperature for deterministic routing
router_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.0)


def analyze_intent(state: AgentState):
    print("\n--- [ROUTER] Analyzing User Intent ---")

    prompt = f"""
    You are a highly efficient routing system for an AI assistant. Classify the following user query into exactly ONE of these three categories:
    
    1. 'casual': Greetings, playful talk, small talk, or questions about the user's name/preferences/history.
    2. 'explanatory': General world knowledge, abstract concepts, coding help, or brainstorming that does NOT require searching a specific local database.
    3. 'research': Deep fact-based questions, data analysis, or queries that require retrieving specific documents, citations, or technical PDFs.
    
    User Query: "{state["user_query"]}"
    
    Output ONLY the category name in lowercase (casual, explanatory, or research). Do not add any punctuation, intro, or explanation.
    """

    response = router_llm.invoke(prompt)
    intent = response.content.strip().lower()

    # Fallback safety net
    if intent not in ["casual", "explanatory", "research"]:
        intent = "research"

    print(f"--- [ROUTER] Intent Classified: {intent.upper()} ---")
    return {"intent": intent}
