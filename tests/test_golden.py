from src.graph import app
from src.state import AgentState

inputs = AgentState(query="What is the definition of the 'Axiological' framework of coloniality in terms of value systems and the 'Standard of Civilization'?")
# Stream and capture the final state
final_state = None
for output in app.stream(inputs):
    for key, value in output.items():
        print(f"--- Node '{key}' Finished ---")
        # Keep track of the latest state update
        final_state = value 

print("\n--- FINAL NARRATIVE ANSWER ---")
# Access the answer from the Actor's final output
if final_state and "answer" in final_state:
    print(final_state["answer"])
else:
    print("No answer generated. Check Critic scores.")