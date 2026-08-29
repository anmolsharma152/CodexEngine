# CodexEngine — Task Board & Roadmap

> **Tracking Document:** Project Milestones, Sprint Backlog & Verification Status  
> **Last Synchronized:** August 2026

---

## 🚦 Milestone Overview

```text
  [ Phase 1: v4 Production Hardening ]  ──────▶  [ DONE ]
  [ Phase 2: v5 Agentic Synchronization ] ───▶  [ IN PROGRESS ]
  [ Phase 3: v5.1 - v5.3 Ecosystem ]    ─────▶  [ UPCOMING ]
```

---

## 🏁 Phase 1: Production Stability & Multi-Tier Architecture (v4 `main`) `[COMPLETED]`

- [x] **3-Tier Zero-Cost LLM Fallback Engine**:
  - [x] Integrate `langchain-openai>=0.1.0` in `requirements.txt`.
  - [x] Implement cascading `ChatOpenAI` fallback in [`src/llm.py`](file:///home/anmol/Projects/CodexEngine/codex-backend/src/llm.py): Gemini 2.5 Flash $\rightarrow$ Groq GPT-OSS 120B $\rightarrow$ OpenRouter Free.
  - [x] Eliminate Qwen `<think>` token pollution and fix router/evaluator parsing errors.
  - [x] Remove hardcoded `model="llama-3.3-70b-versatile"` in [`src/nodes/actor.py`](file:///home/anmol/Projects/CodexEngine/codex-backend/src/nodes/actor.py).
- [x] **Supabase 7-Day Inactivity Prevention**:
  - [x] Implement lightweight `SELECT 1;` execution inside `GET /` in [`server.py`](file:///home/anmol/Projects/CodexEngine/codex-backend/server.py).
  - [x] Link with external UptimeRobot HTTP 5-minute ping monitor.
- [x] **Complete Visual Brand Identity Overhaul**:
  - [x] Design unified 3D Isometric Knowledge Stack SVG assets (`app/icon.svg`, `public/favicon.svg`, `public/logo.svg`, `public/apple-touch-icon.svg`).
  - [x] Generate multi-resolution binary `favicon.ico` (`16x16`, `32x32`, `48x48`, `64x64`).
  - [x] Build reusable `<CodexLogo />` component in [`CodexLogo.tsx`](file:///home/anmol/Projects/CodexEngine/codex-frontend/app/components/CodexLogo.tsx).
  - [x] Integrate `<CodexLogo />` into the sidebar, context drawer, and login hero section.
- [x] **CI/CD Hardening**:
  - [x] Pass multi-tier API keys down to GitHub Actions in [`.github/workflows/eval.yml`](file:///home/anmol/Projects/CodexEngine/.github/workflows/eval.yml).
  - [x] Verify green test runs for unit tests, DB seeding, golden query test, sweep, and RAGAS eval.

---

## ⚡ Phase 2: v5 Workspace Agent Track (`agentic` branch) `[IN PROGRESS]`

- [ ] **Port 3-Tier LLM Architecture to v5**:
  - [ ] Update [`src/llm/providers.py`](file:///home/anmol/Projects/CodexEngine/codex-backend/src/llm/providers.py) to default to `gemini-2.5-flash` for Gemini and `openai/gpt-oss-120b` for Groq.
  - [ ] Add chained fallback logic to `agent_loop.py` for autonomous tool execution.
- [ ] **Synchronize Branding Assets to `agentic`**:
  - [ ] Copy `CodexLogo.tsx`, SVG icons, and binary `.ico` files into `agentic` frontend.
  - [ ] Add `SELECT 1` async keep-alive to `agentic` `server.py`.
- [ ] **7-Day Live Dogfooding Protocol**:
  - [ ] **Day 1: Project Isolation Validation** — Verify `project_id` scoping prevents cross-project context leaks.
  - [ ] **Day 2: Multi-Turn Deep Retrieval** — Test file synthesis with `read_document` and `list_documents` primitives.
  - [ ] **Day 3: Artifact Canvas Lifecycle** — Validate live Markdown/Code artifact generation and side-by-side editing.
  - [ ] **Day 4: Session State Persistence** — Confirm thread resumption across browser reloads.
  - [ ] **Day 5: Error Recovery & Failover** — Simulate tool timeouts and model failovers mid-loop.
  - [ ] **Day 6: Large Document Batch Ingestion** — Stress-test 50+ page PDF and multi-file text parsing.
  - [ ] **Day 7: Full End-to-End Evaluation** — Run automated RAGAS benchmark on v5 workspace agent.

---

## 🚀 Phase 3: Ecosystem Expansion (`v5.1` – `v5.3`) `[UPCOMING]`

- [ ] **v5.1 — Firecrawl Deep Web & Documentation Ingestion**:
  - [ ] Implement `crawl_website` and `scrape_documentation` tools in `@tool` registry.
  - [ ] Add markdown header-based hierarchical chunking (`#`, `##`, `###`).
- [ ] **v5.2 — Composio Tool Integration**:
  - [ ] Connect external developer tools (GitHub PR creation, Notion doc sync, Slack alerts, Jira issue creation).
  - [ ] Execute actions natively without heavyweight MCP background daemons.
- [ ] **v5.3 — Structured Agent Persistent Memory**:
  - [ ] Implement memory schemas: `memory/decisions.json`, `memory/user_preferences.json`, and entity relationship graphs in PostgreSQL.
  - [ ] Automatic cross-session recall during agent planning phase.

---

## 📊 Verification & QA Commands

```bash
# Backend Unit Tests
python -m unittest codex-backend/tests/test_upload_pipeline.py

# End-to-End Golden Query Evaluation
python codex-backend/tests/test_golden.py

# Frontend Static Production Build
cd codex-frontend && npm run build

# Check Remote CI/CD Run Status
gh run list -L 5
```
