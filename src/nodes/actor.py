import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.state import AgentState

# 1. Load environment variables for the GROQ_API_KEY
load_dotenv()

# 2. Upgrade to Llama 3.3 70B for the final response synthesis
# It is much better at following the "Admit you don't know" instruction.
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)

def generate_answer(state: AgentState):
    # Dictionary access is exactly what we need for the V3 TypedDict state
    prompt = f"""
    You are CodexEngine, a precise RAG-based analyst. 
    
    ORIGINAL INTENT: {state['user_query']}
    CONTEXT RETRIEVED: {state['context']}
    
    INSTRUCTION:
    1. Use the CONTEXT to answer the ORIGINAL INTENT. 
    2. If the context is irrelevant to the intent (e.g., it discusses Nigeria oil or unrelated topics), 
       do NOT attempt to answer. 
    3. Simply state: "I don't have enough specific information in my database to answer that accurately."
    """
    
    print("\n--- [ACTOR] Generating Final Response ---")
    response = llm.invoke(prompt)
    
    return {"response": response.content}