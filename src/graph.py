from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.retriever import retrieve_parent_context
from src.nodes.evaluator import evaluate_node
from src.nodes.actor import actor_node 

# The routing function reads the state set by the Evaluator
def route_decision(state):
    if state["route"] == "generate":
        return "generate"
    else:
        return "retrieve"

def create_codex_engine():
    workflow = StateGraph(AgentState)

    # 1. Add all three nodes
    workflow.add_node("retrieve", retrieve_parent_context)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("generate", actor_node)

    # 2. Define the Flow
    workflow.set_entry_point("retrieve")
    
    # After retrieval, ALWAYS evaluate the context
    workflow.add_edge("retrieve", "evaluate")
    
    # Conditional Fork: The Graph decides where to go based on the Evaluator's decision
    workflow.add_conditional_edges(
        "evaluate", 
        route_decision, 
        {
            "generate": "generate",  # Go to the Actor
            "retrieve": "retrieve"   # Loop back to the Retriever
        }
    )
    
    # After generation, end the process
    workflow.add_edge("generate", END)

    return workflow.compile()