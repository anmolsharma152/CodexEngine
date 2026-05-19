import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()
DB_URL = os.environ["DB_URL"]

from src.state import AgentState
from src.nodes.nodes import *


# 1. Define the Graph (Now accepts a checkpointer)
def create_graph(checkpointer):
    workflow = StateGraph(AgentState)

    workflow.add_node("condense", condense_question_node)
    workflow.add_node("retrieve", retrieve_hybrid_context)
    workflow.add_node("evaluate", evaluate_retrieval)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("actor", generate_answer)

    workflow.add_edge(START, "condense")
    workflow.add_edge("condense", "retrieve")
    workflow.add_edge("retrieve", "evaluate")

    workflow.add_conditional_edges(
        "evaluate", lambda x: x["next_step"], {"actor": "actor", "rewrite": "rewrite"}
    )
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("actor", END)

    # Compile the graph WITH the PostgresSaver
    return workflow.compile(checkpointer=checkpointer)


# 2. Database & App Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create connection pool and checkpointer
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        # Automatically creates the 'checkpoints' tables in your DB if missing
        await checkpointer.setup()

        # Compile graph and attach it to the running FastAPI app state
        app.state.agent_engine = create_graph(checkpointer)

        yield
    # Shutdown: Pool closes automatically


# 3. Initialize FastAPI with the lifespan
app = FastAPI(title="CodexEngine V3 API", lifespan=lifespan)


# 4. API Infrastructure
class ChatRequest(BaseModel):
    message: str
    thread_id: str  # No more manual history array!


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Pass the thread_id to LangGraph so it knows which memory to load/save
    config = {"configurable": {"thread_id": request.thread_id}}

    # We only inject the newest message. The checkpointer handles the rest natively.
    initial_state = {
        "user_query": request.message,
        "search_query": request.message,
        "messages": [("user", request.message)],
        "context": "",
        "critic_score": 0.0,
        "revision_count": 0,
        "next_step": "condense",
        "response": "",
    }

    # Run the graph using the engine stored in the app state
    final_state = await app.state.agent_engine.ainvoke(initial_state, config)

    return {"response": final_state["response"]}
