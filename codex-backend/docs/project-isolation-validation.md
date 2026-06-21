# Project Isolation Validation

> Verify that `project_id` flows correctly end-to-end and that
> artifacts in different projects are isolated.

## Setup

1. Start the server and frontend.
2. Confirm the `workspace_artifacts` table exists.

---

## Test 1: Artifact Creation in Project A

| Step | Action | Expected |
|---|---|---|
| 1 | Set active project to "project-a" in the frontend | — |
| 2 | Ask: "Analyze the search_documents function and save the analysis." | Agent calls `write_document` with `project_id="project-a"` |
| 3 | Check the DB: `SELECT project_id, path FROM workspace_artifacts;` | One row with `project_id = "project-a"` |

---

## Test 2: Artifact Creation in Project B

| Step | Action | Expected |
|---|---|---|
| 1 | Switch active project to "project-b" | — |
| 2 | Ask: "Analyze the agent loop architecture and save the analysis." | Agent calls `write_document` with `project_id="project-b"` |
| 3 | Check the DB: `SELECT project_id, path FROM workspace_artifacts;` | Two rows: one `"project-a"`, one `"project-b"` |

---

## Test 3: `list_documents` Isolation

| Step | Action | Expected |
|---|---|---|
| 1 | With "project-a" active, ask: "List saved artifacts." | Only the project-a artifact appears |
| 2 | Switch to "project-b", ask: "List saved artifacts." | Only the project-b artifact appears |
| 3 | Check the DB directly: `SELECT project_id, path FROM workspace_artifacts ORDER BY project_id;` | Both artifacts exist in the table |

**Failure if:** `list_documents` returns artifacts from both projects regardless of the active project.

---

## Test 4: `read_document` Isolation

| Step | Action | Expected |
|---|---|---|
| 1 | With "project-a" active, ask: "Read the analysis of search_documents." | Success — artifact exists in project-a |
| 2 | With "project-b" active, ask: "Read the analysis of search_documents." | Error — no artifact found at that path in project-b |

**Failure if:** `read_document` returns a project-a artifact while project-b is active (cross-project leak).

---

## Test 5: Cross-Session Reuse Within Same Project

| Step | Action | Expected |
|---|---|---|
| 1 | With "project-a" active, ask: "What did we find about search_documents?" | Agent calls `read_document` on the artifact written in Test 1 |
| 2 | Verify: `SELECT * FROM tool_invocations WHERE tool_name = 'read_document' AND arguments::json->>'project_id' = 'project-a';` | At least one row exists |

**Failure if:** Agent re-searches instead of reading its own artifact, or searches with the wrong `project_id`.

---

## Data Cleanup

After testing, clean up test artifacts:

```sql
DELETE FROM workspace_artifacts WHERE project_id IN ('project-a', 'project-b');
```
