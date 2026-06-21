# Workspace Experiment

## Hypothesis

The agent can produce useful persistent artifacts and reuse them as context
in follow-up turns, enabling long-running knowledge work that spans
conversation boundaries.

## Entity Model (MVP)

| Entity | Table | MVP |
|---|---|---|
| **Artifact** | `workspace_artifacts` | ✅ Full support |
| Note | `workspace_artifacts` (type=`note`) | Future |
| Task | separate table | Future |
| Reference | edge table | Future |

## Metrics

| Metric | Definition | Target |
|---|---|---|
| **Artifact creation rate** | `write_document` calls per session | >= 1 per session |
| **Artifact reuse rate** | `read_document` calls per unique artifact | >= 1 revisit |
| **Artifact discovery rate** | `list_documents` calls per session | >= 1 per session |
| **Path diversity** | unique path prefixes per session | >= 2 per session |
| **Reuse latency** | time from write to first read of same artifact | < 10 min |

## Success Criteria

1. Agent produces >= 1 artifact in >= 80% of sessions.
2. Agent reads its own artifact in >= 30% of sessions with prior writes.
3. Agent discovers artifacts via list_documents in >= 20% of sessions.
4. Artifact content is coherent and usable as standalone output.

## Failure Modes

| Mode | Symptom | Mitigation |
|---|---|---|
| **Artifact invisibility** | Agent writes but never reads | Prompt reinforcement: "Check what you already have" |
| **No quality loop** | First write is final write | Implicit via tool_invocations: low reuse = prompt fix |
| **User bypass** | User wants chat answers, not files | Workflow-specific; acceptable for pure Q&A |
| **Path pollution** | Agent creates nonsense paths | Schema-level: keep path simple, use path convention |

## Example Workflow

```
User: "Analyze the auth module in my codebase."

1. agent calls search_documents("auth")  // research
2. agent calls write_document("analysis/auth-module.md", ...)  // produce
3. agent responds: "I wrote analysis/auth-module.md"

User: "What were the key findings about auth?"

4. agent calls read_document("analysis/auth-module.md")  // reuse
5. agent responds based on artifact content

User: "List what I have in analysis/"

6. agent calls list_documents(pattern="analysis/%")  // discover
7. agent responds with list
```

## Implementation

| Component | Code | Status |
|---|---|---|
| Table | `db.py` — `workspace_artifacts` | ✅ Committed |
| Tool: read | `tools.py` — `read_document` | ✅ Committed |
| Tool: write | `tools.py` — `write_document` | ✅ Committed |
| Tool: list | `tools.py` — `list_documents` | ✅ Committed |
| Prompt | `agent_loop.py` — `SYSTEM_PROMPT` | ✅ Committed |
| Logging | `tool_invocations` table + inline in agent_loop | ✅ Committed |
