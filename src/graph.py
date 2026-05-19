from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.nodes import *  # This works because of your nodes.py exports


def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("condense", condense_question_node)
    workflow.add_node("retrieve", retrieve_hybrid_context)
    workflow.add_node("evaluate", evaluate_retrieval)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("actor", generate_answer)

    # The New Memory-First Path
    workflow.add_edge(START, "condense")
    workflow.add_edge("condense", "retrieve")
    workflow.add_edge("retrieve", "evaluate")

    workflow.add_conditional_edges(
        "evaluate", lambda x: x["next_step"], {"actor": "actor", "rewrite": "rewrite"}
    )
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("actor", END)

    return workflow.compile()


app = create_graph()
