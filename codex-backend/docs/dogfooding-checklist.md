# Dogfooding Checklist

> Run 2 workflows per day for 5 days (Mon–Fri). Each takes 5–10 minutes.

## Setup

- [ ] Confirm `workspace_artifacts` table exists in your DB
- [ ] Confirm `tool_invocations` table exists in your DB
- [ ] Clean slate: `DELETE FROM workspace_artifacts WHERE project_id = '';`
- [ ] Smoke test: ask agent to `write_document("test/hello.md", "hello")` then `read_document("test/hello.md")`

---

## Quick Reference

This checklist is a quick-reference scorecard. The full day-by-day
protocol with exact prompts is at:

> **[docs/7-day-dogfooding-plan.md](../../docs/7-day-dogfooding-plan.md)**

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
WHERE created_at >= CURRENT_DATE GROUP BY tool_name;
```

---

## Scoring (check when ≥1 session triggers each)

| Criterion | Threshold | Check |
|---|---|---|
| Agent creates an artifact | ≥1 per session | ☐ |
| Agent reads an artifact it wrote earlier (same session) | ≥2 across week | ☐ |
| Agent discovers artifacts via `list_documents` | ≥1 across week | ☐ |
| Cross-session reuse (read written on a prior day) | ≥1 across week | ☐ |
| Agent prefers artifact over search (no re-search) | ≥1 observed | ☐ |
| Artifact content is coherent (useful as standalone output) | ≥80% of artifacts | ☐ |
| Agent follows path convention (`analysis/`, `plans/`, etc.) | ≥70% of artifacts | ☐ |
| project_id is correct on all tool calls | 100% | ☐ |

---

## End-of-Week

- [ ] Run the retrospective prompts from the [7-day plan](../../docs/7-day-dogfooding-plan.md#day-7--retrospective--evidence-compilation)
- [ ] Run the evidence queries from the plan
- [ ] Answer the End-of-Week Questions from the plan
- [ ] Compare agent's self-evaluation against your daily logs
