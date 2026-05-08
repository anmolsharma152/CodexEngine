from langchain_openai import ChatOpenAI # Or your local Llama-3-8b
from langchain_core.prompts import ChatPromptTemplate

def condense_question_node(state: AgentState):
    """Resolves pronouns and context based on history."""
    history = state["messages"][:-1]
    if not history:
        return {"search_query": state["user_query"]}

    prompt = ChatPromptTemplate.from_template("""
        Given the following conversation and a follow-up question, 
        rephrase the follow-up to be a standalone question.
        
        Chat History: {history}
        Follow-up: {user_query}
        Standalone Question:
    """)
    
    # Using your standardized 8b model
    llm = ChatOpenAI(model="llama-3-8b", temperature=0)
    chain = prompt | llm
    
    result = chain.invoke({"history": history, "user_query": state["user_query"]})
    return {"search_query": result.content}