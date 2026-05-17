from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.state import AgentState

# 1. Load environment variables
load_dotenv()

# 2. Initialize Llama 3.3 70B
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


def generate_answer(state: AgentState):
    # Extract messages. LangGraph stores them as tuples or BaseMessage objects.
    # We want everything EXCEPT the latest message to form our history block.
    messages = state.get("messages", [])
    history_text = "No prior history."

    if len(messages) > 1:
        # Format previous messages cleanly for the LLM
        history_lines = []
        for m in messages[:-1]:
            role = m[0] if isinstance(m, tuple) else m.type
            content = m[1] if isinstance(m, tuple) else m.content
            history_lines.append(f"{role.capitalize()}: {content}")
        history_text = "\n".join(history_lines)

    # Dictionary access for V3 TypedDict state
    prompt = f"""
    You are CodexEngine, a precise and conversational RAG-based analyst. 
    
    === CHAT HISTORY ===
    {history_text}
    
    === CURRENT TURN ===
    LATEST USER INTENT: {state["user_query"]}
    RETRIEVED CONTEXT: {state["context"]}
    
    === INSTRUCTIONS ===
    1. CONVERSATIONAL AWARENESS: If the LATEST USER INTENT is conversational, a greeting, or references previous messages (e.g., "What is my name?", "Tell me more about that"), use the CHAT HISTORY to answer naturally.
    2. FACTUAL GROUNDING: If the user is asking a specific knowledge question, you MUST base your answer strictly on the RETRIEVED CONTEXT. 
    3. HALLUCINATION PREVENTION: If it is a factual question and the RETRIEVED CONTEXT is irrelevant or empty, do NOT attempt to answer. Simply state: "I don't have enough specific information in my database to answer that accurately."
    """

    print("\n--- [ACTOR] Generating Final Response ---")
    response = llm.invoke(prompt)

    return {"response": response.content}

