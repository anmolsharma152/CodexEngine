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
    
    1. 'casual': Greetings, small talk, OR explicit statements where the user is telling you personal facts, system setups, or rules to remember for the session. Also includes questions about the user's own name, preferences, or conversation history.
    2. 'explanatory': General world knowledge, abstract concepts, math, or coding help that can be answered purely using pre-trained internal logic without a database.
    3. 'research': Queries asking for specific facts, metrics, citations, figures, or data located within indexed documents, books, papers, or technical manuals.
    
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
