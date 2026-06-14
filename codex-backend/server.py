import os
import asyncio
import uuid
import json
import shutil
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import jwt
import bcrypt
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

load_dotenv()
DB_URL = os.environ["DB_URL"]
engine = create_engine(DB_URL)


def create_auth_tables():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        )
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS threads (
                id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                timestamp BIGINT NOT NULL,
                pinned BOOLEAN DEFAULT FALSE
            );
        """)
        )
        conn.commit()


create_auth_tables()

# Security Helpers
JWT_SECRET = os.environ.get("JWT_SECRET", "codex-engine-recruiter-jwt-secret-key-928371")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"id": int(user_id), "username": username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def verify_thread_ownership(thread_id: str, user_id: int):
    query = text("SELECT user_id FROM threads WHERE id = :thread_id;")
    with engine.connect() as conn:
        res = conn.execute(query, {"thread_id": thread_id}).fetchone()
        if res and res[0] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this thread",
            )


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
    checkpointer_url = DB_URL.replace("postgresql+psycopg://", "postgresql://")
    async with AsyncPostgresSaver.from_conn_string(checkpointer_url) as checkpointer:
        await checkpointer.setup()
        app.state.agent_engine = create_graph(checkpointer)
        logger.info("LangGraph engine ready, LangSmith tracing active")
        yield


# FastAPI app
app = FastAPI(title="CodexEngine V4 API", lifespan=lifespan)
# CORS
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
class RegisterRequest(BaseModel):
    username: str
    password: str


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
async def register_endpoint(request: RegisterRequest):
    username = request.username.strip()
    password = request.password
    if not username or not password:
        return JSONResponse(status_code=400, content={"message": "Username and password are required"})

    query = text("SELECT id FROM users WHERE username = :username;")
    with engine.connect() as conn:
        res = conn.execute(query, {"username": username}).fetchone()
        if res:
            return JSONResponse(status_code=400, content={"message": "Username already exists"})
        hashed = hash_password(password)
        insert_query = text("INSERT INTO users (username, password_hash) VALUES (:username, :hashed) RETURNING id;")
        res_id = conn.execute(insert_query, {"username": username, "hashed": hashed}).fetchone()
        conn.commit()
        user_id = res_id[0]
    logger.info(f"User registered: {username} (id={user_id})")
    return {"message": "User registered successfully", "user_id": user_id}


@app.post("/login")
async def login_endpoint(request: RegisterRequest):
    username = request.username.strip()
    password = request.password

    query = text("SELECT id, username, password_hash FROM users WHERE username = :username;")
    with engine.connect() as conn:
        res = conn.execute(query, {"username": username}).fetchone()
        if not res:
            return JSONResponse(status_code=401, content={"message": "Invalid username or password"})
        user_id, db_username, password_hash = res[0], res[1], res[2]
        if not verify_password(password, password_hash):
            return JSONResponse(status_code=401, content={"message": "Invalid username or password"})

    token = create_access_token(user_id, db_username)
    logger.info(f"User logged in: {db_username}")
    return {"access_token": token, "token_type": "bearer", "username": db_username}


@app.get("/user/me")
async def get_me_endpoint(current_user=Depends(get_current_user)):
    return current_user


@app.get("/threads")
async def get_threads_endpoint(current_user=Depends(get_current_user)):
    query = text("SELECT id, title, timestamp, pinned FROM threads WHERE user_id = :user_id ORDER BY pinned DESC, timestamp DESC;")
    threads = []
    with engine.connect() as conn:
        res = conn.execute(query, {"user_id": current_user["id"]})
        for r in res:
            threads.append({"id": r[0], "title": r[1], "timestamp": int(r[2]), "pinned": bool(r[3])})
    return {"threads": threads}


@app.post("/threads")
async def save_thread_endpoint(request: SaveThreadRequest, current_user=Depends(get_current_user)):
    select_query = text("SELECT id FROM threads WHERE id = :id AND user_id = :user_id;")
    with engine.connect() as conn:
        existing = conn.execute(select_query, {"id": request.id, "user_id": current_user["id"]}).fetchone()
        if existing:
            update_query = text("UPDATE threads SET title = :title, timestamp = :timestamp, pinned = :pinned WHERE id = :id AND user_id = :user_id;")
            conn.execute(update_query, {"title": request.title, "timestamp": request.timestamp, "pinned": request.pinned, "id": request.id, "user_id": current_user["id"]})
        else:
            insert_query = text("INSERT INTO threads (id, user_id, title, timestamp, pinned) VALUES (:id, :user_id, :title, :timestamp, :pinned);")
            conn.execute(insert_query, {"id": request.id, "user_id": current_user["id"], "title": request.title, "timestamp": request.timestamp, "pinned": request.pinned})
        conn.commit()
    return {"message": "Thread saved successfully"}


@app.delete("/threads/{thread_id}")
async def delete_thread_endpoint(thread_id: str, current_user=Depends(get_current_user)):
    verify_query = text("SELECT id FROM threads WHERE id = :thread_id AND user_id = :user_id;")
    with engine.connect() as conn:
        existing = conn.execute(verify_query, {"thread_id": thread_id, "user_id": current_user["id"]}).fetchone()
        if not existing:
            return JSONResponse(status_code=404, content={"message": "Thread not found"})
        delete_query = text("DELETE FROM threads WHERE id = :thread_id AND user_id = :user_id;")
        conn.execute(delete_query, {"thread_id": thread_id, "user_id": current_user["id"]})
        delete_chunks = text("DELETE FROM prose_chunks WHERE metadata->>'thread_id' = :thread_id;")
        conn.execute(delete_chunks, {"thread_id": thread_id})
        conn.commit()
    return {"message": "Thread deleted successfully"}


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, current_user=Depends(get_current_user)):
    verify_thread_ownership(request.thread_id, current_user["id"])
    config = {"configurable": {"thread_id": request.thread_id, "user_id": current_user["id"]}}

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
        verify_thread_ownership(thread_id, current_user["id"])
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


os.makedirs("data/raw", exist_ok=True)


@app.post("/upload")
async def upload_document(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    try:
        filename = f"user_{current_user['id']}_{file.filename}"
        file_path = f"data/raw/{filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Received file: {filename}")
        await asyncio.to_thread(ingest_file, file_path, None, current_user["id"])
        return JSONResponse(status_code=200, content={"message": f"Successfully uploaded and ingested {file.filename}"})
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.get("/documents")
async def list_documents_endpoint(current_user=Depends(get_current_user)):
    try:
        def _get():
            raw_path = "data/raw"
            files = []
            with engine.connect() as conn:
                res_threads = conn.execute(text("SELECT id FROM threads WHERE user_id = :uid;"), {"uid": current_user["id"]})
                user_threads = {r[0] for r in res_threads}

            def is_valid_uuid(val):
                if not val:
                    return False
                try:
                    uuid.UUID(str(val))
                    return True
                except ValueError:
                    return False

            user_prefix = f"user_{current_user['id']}_"
            if os.path.exists(raw_path):
                for fn in os.listdir(raw_path):
                    if fn.endswith((".pdf", ".txt", ".md", ".csv")):
                        is_owned = False
                        if fn.startswith("user_"):
                            if fn.startswith(user_prefix):
                                is_owned = True
                        elif "_" in fn:
                            parts = fn.split("_", 1)
                            potential_uuid = parts[0]
                            if is_valid_uuid(potential_uuid):
                                if potential_uuid in user_threads:
                                    is_owned = True
                            else:
                                is_owned = True
                        else:
                            is_owned = True
                        if is_owned:
                            fpath = os.path.join(raw_path, fn)
                            size = os.path.getsize(fpath)
                            files.append({"filename": fn, "size_bytes": size, "chunks_count": 0, "status": "Pending"})

            thread_ids_list = list(user_threads) if user_threads else ["dummy-placeholder-uuid"]
            sql = text("""
                SELECT metadata->>'source' as source, metadata->>'thread_id' as thread_id, count(*) as count
                FROM prose_chunks
                WHERE (metadata->>'user_id' IS NULL AND metadata->>'thread_id' IS NULL)
                   OR (metadata->>'user_id' = :user_id_str)
                   OR (metadata->>'thread_id' = ANY(:thread_ids))
                GROUP BY source, thread_id;
            """)
            db_counts = []
            with engine.connect() as conn:
                res = conn.execute(sql, {"user_id_str": str(current_user["id"]), "thread_ids": thread_ids_list})
                for r in res:
                    source, tid, count = r[0], r[1], r[2]
                    if source:
                        db_counts.append({"source": source, "thread_id": tid, "count": count})

            merged = []
            seen_keys = set()
            for f in files:
                fn = f["filename"]
                clean_fn = fn[len(user_prefix):] if fn.startswith(user_prefix) else fn
                prefix = None
                display_name = clean_fn
                if "_" in clean_fn:
                    parts = clean_fn.split("_", 1)
                    if is_valid_uuid(parts[0]):
                        prefix = parts[0]
                        display_name = parts[1]
                count = 0
                status = "Pending"
                for db in db_counts:
                    if db["source"] == display_name and db["thread_id"] == prefix:
                        count = db["count"]
                        status = "Ingested"
                        break
                seen_keys.add((display_name, prefix))
                merged.append({"filename": display_name, "size_bytes": f["size_bytes"], "chunks_count": count, "status": status, "thread_id": prefix})

            for db in db_counts:
                key = (db["source"], db["thread_id"])
                if key not in seen_keys:
                    merged.append({"filename": db["source"], "size_bytes": 0, "chunks_count": db["count"], "status": "Ingested (DB only)", "thread_id": db["thread_id"]})
            return merged

        data = await asyncio.to_thread(_get)
        return {"documents": data}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.delete("/documents/{filename}")
async def delete_document_endpoint(filename: str, thread_id: str = None, current_user=Depends(get_current_user)):
    try:
        if thread_id:
            verify_thread_ownership(thread_id, current_user["id"])

        def _delete():
            disk_deleted = False
            user_prefix = f"user_{current_user['id']}_"
            raw_path = f"data/raw/{user_prefix}{thread_id}_{filename}" if thread_id else f"data/raw/{user_prefix}{filename}"
            if os.path.exists(raw_path):
                os.remove(raw_path)
                disk_deleted = True
            with engine.connect() as conn:
                if thread_id:
                    res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'thread_id' = :tid"), {"fn": filename, "tid": thread_id})
                else:
                    res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'user_id' = :uid"), {"fn": filename, "uid": str(current_user["id"])})
                conn.commit()
                rowcount = res.rowcount
            return disk_deleted, rowcount

        disk_deleted, db_deleted = await asyncio.to_thread(_delete)
        return {"message": f"Successfully deleted {filename}", "disk_deleted": disk_deleted, "db_chunks_deleted": db_deleted}
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.post("/documents/{filename}/reingest")
async def reingest_document(filename: str, thread_id: str = None, current_user=Depends(get_current_user)):
    try:
        if thread_id:
            verify_thread_ownership(thread_id, current_user["id"])

        def _reingest():
            user_prefix = f"user_{current_user['id']}_"
            raw_path = f"data/raw/{user_prefix}{thread_id}_{filename}" if thread_id else f"data/raw/{user_prefix}{filename}"
            if not os.path.exists(raw_path):
                return False, 0
            with engine.connect() as conn:
                if thread_id:
                    res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'thread_id' = :tid"), {"fn": filename, "tid": thread_id})
                else:
                    res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'source' = :fn AND metadata->>'user_id' = :uid"), {"fn": filename, "uid": str(current_user["id"])})
                conn.commit()
                rowcount = res.rowcount
            ingest_file(raw_path, thread_id, current_user["id"])
            return True, rowcount

        success, db_deleted = await asyncio.to_thread(_reingest)
        if not success:
            return JSONResponse(status_code=404, content={"message": "Source file not found on disk."})
        return {"message": f"Successfully re-ingested {filename}", "db_chunks_cleared": db_deleted}
    except Exception as e:
        logger.error(f"Failed to re-ingest document: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.post("/upload/temporal")
async def upload_temporal_document(thread_id: str, file: UploadFile = File(...), current_user=Depends(get_current_user)):
    try:
        verify_thread_ownership(thread_id, current_user["id"])
        os.makedirs("data/raw", exist_ok=True)
        user_prefix = f"user_{current_user['id']}_"
        filename = f"{user_prefix}{thread_id}_{file.filename}"
        file_path = f"data/raw/{filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Temporal file: {filename} for thread: {thread_id}")
        await asyncio.to_thread(ingest_file, file_path, thread_id, current_user["id"])
        return JSONResponse(status_code=200, content={"message": f"Successfully uploaded and ingested {file.filename} temporally"})
    except Exception as e:
        logger.error(f"Temporal upload failed: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.delete("/chat/{thread_id}/temporal")
async def delete_temporal_chunks_endpoint(thread_id: str, current_user=Depends(get_current_user)):
    try:
        verify_thread_ownership(thread_id, current_user["id"])

        def _delete():
            user_prefix = f"user_{current_user['id']}_"
            raw_path = "data/raw"
            disk_deleted_count = 0
            if os.path.exists(raw_path):
                for fn in os.listdir(raw_path):
                    if fn.startswith(f"{user_prefix}{thread_id}_"):
                        os.remove(os.path.join(raw_path, fn))
                        disk_deleted_count += 1
            with engine.connect() as conn:
                res = conn.execute(text("DELETE FROM prose_chunks WHERE metadata->>'thread_id' = :tid"), {"tid": thread_id})
                conn.commit()
                rowcount = res.rowcount
            return disk_deleted_count, rowcount

        disk_deleted, db_deleted = await asyncio.to_thread(_delete)
        return {"message": f"Cleared temporal chunks for session {thread_id}", "disk_files_deleted": disk_deleted, "db_chunks_deleted": db_deleted}
    except Exception as e:
        logger.error(f"Failed to clear temporal chunks: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})
