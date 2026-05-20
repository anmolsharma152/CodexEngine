import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

import json
from fastapi.responses import StreamingResponse

from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()
DB_URL = os.environ["DB_URL"]

from src.state import AgentState
from src.nodes.nodes import *


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
        if state.get("intent") == "research":
            return "condense"  # Hit the heavy PDF processing pipeline
        else:
            return "actor"  # Casual & Explanatory bypass the DB completely

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
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # Signal the frontend that the stream is complete
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            # Safely catch and stream any pipeline explosions
            yield f"data: {json.dumps({'type': 'error', 'content': f'Engine failure: {str(e)}'})}\n\n"

    # Return the generator wrapped in FastAPI's SSE format
    return StreamingResponse(event_generator(), media_type="text/event-stream")
