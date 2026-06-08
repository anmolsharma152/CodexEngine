import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
import asyncio
from langgraph.checkpoint.memory import MemorySaver
from server import create_graph

checkpointer = MemorySaver()
app = create_graph(checkpointer)


async def run_rigorous_tests():
    # 1. Load the Benchmarks
    with open("eval/golden_queries.json", "r") as f:
        data = json.load(f)
        queries = data["dataset"]

    results = []

    print(f"🚀 Starting Rigorous Sweep of {len(queries)} Queries...")

    for q in queries:
        print(f"\n{'=' * 50}")
        print(f"TESTING: {q['query_id']} ({q['eval_focus']})")
        print(f"QUESTION: {q['question']}")
        print(f"{'=' * 50}")

        inputs = {
            "user_query": q["question"],
            "search_query": q["question"],
            "messages": [("user", q["question"])],
            "context": "",
            "critic_score": 0.0,
            "revision_count": 0,
            "response": "",
        }

        config = {"configurable": {"thread_id": f"thread_{q['query_id']}"}}

        # Run the full agentic loop
        final_answer = ""
        async for output in app.astream(inputs, config):
            for node, state in output.items():
                if node == "evaluate":
                    print(f"-> Critic Score: {state.get('critic_score')}")
                if node == "rewrite":
                    print(f"-> Rewriter Pivot: {state.get('search_query')}")
                if node == "actor":
                    final_answer = state.get("response", "")

        results.append(
            {
                "query_id": q["query_id"],
                "question": q["question"],
                "v3_0_answer": final_answer,
            }
        )

    # Save for comparison
    with open("eval/v4_0_live_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n✅ Sweep Complete. Results saved to eval/v4_0_live_results.json")


if __name__ == "__main__":
    asyncio.run(run_rigorous_tests())
