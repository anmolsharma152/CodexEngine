# API Reference

Base URL: `http://127.0.0.1:8000` (local) or `https://<your-app>.onrender.com` (production)

## Authentication

Most endpoints require a Bearer JWT token obtained from `/login` or `/register`.

```http
Authorization: Bearer <jwt_token>
```

## Endpoints

### Auth

```
POST /register
Content-Type: application/json

{"email": "user@example.com", "password": "secret123", "username": "alice"}

→ 200 {"message": "User registered successfully", "user_id": "uuid"}
```

```
POST /login
Content-Type: application/json

{"email": "user@example.com", "password": "secret123"}

→ 200 {"access_token": "jwt...", "token_type": "bearer"}
```

```
GET /user/me
Authorization: Bearer <token>

→ 200 {"id": "uuid", "email": "user@example.com", "username": "alice"}
```

### Threads

```
GET /threads
Authorization: Bearer <token>

→ 200 {"threads": [{"id": "...", "title": "...", ...}]}
```

```
POST /threads
Authorization: Bearer <token>
Content-Type: application/json

{"id": "thread-uuid", "title": "My Chat", "timestamp": 1700000000, "pinned": false}

→ 200 {"message": "Thread saved"}
```

```
DELETE /threads/{thread_id}
Authorization: Bearer <token>

→ 200 {"message": "Thread deleted"}
```

### Chat

```
POST /chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{"message": "What is a transformer?", "thread_id": "thread-uuid", "title": "My Chat"}

→ SSE stream:
data: {"type": "status", "content": "Agent routing to router..."}
data: {"type": "token", "content": "A transformer is..."}
data: {"type": "done"}
```

```
GET /chat/{thread_id}/history
Authorization: Bearer <token>

→ 200 {"history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### Documents

```
POST /upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <pdf/txt/csv>

→ 202 {"message": "File uploaded to storage and queued for background ingestion.", "filename": "file.pdf"}
```

```
POST /upload/temporal?thread_id=thread-uuid
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <pdf/txt/csv>

→ 200 {"message": "Successfully uploaded and ingested file.txt temporally"}
```

```
GET /documents
Authorization: Bearer <token>

→ 200 {"documents": [{"filename": "...", "size_bytes": 123, "chunks_count": 5, "status": "Ingested"}]}
```

```
DELETE /documents/{filename}[?thread_id=thread-uuid]
Authorization: Bearer <token>

→ 200 {"message": "Successfully deleted file.pdf", "db_chunks_deleted": 5}
```

```
POST /documents/{filename}/reingest[?thread_id=thread-uuid]
Authorization: Bearer <token>

→ 200 {"message": "File re-ingested successfully", "chunks_count": 5}
```

```
DELETE /chat/{thread_id}/temporal
Authorization: Bearer <token>

→ 200 {"message": "Cleared temporal chunks for session ...", "storage_files_deleted": 1, "db_chunks_deleted": 1}
```

### Health

```
GET /

→ 200 {"status": "ok", "app": "CodexEngine V4", "version": "4.0"}
```
