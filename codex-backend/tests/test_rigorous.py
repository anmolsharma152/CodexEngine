import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
import asyncio
from langgraph.checkpoint.memory import MemorySaver
from server import create_graph

checkpointer = MemorySaver()
app = create_graph(checkpointer)


async def run_rigorous_tests():
    with open("eval/golden_queries.json", "r") as f:
        data = json.load(f)
        queries = data["dataset"]

    results = []
    failures = []

    for q in queries:
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

        final_answer = ""
        try:
            async for output in app.astream(inputs, config):
                for node, state in output.items():
                    if node == "actor":
                        final_answer = state.get("response", "")
        except Exception as e:
            failures.append({"query_id": q["query_id"], "error": str(e)})
            continue

        assert final_answer, f"[{q['query_id']}] Empty response. Question: {q['question'][:60]}..."
        assert len(final_answer) > 50, f"[{q['query_id']}] Response too short ({len(final_answer)} chars)"

        results.append({
            "query_id": q["query_id"],
            "question": q["question"],
            "answer_length": len(final_answer),
        })

    with open("eval/v4_0_live_results.json", "w") as f:
        json.dump(results, f, indent=2)

    assert not failures, f"{len(failures)} queries failed: {failures}"
    assert len(results) == len(queries), f"Only {len(results)}/{len(queries)} queries completed"
    print(f"PASS: All {len(results)} queries completed successfully")


if __name__ == "__main__":
    asyncio.run(run_rigorous_tests())
