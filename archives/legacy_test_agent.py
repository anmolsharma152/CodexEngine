import json
from src.graph import create_codex_engine

def run_v2_test():
    print("🏛️  Starting CodexEngine V2: Agentic Evaluation\n")
    
    # Initialize the compiled LangGraph
    app = create_codex_engine()
    
    # Load your Golden Queries
    with open("eval/golden_queries.json", "r") as f:
        data = json.load(f)
    
    v2_results = []

    for item in data['dataset']:
        print(f"--- [TESTING] {item['eval_focus']} ---")
        print(f"Query: {item['question']}")
        
        # Initial State in test_agent.py (around line 21)
        initial_state = {
            "initial_query": item['question'],
            "current_query": item['question'],
            "context": "",
            "response": "",
            "iteration": 0,
            "route": ""
        }
        
        # Execute the Graph
        # This will trigger our retriever node (ONNX) then our actor node (Groq)
        final_state = app.invoke(initial_state)
        
        print(f"V2 Answer: {final_state['response'][:250]}...\n")
        
        v2_results.append({
            "query_id": item['query_id'],
            "question": item['question'],
            "v2_answer": final_state['response']
        })

    # Save for final comparison
    with open("eval/v2_results.json", "w") as f:
        json.dump(v2_results, f, indent=2)
    
    print("✅ V2 Evaluation Complete. Results saved to eval/v2_results.json")

if __name__ == "__main__":
    run_v2_test()
