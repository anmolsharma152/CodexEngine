import os
import asyncio
import uuid
import json
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import create_engine, text

from scripts.ingestion import ingest_file
from src.state import AgentState
from src.nodes.nodes import (
    analyze_intent,
    condense_question_node,
    evaluate_retrieval,
    generate_answer,
    retrieve_hybrid_context,
    rewrite_query,
)
from src.log_utils import logger
from src.supabase_client import supabase
import src.storage_client as storage_client

load_dotenv()
DB_URL = os.environ["DB_URL"]
engine = create_engine(DB_URL)


def ensure_schema():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS threads (
                id VARCHAR(255) PRIMARY KEY,
                user_id UUID NOT NULL,
                title VARCHAR(255) NOT NULL,
                timestamp BIGINT NOT NULL,
                pinned BOOLEAN DEFAULT FALSE
            );
        """))
        conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'threads' AND column_name = 'user_id' AND data_type = 'integer'
                ) THEN
                    ALTER TABLE threads DROP CONSTRAINT IF EXISTS threads_user_id_fkey;
                    ALTER TABLE threads ALTER COLUMN user_id TYPE UUID USING '00000000-0000-0000-0000-000000000000'::uuid;
                END IF;
            END $$;
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prose_chunks (
                id BIGSERIAL PRIMARY KEY,
                content TEXT,
                metadata JSONB,
                embedding vector(384)
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prose_chunks_metadata ON prose_chunks USING GIN (metadata);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads (user_id);"))
        conn.commit()


ensure_schema()

security_scheme = HTTPBearer()


class AuthUser:
    def __init__(self, user, token: str):
        self.id = user.id
        self.email = user.email
        self.user_metadata = getattr(user, "user_metadata", {})
        self.token = token


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    try:
        resp = await asyncio.to_thread(supabase.auth.get_user, credentials.credentials)
        return AuthUser(resp.user, credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def verify_thread_ownership(thread_id: str, user_id: str):
    query = text("SELECT user_id FROM threads WHERE id = :thread_id;")
    with engine.connect() as conn:
        res = conn.execute(query, {"thread_id": thread_id}).fetchone()
        if res and str(res[0]) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this thread",
            )


STORAGE_BUCKET = "documents"


def _storage_path(user_id: str, filename: str, thread_id: str | None = None) -> str:
    if thread_id:
        return f"{user_id}/{thread_id}/{filename}"
    return f"{user_id}/{filename}"


async def _download_from_storage(storage_path: str, auth_token: str | None = None) -> str | None:
    try:
        data = await storage_client.download_file(STORAGE_BUCKET, storage_path, auth_token)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(storage_path)[1])
        tmp.write(data)
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.error(f"Failed to download {storage_path} from storage: {e}")
        return None


async def _list_storage_files(prefix: str, auth_token: str | None = None) -> list[dict]:
    try:
        objects = await storage_client.list_files(STORAGE_BUCKET, prefix, auth_token)
        files = []
        for obj in objects:
            name = obj.get("name")
            if name and not name.endswith("/"):
                files.append({
                    "filename": name,
                    "size_bytes": obj.get("metadata", {}).get("size", 0),
                    "updated_at": obj.get("updated_at", ""),
                })
        return files
    except Exception as e:
        logger.error(f"Failed to list storage files under {prefix}: {e}")
        return []


async def _remove_storage_paths(paths: list[str], auth_token: str | None = None):
    try:
        await storage_client.remove_files(STORAGE_BUCKET, paths, auth_token)
    except Exception as e:
        logger.error(f"Failed to remove storage paths {paths}: {e}")


# Graph definition
def create_graph(checkpointer):
    workflow = StateGraph(AgentState)
    workflow.add_node("router", analyze_intent)
    workflow.add_node("condense", condense_question_node)
    workflow.add_node("retrieve", retrieve_hybrid_context)
    workflow.add_node("evaluate", evaluate_retrieval)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("actor", generate_answer)
    workflow.add_edge(START, "router")

    def route_after_analysis(state: AgentState):
        if state.get("intent") == "retrieval_required":
            return "condense"
        return "actor"

    workflow.add_conditional_edges(
        "router", route_after_analysis, {"condense": "condense", "actor": "actor"}
    )
    workflow.add_edge("condense", "retrieve")
    workflow.add_edge("retrieve", "evaluate")
    workflow.add_conditional_edges(
        "evaluate", lambda x: x["next_step"], {"actor": "actor", "rewrite": "rewrite"}
    )
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("actor", END)
    return workflow.compile(checkpointer=checkpointer)


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage_client.ensure_bucket(STORAGE_BUCKET)
    checkpointer_url = DB_URL.replace("postgresql+psycopg://", "postgresql://")
    async with AsyncPostgresSaver.from_conn_string(checkpointer_url) as checkpointer:
        await checkpointer.setup()
        app.state.agent_engine = create_graph(checkpointer)
        logger.info("LangGraph engine ready, LangSmith tracing active")
        yield


# FastAPI app
app = FastAPI(title="CodexEngine V4 API", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "app": "CodexEngine V4", "version": "4.0"}
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Schemas
class AuthRequest(BaseModel):
    email: str
    password: str
    username: str | None = None


class SaveThreadRequest(BaseModel):
    id: str
    title: str
    timestamp: int
    pinned: bool = False


class ChatRequest(BaseModel):
    message: str
    thread_id: str


# Endpoints
@app.post("/register")
async def register_endpoint(request: AuthRequest):
    email = request.email.strip().lower()
    password = request.password
    username = request.username or email.split("@")[0]
    if not email or not password:
        return JSONResponse(status_code=400, content={"message": "Email and password are required"})
    try:
        resp = await asyncio.to_thread(
            supabase.auth.sign_up,
            {"email": email, "password": password, "options": {"data": {"username": username}}},
        )
        if resp.user:
            logger.info(f"User registered: {email} ({resp.user.id})")
            return {"message": "User registered successfully", "user_id": resp.user.id}
        return JSONResponse(status_code=400, content={"message": "Registration failed"})
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JSONResponse(status_code=400, content={"message": str(e)})


@app.post("/login")
async def login_endpoint(request: AuthRequest):
    email = request.email.strip().lower()
    password = request.password
    if not email or not password:
        return JSONResponse(status_code=400, content={"message": "Email and password are required"})
    try:
        resp = await asyncio.to_thread(supabase.auth.sign_in_with_password, {"email": email, "password": password})
        if resp.session:
            logger.info(f"User logged in: {email}")
            return {
                "access_token": resp.session.access_token,
                "token_type": "bearer",
                "email": resp.user.email,
                "username": resp.user.user_metadata.get("username", ""),
            }
        return JSONResponse(status_code=401, content={"message": "Invalid credentials"})
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(status_code=401, content={"message": str(e)})


@app.get("/user/me")
async def get_me_endpoint(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.user_metadata.get("username", ""),
    }


@app.get("/threads")
async def get_threads_endpoint(current_user=Depends(get_current_user)):
    query = text("SELECT id, title, timestamp, pinned FROM threads WHERE user_id = :user_id ORDER BY pinned DESC, timestamp DESC;")
    threads = []
    with engine.connect() as conn:
        res = conn.execute(query, {"user_id": current_user.id})
        for r in res:
            threads.append({"id": r[0], "title": r[1], "timestamp": int(r[2]), "pinned": bool(r[3])})
    return {"threads": threads}


@app.post("/threads")
async def save_thread_endpoint(request: SaveThreadRequest, current_user=Depends(get_current_user)):
    select_query = text("SELECT id FROM threads WHERE id = :id AND user_id = :user_id;")
    with engine.connect() as conn:
        existing = conn.execute(select_query, {"id": request.id, "user_id": current_user.id}).fetchone()
        if existing:
            update_query = text("UPDATE threads SET title = :title, timestamp = :timestamp, pinned = :pinned WHERE id = :id AND user_id = :user_id;")
            conn.execute(update_query, {"title": request.title, "timestamp": request.timestamp, "pinned": request.pinned, "id": request.id, "user_id": current_user.id})
        else:
            insert_query = text("INSERT INTO threads (id, user_id, title, timestamp, pinned) VALUES (:id, :user_id, :title, :timestamp, :pinned);")
            conn.execute(insert_query, {"id": request.id, "user_id": current_user.id, "title": request.title, "timestamp": request.timestamp, "pinned": request.pinned})
        conn.commit()
    return {"message": "Thread saved successfully"}


@app.delete("/threads/{thread_id}")
async def delete_thread_endpoint(thread_id: str, current_user=Depends(get_current_user)):
    verify_thread_ownership(thread_id, current_user.id)
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM threads WHERE id = :thread_id AND user_id = :user_id;"), {"thread_id": thread_id, "user_id": current_user.id})
        conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'thread_id' = :thread_id;"), {"thread_id": thread_id})
        conn.commit()
    return {"message": "Thread deleted successfully"}


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, current_user=Depends(get_current_user)):
    verify_thread_ownership(request.thread_id, current_user.id)
    config = {"configurable": {"thread_id": request.thread_id, "user_id": current_user.id}}

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
            async for event in app.state.agent_engine.astream_events(initial_state, config, version="v2"):
                kind = event["event"]
                node_name = event.get("name", "unknown node")
                if kind == "on_chain_start" and node_name in ["router", "condense", "retrieve", "evaluate", "rewrite", "actor"]:
                    yield f"data: {json.dumps({'type': 'status', 'content': f'Agent routing to {node_name}...'})}\n\n"
                elif kind == "on_chat_model_stream":
                    if event.get("metadata", {}).get("langgraph_node") == "actor":
                        chunk = event["data"]["chunk"].content
                        if chunk:
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            try:
                state = await app.state.agent_engine.aget_state(config)
                evaluation = state.values.get("evaluation", {})
                intent = state.values.get("intent", "retrieval_required")
                context = state.values.get("context", "")
                yield f"data: {json.dumps({'type': 'evaluation', 'content': evaluation, 'intent': intent, 'context': context})}\n\n"
            except Exception as e:
                logger.error(f"Failed to yield evaluation metrics: {e}")

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Engine failure: {str(e)}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/chat/{thread_id}/history")
async def chat_history_endpoint(thread_id: str, current_user=Depends(get_current_user)):
    try:
        verify_thread_ownership(thread_id, current_user.id)
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
        logger.error(f"Failed to fetch history: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.post("/upload")
async def upload_document(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    raw = await file.read()
    storage_path = _storage_path(current_user.id, file.filename)
    await storage_client.upload_file(STORAGE_BUCKET, storage_path, raw, file.content_type, auth_token=current_user.token)
    try:
        tmp_path = await _download_from_storage(storage_path, auth_token=current_user.token)
        if not tmp_path:
            raise RuntimeError("Failed to retrieve uploaded file for ingestion")
        renamed = os.path.join(os.path.dirname(tmp_path), file.filename)
        os.rename(tmp_path, renamed)
        await asyncio.to_thread(ingest_file, renamed, None, current_user.id)
        os.unlink(renamed)
        logger.info(f"Uploaded and ingested: {file.filename}")
        return JSONResponse(status_code=200, content={"message": f"Successfully uploaded and ingested {file.filename}"})
    except Exception as e:
        logger.error(f"Ingestion failed, cleaning up storage file: {e}")
        await storage_client.remove_files(STORAGE_BUCKET, [storage_path], auth_token=current_user.token)
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.get("/documents")
async def list_documents_endpoint(current_user=Depends(get_current_user)):
    try:
        user_prefix = f"{current_user.id}/"
        storage_files = await _list_storage_files(user_prefix, auth_token=current_user.token)

        with engine.connect() as conn:
            sql = text("""
                SELECT metadata->>'source' as source, count(*) as count
                FROM prose_chunks
                WHERE metadata->>'user_id' = :user_id
                GROUP BY source;
            """)
            res = conn.execute(sql, {"user_id": str(current_user.id)})
            db_counts = {r[0]: r[1] for r in res}

        merged = []
        for sf in storage_files:
            path = sf["filename"]
            rel = path.removeprefix(user_prefix)
            parts = rel.split("/", 1)
            basename = parts[-1]
            thread_id = parts[0] if len(parts) > 1 and parts[0] != parts[-1] else None

            merged.append({
                "filename": basename,
                "size_bytes": sf["size_bytes"],
                "chunks_count": db_counts.get(basename, 0),
                "status": "Ingested" if basename in db_counts else "Pending",
                "thread_id": thread_id,
            })

        for src, cnt in db_counts.items():
            if not any(m["filename"] == src for m in merged):
                merged.append({"filename": src, "size_bytes": 0, "chunks_count": cnt, "status": "Ingested (DB only)"})

        return {"documents": merged}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.delete("/documents/{filename}")
async def delete_document_endpoint(filename: str, thread_id: str = None, current_user=Depends(get_current_user)):
    try:
        if thread_id:
            verify_thread_ownership(thread_id, current_user.id)
            storage_path = _storage_path(current_user.id, filename, thread_id)
        else:
            storage_path = _storage_path(current_user.id, filename)

        await _remove_storage_paths([storage_path], auth_token=current_user.token)

        with engine.connect() as conn:
            if thread_id:
                res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'thread_id' = :tid"), {"fn": filename, "tid": thread_id})
            else:
                res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'user_id' = :uid"), {"fn": filename, "uid": str(current_user.id)})
            conn.commit()
            rowcount = res.rowcount

        return {"message": f"Successfully deleted {filename}", "db_chunks_deleted": rowcount}
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.post("/documents/{filename}/reingest")
async def reingest_document(filename: str, thread_id: str = None, current_user=Depends(get_current_user)):
    try:
        if thread_id:
            verify_thread_ownership(thread_id, current_user.id)
            storage_path = _storage_path(current_user.id, filename, thread_id)
        else:
            storage_path = _storage_path(current_user.id, filename)

        tmp_path = await _download_from_storage(storage_path, auth_token=current_user.token)
        if not tmp_path:
            return JSONResponse(status_code=404, content={"message": "Source file not found in storage."})
        renamed = os.path.join(os.path.dirname(tmp_path), filename)
        os.rename(tmp_path, renamed)

        with engine.connect() as conn:
            if thread_id:
                res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'thread_id' = :tid"), {"fn": filename, "tid": thread_id})
            else:
                res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'user_id' = :uid"), {"fn": filename, "uid": str(current_user.id)})
            conn.commit()
            rowcount = res.rowcount

        await asyncio.to_thread(ingest_file, renamed, thread_id, current_user.id)
        os.unlink(renamed)

        return {"message": f"Successfully re-ingested {filename}", "db_chunks_cleared": rowcount}
    except Exception as e:
        logger.error(f"Failed to re-ingest document: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.post("/upload/temporal")
async def upload_temporal_document(thread_id: str, file: UploadFile = File(...), current_user=Depends(get_current_user)):
    try:
        verify_thread_ownership(thread_id, current_user.id)
        raw = await file.read()
        storage_path = _storage_path(current_user.id, file.filename, thread_id)
        await storage_client.upload_file(STORAGE_BUCKET, storage_path, raw, file.content_type, auth_token=current_user.token)

        tmp_path = await _download_from_storage(storage_path, auth_token=current_user.token)
        if not tmp_path:
            return JSONResponse(status_code=500, content={"message": "Failed to retrieve uploaded file for ingestion"})
        renamed = os.path.join(os.path.dirname(tmp_path), file.filename)
        os.rename(tmp_path, renamed)
        await asyncio.to_thread(ingest_file, renamed, thread_id, current_user.id)
        os.unlink(renamed)

        logger.info(f"Temporal upload: {file.filename} for thread: {thread_id}")
        return JSONResponse(status_code=200, content={"message": f"Successfully uploaded and ingested {file.filename} temporally"})
    except Exception as e:
        logger.error(f"Temporal upload failed: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.delete("/chat/{thread_id}/temporal")
async def delete_temporal_chunks_endpoint(thread_id: str, current_user=Depends(get_current_user)):
    try:
        verify_thread_ownership(thread_id, current_user.id)
        prefix = f"{current_user.id}/{thread_id}/"
        objects = await storage_client.list_files(STORAGE_BUCKET, prefix, auth_token=current_user.token)
        paths_to_remove = [f"{prefix}{o['name']}" for o in objects if o.get("name") and not o["name"].endswith("/")]
        if paths_to_remove:
            await _remove_storage_paths(paths_to_remove, auth_token=current_user.token)

        with engine.connect() as conn:
            res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'thread_id' = :tid"), {"tid": thread_id})
            conn.commit()
            rowcount = res.rowcount

        return {"message": f"Cleared temporal chunks for session {thread_id}", "storage_files_deleted": len(paths_to_remove), "db_chunks_deleted": rowcount}
    except Exception as e:
        logger.error(f"Failed to clear temporal chunks: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})
