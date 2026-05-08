from langchain_groq import ChatGroq
from src.state import AgentState

llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.3)

def generate_answer(state: AgentState):
    prompt = f"""
    You are CodexEngine. 
    ORIGINAL INTENT: {state['user_query']}
    CONTEXT: {state['context']}
    
    INSTRUCTION:
    Use the context to answer the ORIGINAL INTENT. 
    If the context is about something else (like Nigeria oil), DO NOT use it.
    Simply say you don't have that information.
    """
    response = llm.invoke(prompt)
    return {"response": response.content}