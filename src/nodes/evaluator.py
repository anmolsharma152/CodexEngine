import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

# Define the strict output format we want from the LLM
class GraderOutput(BaseModel):
    is_relevant: str = Field(description="'yes' if context contains the answer, 'no' if it does not.")
    new_query: str = Field(description="If 'no', write a better, highly specific search query to find the missing info. If 'yes', leave empty.")

def evaluate_node(state):
    print("\n--- [EVALUATOR] GRADING CONTEXT ---")
    
    # Initialize the LLM and bind it to our Pydantic schema
    # Quick change in src/nodes/evaluator.py
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)
    structured_llm = llm.with_structured_output(GraderOutput)
    
    prompt = ChatPromptTemplate.from_template("""
    You are a strict retrieval evaluator. Does the following context contain the exact information needed to answer the question?
    
    Question: {query}
    
    Context: {context}
    
    If it does NOT contain the answer, rewrite the question into a better search query that targets specific keywords or alternative phrasing.
    """)
    
    chain = prompt | structured_llm
    result = chain.invoke({"query": state["initial_query"], "context": state["context"]})
    
    # Increment the loop counter
    iteration = state.get("iteration", 0) + 1
    
    if result.is_relevant.lower() == 'yes' or iteration >= 3:
        print(f"  -> ✅ Context Approved (or max tries hit: {iteration}/3). Routing to Generation.")
        return {"route": "generate", "iteration": iteration}
    else:
        print(f"  -> ❌ Context Failed. Rewriting query to: '{result.new_query}'")
        return {"current_query": result.new_query, "route": "retry", "iteration": iteration}