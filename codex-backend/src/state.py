from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    CodexEngine V4.0 State: Persistent Cognition and Structured Evaluation.
    """

    # 1. Memory & State Tracking
    # user_query: The immutable anchor to prevent "Nigeria Delta" drift.
    user_query: str
    # search_query: What the Rewriter optimizes.
    search_query: str
    # messages: The actual conversation history for the 'Condense' node.
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 2. RAG Data
    # Using str for concatenated context to keep the Actor prompt clean.
    context: str

    # 3. V2.5 Guardrails (Keeping these!)
    intent: str
    critic_score: float
    evaluation: dict
    revision_count: int
    next_step: str

    # 4. Output
    response: str
