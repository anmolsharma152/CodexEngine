import asyncio
import json
import time
import uuid
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.agent.agent_loop import agent_loop
from src.db import async_engine, ensure_schema
from sqlalchemy import text

PROMPTS = [
    {
        "id": "Prompt_A",
        "name": "Cross-Artifact Synthesis",
        "prompt": "List all saved artifacts in the `analysis/` folder, read each one, and generate a unified master roadmap saved to `plans/system_roadmap.md`.",
        "project_id": "project-alpha",
        "user_id": "00000000-0000-0000-0000-000000000001",
    },
    {
        "id": "Prompt_B",
        "name": "Overwrite & Refinement Test",
        "prompt": "Read `analysis/search_documents_reranking_logic.md`, add a new section evaluating BM25 vs Vector score weights, and save the updated analysis to the same path.",
        "project_id": "project-alpha",
        "user_id": "00000000-0000-0000-0000-000000000001",
    },
    {
        "id": "Prompt_C",
        "name": "Web Research + Artifact Production",
        "prompt": "Search the web for python duckduckgo search library ddgs, summarize the key details, and save a migration note to `analysis/web_search_migration.md`.",
        "project_id": "project-alpha",
        "user_id": "00000000-0000-0000-0000-000000000001",
    },
    {
        "id": "Prompt_D",
        "name": "Project Isolation Boundary Test",
        "prompt": "Read the reranking logic analysis artifact.",
        "project_id": "project-beta",  # Operating in project-beta where analysis/ search_documents_reranking_logic.md should NOT exist
        "user_id": "00000000-0000-0000-0000-000000000001",
    },
]

PROVIDERS = [
    {"provider": "groq", "model": "qwen/qwen3.6-27b", "label": "Groq (Qwen 27B)"},
    {"provider": "nvidia", "model": "meta/llama-3.3-70b-instruct", "label": "NVIDIA NIM (Llama 3.3 70B)"},
    {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct:free", "label": "OpenRouter Free (Llama 3.3 70B)"},
    {"provider": "cerebras", "model": "llama3.3-70b", "label": "Cerebras Cloud (Llama 3.3 70B)"},
]

async def run_single_benchmark(p_info: dict, p_config: dict) -> dict:
    provider = p_info["provider"]
    model = p_info["model"]
    label = p_info["label"]
    thread_id = str(uuid.uuid4())
    print(f"\n=======================================================")
    print(f"RUNNING BENCHMARK: {label}")
    print(f"Prompt={p_config['id']} ({p_config['name']}) | Thread={thread_id}")
    print(f"=======================================================")

    tool_calls_made = []
    tool_results_received = []
    tokens = []
    start_time = time.time()
    ttft = None

    try:
        async for event_str in agent_loop(
            user_message=p_config["prompt"],
            thread_id=thread_id,
            user_id=p_config["user_id"],
            project_id=p_config["project_id"],
            provider=provider,
            model=model,
        ):
            event = json.loads(event_str)
            etype = event.get("type")
            if etype == "token":
                if ttft is None:
                    ttft = round((time.time() - start_time) * 1000, 2)
                tokens.append(event["content"])
            elif etype == "tool_call":
                tc = event["content"]
                print(f"  [Tool Call] {tc['name']}")
                tool_calls_made.append(tc)
            elif etype == "tool_result":
                tr = event["content"]
                print(f"  [Tool Result] {tr['name']}")
                tool_results_received.append(tr)
            elif etype == "done":
                break
    except Exception as e:
        print(f"  [ERROR] Execution failed for {label}: {e}")
        return {
            "label": label,
            "provider": provider,
            "model": model,
            "prompt_id": p_config["id"],
            "status": "FAILED",
            "error": str(e),
            "duration_s": round(time.time() - start_time, 2),
        }

    duration = round(time.time() - start_time, 2)
    full_text = "".join(tokens)
    token_count = len(full_text.split()) * 1.3  # Approx token count from words
    tps = round(token_count / duration, 2) if duration > 0 else 0

    print(f"  --> SUCCESS: Duration={duration}s | TTFT={ttft}ms | Est. Speed={tps} tokens/sec")

    return {
        "label": label,
        "provider": provider,
        "model": model,
        "prompt_id": p_config["id"],
        "prompt_name": p_config["name"],
        "status": "SUCCESS",
        "duration_s": duration,
        "ttft_ms": ttft,
        "est_tokens_per_sec": tps,
        "tool_calls_count": len(tool_calls_made),
        "response_snippet": full_text[:200] + "...",
    }

async def main():
    ensure_schema()
    results = []
    
    print("=======================================================")
    print("MULTI-PROVIDER PERFORMANCE & LATENCY BENCHMARK")
    print(f"Providers: {[p['label'] for p in PROVIDERS]}")
    print("=======================================================")

    # Run Prompt A across all providers to measure latency & TPS
    prompt_cfg = PROMPTS[0]
    for p_info in PROVIDERS:
        res = await run_single_benchmark(p_info, prompt_cfg)
        results.append(res)
        await asyncio.sleep(1)

    out_file = "multi_provider_benchmark.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=======================================================")
    print(f"BENCHMARK COMPLETE! Results saved to {out_file}")
    print(f"=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
