import json
from src.graph import app
from src.state import AgentState

def run_rigorous_tests():
    # 1. Load the Benchmarks
    with open("eval/golden_queries.json", "r") as f:
        data = json.load(f)
        queries = data["dataset"]

    results = []

    print(f"🚀 Starting Rigorous Sweep of {len(queries)} Queries...")

    for q in queries:
        print(f"\n{'='*50}")
        print(f"TESTING: {q['query_id']} ({q['eval_focus']})")
        print(f"QUESTION: {q['question']}")
        print(f"{'='*50}")

        inputs = AgentState(query=q["question"])
        
        # Run the full agentic loop
        final_answer = ""
        for output in app.stream(inputs):
            for node, state in output.items():
                if node == "evaluate":
                    print(f"-> Critic Score: {state.get('critic_score')}")
                if node == "rewrite":
                    print(f"-> Rewriter Pivot: {state.get('query')}")
                if node == "actor":
                    final_answer = state.get("answer")

        results.append({
            "query_id": q["query_id"],
            "question": q["question"],
            "v2_5_answer": final_answer
        })

    # Save for comparison
    with open("eval/v2_5_live_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Sweep Complete. Results saved to eval/v2_5_live_results.json")

if __name__ == "__main__":
    run_rigorous_tests()