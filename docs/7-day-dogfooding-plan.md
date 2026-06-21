# 7-Day Dogfooding Plan

> Practical evaluation protocol for the workspace artifact experiment.
> One session per day (~10-15 minutes). Collects evidence on artifact
> production, reuse, project isolation, and search preference.

---

## Setup (Before Day 1)

```bash
# Clean slate
psql $DB_URL -c "DELETE FROM workspace_artifacts WHERE project_id = '';"
psql $DB_URL -c "DELETE FROM tool_invocations;"

# Verify tables exist
psql $DB_URL -c "\d workspace_artifacts"
psql $DB_URL -c "\d tool_invocations"
```

1. Start the server and frontend.
2. Create two projects in the UI: **"project-alpha"** and **"project-beta"**.
3. Smoke test: ask "Write a test artifact saying hello." Then ask "Read test/hello.md."

---

## Day 1 — Project Isolation Baseline

**Goal:** Prove artifacts stay inside their project boundary.

Run these four prompts in order.

### 1.1 — Create in project-alpha

| Field | Value |
|---|---|
| Active project | project-alpha |
| Prompt | "Analyze the `search_documents` function's reranking logic and save the analysis." |
| Expected tool calls | `search_documents` → `write_document(path="analysis/reranking.md")` |
| Expected `project_id` | `"project-alpha"` |

### 1.2 — Create in project-beta

| Field | Value |
|---|---|
| Active project | project-beta |
| Prompt | "Analyze the agent loop's iteration control and save the analysis." |
| Expected tool calls | `search_documents` → `write_document(path="analysis/agent-loop-control.md")` |
| Expected `project_id` | `"project-beta"` |

### 1.3 — List in project-alpha

| Field | Value |
|---|---|
| Active project | project-alpha |
| Prompt | "List saved artifacts." |
| Expected | `list_documents` returns only `analysis/reranking.md` |

### 1.4 — Read across projects

| Field | Value |
|---|---|
| Active project | project-beta |
| Prompt | "Read the analysis of reranking." |
| Expected | `read_document` returns `"Error: no artifact found at..."` |

**Failure signals:**
- 1.3 lists artifacts from project-beta (leak)
- 1.4 finds the project-alpha artifact while in project-beta (cross-project read)
- Any `tool_invocations` row shows `project_id = ""` instead of the active project

**Evidence:**
```sql
SELECT tool_name, arguments::json->>'project_id' AS project_id, duration_ms
FROM tool_invocations ORDER BY created_at;
```

---

## Day 2 — Artifact Production + Same-Session Reuse

**Goal:** Agent writes an artifact then reads it back in the same session.

| | Active project: **project-alpha** |
|---|---|

### 2.1 — Write

| Field | Value |
|---|---|
| Prompt | "Map all the tool functions in `tools.py`, their dependencies, and their data flow. Save the map." |
| Expected | `search_documents` → `write_document(path="analysis/tool-map.md")` |

### 2.2 — Read (same session)

| Field | Value |
|---|---|
| Prompt | "What does `_deduplicate` do and which tools call it?" |
| Expected | `read_document(path="analysis/tool-map.md")` — agent reads its own artifact |
| Failure | Agent calls `search_documents` instead (artifact invisibility) |

**Evidence:**
```sql
SELECT tool_name, arguments::json->>'path' AS path, duration_ms
FROM tool_invocations
WHERE tool_name IN ('read_document', 'search_documents')
ORDER BY created_at;
```

---

## Day 3 — Artifact vs. Search Preference

**Goal:** The most important test. Does the agent prefer its artifact or
re-search when asked a question the artifact can answer?

| | Active project: **project-alpha** |
|---|---|

### 3.1 — Cold question

| Field | Value |
|---|---|
| Prompt | "Explain how the tool registry generates JSON schemas from Python type hints." |
| Expected / acceptable | Agent calls `read_document` on `analysis/tool-map.md` OR `search_documents`. **Note which one wins.** |
| Strong pass | Agent reads the artifact (tool-map.md) without searching. |
| Weak pass | Agent searches first, then reads the artifact. |
| Fail | Agent only searches, never reads. |
| Critical fail | Agent hallucinates an answer that contradicts the artifact content. |

**Do not prime the agent.** Do not say "you already wrote about this."
Ask the question cold. This is the single most important data point of
the week.

**Evidence:**
```sql
SELECT tool_name, arguments, created_at
FROM tool_invocations
WHERE tool_name IN ('read_document', 'search_documents')
ORDER BY created_at;
```

**Judgment call:** If no `read_document` call occurred, that is strong
evidence of artifact invisibility — the hypothesis fails.

---

## Day 4 — Overwrite Awareness + Path Conventions

**Goal:** Agent handles overwriting an existing artifact and uses consistent paths.

| | Active project: **project-alpha** |
|---|---|

### 4.1 — Overwrite

| Field | Value |
|---|---|
| Prompt | "Now expand the tool map to include the web search tool's DDGS integration. Update the existing analysis." |
| Expected | `write_document(path="analysis/tool-map.md")` — same path, content overwritten |
| Failure | Agent writes a new file with a different path instead of overwriting |

### 4.2 — List to verify

| Field | Value |
|---|---|
| Prompt | "List all artifacts in the analysis directory." |
| Expected | `list_documents(pattern="analysis/%")` — returns the artifact (still one entry) |

### 4.3 — Read back

| Field | Value |
|---|---|
| Prompt | "Read the updated tool map." |
| Expected | `read_document` returns the expanded version with DDGS details |
| Failure | Returns old content (stale read) or creates a hallucinated response |

**Evidence:**
```sql
SELECT path, created_at, updated_at FROM workspace_artifacts
WHERE project_id = 'project-alpha';
```

---

## Day 5 — Cross-Session Reuse (24-Hour Gap)

**Goal:** Agent reuses an artifact written on a previous day.

| | Active project: **project-alpha** |
|---|---|

### 5.1 — Cold recall

| Field | Value |
|---|---|
| Prompt | "Remind me how the tool registry generates schemas. I need the details about Optional type handling." |
| Expected | `read_document(path="analysis/tool-map.md")` — reusable artifact written on Day 2, expanded on Day 4 |
| Failure | `search_documents` instead of `read_document` |
| Critical fail | Agent gives a vague or wrong answer that doesn't match the artifact's content |

This is the second most important test. Cross-session reuse is the stated
hypothesis. If the agent doesn't read the artifact, the hypothesis is not
validated.

**Evidence:**
```sql
SELECT tool_name, arguments, created_at
FROM tool_invocations
WHERE tool_name IN ('read_document', 'search_documents')
  AND created_at >= CURRENT_DATE - INTERVAL '5 days'
ORDER BY created_at;
```

---

## Day 6 — Project Switching + Isolation

**Goal:** Verify isolation holds when switching projects.

### 6.1 — Cross-project isolation

| | Active project: **project-beta** |
|---|---|
| Prompt | "What did we find about the tool registry schema generation?" |
| Expected | Agent should NOT find `analysis/tool-map.md` (it is in project-alpha). Agent reports no relevant artifacts. |
| Failure | Agent reads project-alpha's artifact while in project-beta (leak) |

### 6.2 — Switch back to project-alpha

| | Active project: **project-alpha** |
|---|---|
| Prompt | "List all artifacts and summarize what they cover." |
| Expected | `list_documents` returns all project-alpha artifacts; agent summarizes them |

**Evidence:**
```sql
SELECT project_id, COUNT(*) AS count FROM workspace_artifacts GROUP BY project_id;
```

---

## Day 7 — Retrospective + Evidence Compilation

### 7.1 — Agent's self-evaluation (project-alpha)

| | Active project: **project-alpha** |
|---|---|
| Prompt | "List all artifacts I created this week in this project and evaluate whether they were useful." |

### 7.2 — Agent's self-evaluation (project-beta)

| | Active project: **project-beta** |
|---|---|
| Prompt | "List all artifacts I created this week in this project and evaluate whether they were useful." |

### Evidence queries

Run these after both evaluations:

```sql
-- Tool usage summary
SELECT tool_name, COUNT(*) AS calls,
  AVG(duration_ms)::int AS avg_ms,
  COUNT(error) FILTER (WHERE error IS NOT NULL) AS errors
FROM tool_invocations
GROUP BY tool_name ORDER BY tool_name;

-- Artifact inventory
SELECT project_id, path, artifact_type, created_at, updated_at
FROM workspace_artifacts
ORDER BY project_id, path;

-- Reuse detection: artifacts read after a delay (>1 hour after write)
SELECT a.path, a.project_id,
  w.created_at AS written,
  r.created_at AS read_at,
  EXTRACT(EPOCH FROM (r.created_at - w.created_at)) / 3600 AS hours_later
FROM workspace_artifacts a
JOIN tool_invocations w ON w.arguments::json->>'path' = a.path
  AND w.tool_name = 'write_document'
JOIN tool_invocations r ON r.arguments::json->>'path' = a.path
  AND r.tool_name = 'read_document'
  AND r.created_at > w.created_at;

-- Cross-project leak check
SELECT tool_name, arguments, created_at
FROM tool_invocations
WHERE tool_name = 'read_document'
  AND arguments::json->>'project_id' != 'project-alpha'
  AND arguments::json->>'project_id' != 'project-beta';
```

---

## Scoring Summary

| Criterion | How to measure | Minimum to pass |
|---|---|---|
| **Project isolation** | Any cross-project leaks in Days 1 or 6? | 0 leaks |
| **Artifact production** | Count of `write_document` calls | ≥5 total |
| **Same-session reuse** | Day 2.2: agent used `read_document`? | Yes |
| **Cross-session reuse** | Day 5: agent used `read_document`? | Yes |
| **Artifact preference** | Day 3: agent read artifact before or instead of searching? | ≥1 observation |
| **Path convention** | All paths start with `analysis/`? | ≥80% |
| **project_id correctness** | All `arguments::json->>'project_id'` match active project? | 100% |

---

## End-of-Week Questions

Answer these after Day 7:

1. **Did project isolation work?** Any leaks across alpha/beta?

2. **Did the agent reuse artifacts naturally?** Or did prompts have to steer it?

3. **Which won — artifact or search?** On Day 3, did the agent reach for
   `read_document` or `search_documents` first?

4. **Was cross-session reuse real?** Day 5 is the single data point. Did the
   agent remember what it wrote?

5. **Did `project_id` injection work?** Check the `tool_invocations` log —
   all arguments show the right project?

6. **What would you change?** The tools? The prompt? The artifact format?
   The evaluation plan itself?
