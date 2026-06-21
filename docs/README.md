# Documentation Index

> Repository-wide documentation map. Last updated: June 2026.

---

## Getting Started

| Document                                    | Description                                                                                                   |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| [README.md](../README.md)                   | v5 workspace agent — branch landing page, status, research questions, dogfooding status, relationship to main |
| [AGENTS.md](../AGENTS.md)                   | Agent architecture — current tools, workspace experiment, future research, non-goals                         |
| [docs/github-profile.md](github-profile.md) | Recommended GitHub topics, description, and website URL                                                       |

---

## Research

Documents about future directions. Nothing here is implemented or planned
for the current MVP.

| Document                                                            | Description                                                                                                                                            |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Future Memory Model](../codex-backend/docs/future-memory-model.md) | Research notes for memory/, skills/, decisions/, workspace-state/, and repository-based memory concepts. Marked as future research — do not implement. |

---

## Experiments

Active experiments on the `agentic` branch.

| Document                                                                              | Description                                                                                                                          |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| [Workspace Experiment](../codex-backend/docs/workspace-experiment.md)                 | Hypothesis, entity model, metrics, success criteria, failure modes, and implementation status for the workspace artifact experiment. |
| [Project Isolation Validation](../codex-backend/docs/project-isolation-validation.md) | Five-test validation plan for `project_id` end-to-end correctness.                                                                   |
| [7-Day Dogfooding Plan](7-day-dogfooding-plan.md)                                     | Complete day-by-day evaluation protocol with exact prompts, expected tool calls, failure signals, and evidence collection queries.   |
| [v5 Testing Roadmap](../codex-backend/docs/v5-testing-roadmap.md)                     | Documented test coverage gaps and proposed test ordering for the workspace experiment.                                                |

---

## Validation

Testing and evaluation materials.

| Document                                                                              | Description                                                                        |
| ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| [Dogfooding Checklist](../codex-backend/docs/dogfooding-checklist.md)                 | Quick-reference scoring sheet and daily log template for the workspace experiment. |
| [Project Isolation Validation](../codex-backend/docs/project-isolation-validation.md) | (also listed in Experiments) — 5-test plan that doubles as a validation suite.     |
| [v5 Testing Roadmap](../codex-backend/docs/v5-testing-roadmap.md)                     | (also listed in Experiments) — planning document for automated test coverage gaps.  |

---

## Operations

Deployment and API reference (applies to both v4 and v5).

| Document                          | Description                                             |
| --------------------------------- | ------------------------------------------------------- |
| [Deployment Guide](deployment.md) | Render, Vercel, and Supabase deployment setup.          |
| [API Reference](api.md)           | Full endpoint reference with request/response examples. |
