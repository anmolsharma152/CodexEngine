from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

def condense_question_node(state: AgentState):
    """Resolves pronouns using chat history via Groq."""
    history = state["messages"][:-1]
    
    if not history:
        return {"search_query": state["user_query"]}

    prompt = ChatPromptTemplate.from_template("""
        Given the following conversation history and a follow-up question, 
        rephrase the follow-up to be a standalone question.
        
        Chat History: {history}
        Follow-up Question: {user_query}
        Standalone Question:
    """)
    
    # Use Groq llama-3.1-8b for fast resolution
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)
    chain = prompt | llm
    
    result = chain.invoke({"history": history, "user_query": state["user_query"]})
    
    print(f"\n--- [MEMORY] Resolved Query: {result.content} ---")
    
    return {"search_query": result.content}