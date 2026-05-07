import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def actor_node(state):
    """
    LangGraph Node: Synthesizes the final answer using 
    the expanded parent context.
    """
    print("--- AGENTIC ACTOR: GENERATING RESPONSE ---")
    
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    
    prompt = ChatPromptTemplate.from_template("""
    You are the CodexEngine V2 Core. Use the following EXPANDED context to answer the user's question. 
    
    Context:
    {context}
    
    Question: {query}
    
    Instruction: Provide a detailed, technical response. If the information is missing, admit it.
    """)
    
    chain = prompt | llm
    response = chain.invoke({"context": state["context"], "query": state["initial_query"]})
    
    return {"answer": response.content}