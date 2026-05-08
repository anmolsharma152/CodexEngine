from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.retriever import retrieve_hybrid_context
from src.nodes.evaluator import evaluate_retrieval
from src.nodes.rewriter import rewrite_query
from src.nodes.actor import generate_answer

def create_graph():
    # 1. Initialize Graph with our Pydantic State
    workflow = StateGraph(AgentState)

    # 2. Add Nodes
    workflow.add_node("retrieve", retrieve_hybrid_context)
    workflow.add_node("evaluate", evaluate_retrieval)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("actor", generate_answer)

    # 3. Build Edges (The Logic Map)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "evaluate")

    # Conditional Routing from Evaluator
    workflow.add_conditional_edges(
        "evaluate",
        lambda x: x.next_step,
        {
            "actor": "actor",
            "rewrite": "rewrite"
        }
    )

    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("actor", END)

    return workflow.compile()

# Compilation
app = create_graph()