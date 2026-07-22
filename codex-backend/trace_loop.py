import asyncio
import json
import uuid
import sys
import os

# Ensure the correct path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.agent.agent_loop import agent_loop
from src.db import async_engine, ensure_schema
from sqlalchemy import text

async def main():
    ensure_schema()
    user_id = "00000000-0000-0000-0000-000000000001"
    thread_id = str(uuid.uuid4())
    project_id = "project-alpha"
    
    prompt = "Analyze the `search_documents` function's reranking logic and save the analysis."
    print(f"--- STARTING TRACE ---")
    print(f"USER PROMPT: {prompt}")
    print(f"PROJECT: {project_id}\n")
    
    print(">>> ENTERING AGENT LOOP")
    
    # We use agent_loop directly. Since it's an async generator, we async iterate over it.
    async for event_str in agent_loop(
        user_message=prompt,
        thread_id=thread_id,
        user_id=user_id,
        project_id=project_id,
        provider="groq",
        model="llama-3.1-8b-instant"
    ):
        event = json.loads(event_str)
        if event["type"] == "status":
            print(f"[STATUS] {event['content']}")
        elif event["type"] == "tool_call":
            name = event['content']['name']
            args = event['content']['args']
            print(f"\n[TOOL CALL] -> {name}")
            print(f"           Args: {json.dumps(args, indent=2)}")
        elif event["type"] == "tool_result":
            name = event['content']['name']
            if 'error' in event['content']:
                res = f"ERROR: {event['content']['error']}"
            else:
                res = event['content'].get('result', '')
                if len(res) > 200:
                    res = res[:200] + "... (truncated)"
            print(f"[TOOL RESULT] <- {name}")
            print(f"             Output: {res}\n")
        elif event["type"] == "token":
            # Print response tokens as they stream in
            print(event["content"], end="", flush=True)
        elif event["type"] == "done":
            print("\n\n>>> EXITED AGENT LOOP")
            
    print("\n--- DATABASE VERIFICATION (PERSISTENCE) ---")
    print("Checking tool_invocations table...")
    async with async_engine.connect() as conn:
        res = await conn.execute(text(f"SELECT tool_name, duration_ms, arguments FROM tool_invocations WHERE thread_id = '{thread_id}' ORDER BY created_at"))
        for row in res:
            print(f"Logged Tool: {row[0]} | Duration: {row[1]}ms | Args: {str(row[2])[:100]}")
            
    print("\nChecking workspace_artifacts table...")
    async with async_engine.connect() as conn:
        res = await conn.execute(text(f"SELECT path, artifact_type FROM workspace_artifacts WHERE user_id = '{user_id}'"))
        for row in res:
            print(f"Created Artifact: {row[0]} (Type: {row[1]})")

if __name__ == "__main__":
    asyncio.run(main())
