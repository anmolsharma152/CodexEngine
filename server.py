import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from scripts.ingestion import ingest_file
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

import shutil
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse

import json
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.state import AgentState

from src.nodes.nodes import (
    analyze_intent,
    condense_question_node,
    evaluate_retrieval,
    generate_answer,
    retrieve_hybrid_context,
    rewrite_query,
)

load_dotenv()
DB_URL = os.environ["DB_URL"]


# 1. Define the Graph (Now with Intent Routing)
def create_graph(checkpointer):
    workflow = StateGraph(AgentState)

    # Add all nodes including the router
    workflow.add_node("router", analyze_intent)
    workflow.add_node("condense", condense_question_node)
    workflow.add_node("retrieve", retrieve_hybrid_context)
    workflow.add_node("evaluate", evaluate_retrieval)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("actor", generate_answer)

    # Point START directly to the traffic cop
    workflow.add_edge(START, "router")

    # Dynamic Routing Condition
    def route_after_analysis(state: AgentState):
        if state.get("intent") == "retrieval_required":
            return "condense"  # Hit the heavy PDF processing pipeline
        else:
            return "actor"  # Casual & Parametric bypass the DB completely

    workflow.add_conditional_edges(
        "router", route_after_analysis, {"condense": "condense", "actor": "actor"}
    )

    # Standard RAG Sub-flow (only runs if routed to 'condense')
    workflow.add_edge("condense", "retrieve")
    workflow.add_edge("retrieve", "evaluate")
    workflow.add_conditional_edges(
        "evaluate", lambda x: x["next_step"], {"actor": "actor", "rewrite": "rewrite"}
    )
    workflow.add_edge("rewrite", "retrieve")

    # Exit point
    workflow.add_edge("actor", END)

    return workflow.compile(checkpointer=checkpointer)


# 2. Database & App Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # LangGraph uses native psycopg; strip out the SQLAlchemy driver flag if present
    checkpointer_url = DB_URL.replace("postgresql+psycopg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(checkpointer_url) as checkpointer:
        await checkpointer.setup()
        app.state.agent_engine = create_graph(checkpointer)
        yield


# 3. Initialize FastAPI with the lifespan
app = FastAPI(title="CodexEngine V3 API", lifespan=lifespan)

# --- HARDENED CORS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------


# 4. API Infrastructure
class ChatRequest(BaseModel):
    message: str
    thread_id: str  # No more manual history array!


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    initial_state = {
        "user_query": request.message,
        "search_query": request.message,
        "messages": [("user", request.message)],
        "context": "",
        "critic_score": 0.0,
        "evaluation": {},
        "revision_count": 0,
        "response": "",
    }

    async def event_generator():
        try:
            # Wiretap the LangGraph execution using version="v2"
            async for event in app.state.agent_engine.astream_events(
                initial_state, config, version="v2"
            ):
                kind = event["event"]

                # 1. Stream Node Transitions (System Thoughts)
                node_name = event.get("name", "unknown node")
                if kind == "on_chain_start" and node_name in [
                    "router",
                    "condense",
                    "retrieve",
                    "evaluate",
                    "rewrite",
                    "actor",
                ]:
                    yield f"data: {json.dumps({'type': 'status', 'content': f'Agent routing to {node_name}...'})}\n\n"

                # 2. Stream LLM Tokens (The actual answer)
                elif kind == "on_chat_model_stream":
                    # THE Fix: Only stream tokens if they come from the final Actor node
                    if event.get("metadata", {}).get("langgraph_node") == "actor":
                        chunk = event["data"]["chunk"].content
                        if chunk:
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # Fetch final state and yield structured evaluation metrics for the UI Command Center
            try:
                state = await app.state.agent_engine.aget_state(config)
                evaluation = state.values.get("evaluation", {})
                intent = state.values.get("intent", "retrieval_required")
                context = state.values.get("context", "")
                yield f"data: {json.dumps({'type': 'evaluation', 'content': evaluation, 'intent': intent, 'context': context})}\n\n"
            except Exception as e:
                print(f"--- [ERROR] Failed to yield evaluation metrics: {e} ---")

            # Signal the frontend that the stream is complete
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            # Safely catch and stream any pipeline explosions
            yield f"data: {json.dumps({'type': 'error', 'content': f'Engine failure: {str(e)}'})}\n\n"

    # Return the generator wrapped in FastAPI's SSE format
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/chat/{thread_id}/history")
async def chat_history_endpoint(thread_id: str):
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await app.state.agent_engine.aget_state(config)
        messages = state.values.get("messages", [])
        history = []
        for msg in messages:
            if isinstance(msg, tuple):
                role, content = msg[0], msg[1]
            elif hasattr(msg, "type"):
                role = "user" if msg.type == "human" else ("assistant" if msg.type == "ai" else msg.type)
                content = msg.content
            else:
                continue
            if role in ["user", "assistant"]:
                history.append({"role": role, "content": content})
        return {"history": history}
    except Exception as e:
        print(f"\n❌ [ERROR] Failed to fetch history: {str(e)}")
        return JSONResponse(status_code=500, content={"message": str(e)})


# Create a staging directory for uploaded documents
os.makedirs("data/raw", exist_ok=True)


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_path = f"data/raw/{file.filename}"

        # Save the file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"\n📥 [INGESTION] Received file: {file.filename}")

        # Trigger the Vector DB chunking and ingestion asynchronously
        await asyncio.to_thread(ingest_file, file_path)

        return JSONResponse(
            status_code=200,
            content={"message": f"Successfully uploaded and ingested {file.filename}"},
        )

    except Exception as e:
        print(f"\n❌ [ERROR] Upload failed: {str(e)}")
        return JSONResponse(status_code=500, content={"message": str(e)})
