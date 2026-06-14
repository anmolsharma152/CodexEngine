import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import asyncio
from langgraph.checkpoint.memory import MemorySaver
from server import create_graph

checkpointer = MemorySaver()
app = create_graph(checkpointer)

query = "What is the definition of the 'Axiological' framework of coloniality in terms of value systems and the 'Standard of Civilization'?"

inputs = {
    "user_query": query,
    "search_query": query,
    "messages": [("user", query)],
    "context": "",
    "critic_score": 0.0,
    "revision_count": 0,
    "response": "",
}

config = {"configurable": {"thread_id": "test_golden_thread"}}


async def run():
    final_state = None
    # Stream and capture the final state using the async graph stream
    async for output in app.astream(inputs, config):
        for key, value in output.items():
            print(f"--- Node '{key}' Finished ---")
            final_state = value

    print("\n--- FINAL NARRATIVE ANSWER ---")
    # Access the answer from the Actor's final output ("response")
    if final_state and "response" in final_state:
        print(final_state["response"])
    else:
        print("No response generated. Check Critic scores.")


if __name__ == "__main__":
    asyncio.run(run())
