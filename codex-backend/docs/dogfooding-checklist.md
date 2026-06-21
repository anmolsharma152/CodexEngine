# Dogfooding Checklist

> Run 2 workflows per day for 5 days (Mon–Fri). Each takes 5–10 minutes.

## Setup

- [ ] Confirm `workspace_artifacts` table exists in your DB
- [ ] Confirm `tool_invocations` table exists in your DB
- [ ] Smoke test: ask agent to `write_document("test/hello.md", "hello")` then `read_document("test/hello.md")`

---

## Each Workflow

- [ ] Perform the workflow prompt (see 10 workflows in `workspace-experiment.md`)
- [ ] Watch for: artifact is created with a sensible path and useful content
- [ ] If the workflow has a follow-up, do it (same or next day)
- [ ] Watch for: agent retrieves the artifact via `read_document` vs starting from scratch

---

## Daily Log

At end of each day, record:

```
Artifacts created:
Reuse events (read_document on a prior artifact):
Failures observed:
```

Query tool counts:
```sql
SELECT tool_name, COUNT(*) FROM tool_invocations
WHERE created_at >= '2026-06-21' GROUP BY tool_name;
```

---

## Scoring (check when ≥1 workflow triggers each)

| Criterion | Threshold | Check |
|---|---|---|
| Agent creates an artifact unprompted | ≥1 across week | ☐ |
| Agent reads an artifact it wrote earlier | ≥2 across week | ☐ |
| Agent discovers artifacts via `list_documents` | ≥1 across week | ☐ |
| Cross-session reuse (read written on a prior day) | ≥1 across week | ☐ |
| Artifact content is non-trivial (≥5 sentences) | ≥80% of artifacts | ☐ |
| Agent follows path convention (`analysis/`, `plans/`, etc.) | ≥70% of artifacts | ☐ |

---

## End-of-Week

- [ ] Run workflow #10: ask agent to list and evaluate all artifacts
- [ ] Answer the 10 questions from `workspace-experiment.md` → End-of-Week Questions section
- [ ] Compare agent's self-evaluation against your daily logs
