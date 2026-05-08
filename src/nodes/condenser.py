from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

def condense_question_node(state: AgentState):
    # Get history excluding the current message
    history = state["messages"][:-1]
    
    if not history:
        return {"search_query": state["user_query"]}

    prompt = ChatPromptTemplate.from_template("""
        Given the following conversation history and a follow-up question, 
        rephrase the follow-up to be a standalone question that can be 
        searched in a database.
        
        Chat History: {history}
        Follow-up: {user_query}
        Standalone Question:
    """)
    
    # Standardizing on Llama-3-8b for speed
    llm = ChatOpenAI(model="llama-3-8b", temperature=0)
    chain = prompt | llm
    
    result = chain.invoke({"history": history, "user_query": state["user_query"]})
    return {"search_query": result.content}