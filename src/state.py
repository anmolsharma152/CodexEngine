from typing import TypedDict

class AgentState(TypedDict):
    initial_query: str   # The user's original question
    current_query: str   # The actively rewritten search query
    context: str         # The retrieved text
    response: str        # The final generated answer
    iteration: int       # Loop counter
    route: str           # "generate" or "retry"