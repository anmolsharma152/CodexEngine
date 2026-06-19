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
    async for output in app.astream(inputs, config):
        for key, value in output.items():
            final_state = value

    assert final_state is not None, "Pipeline produced no final state"
    response_text = final_state.get("response", "")
    assert response_text, f"Response was empty. State: {final_state}"
    assert len(response_text) > 50, f"Response too short ({len(response_text)} chars)"
    print(f"PASS: Response generated ({len(response_text)} chars)")


if __name__ == "__main__":
    asyncio.run(run())
