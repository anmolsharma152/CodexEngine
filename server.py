import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# Load ENV before anything else
load_dotenv()

from src.state import AgentState
from src.nodes.nodes import *

# 1. Initialize FastAPI
api = FastAPI(title="CodexEngine V3 API")

# 2. Define the Graph
def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("condense", condense_question_node)
    workflow.add_node("retrieve", retrieve_hybrid_context)
    workflow.add_node("evaluate", evaluate_retrieval)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("actor", generate_answer)

    workflow.add_edge(START, "condense")
    workflow.add_edge("condense", "retrieve")
    workflow.add_edge("retrieve", "evaluate")

    workflow.add_conditional_edges(
        "evaluate",
        lambda x: x["next_step"],
        {"actor": "actor", "rewrite": "rewrite"}
    )
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("actor", END)

    return workflow.compile()

# Compile the graph as a standalone object
agent_engine = create_graph()

# 3. API Infrastructure
class ChatRequest(BaseModel):
    message: str
    history: list = [] # Should be list of [role, content] or similar

@api.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Initialize the state for the Graph
    initial_state = {
        "user_query": request.message,
        "search_query": request.message,
        "messages": request.history + [("user", request.message)],
        "context": "",
        "critic_score": 0.0,
        "revision_count": 0,
        "next_step": "condense",
        "response": ""
    }
    
    # Run the graph
    final_state = await agent_engine.ainvoke(initial_state)
    
    return {"response": final_state["response"]}

# Rename this to 'app' so uvicorn server:app works
app = api