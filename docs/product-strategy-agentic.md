# CodexEngine Agentic — Product Strategy, Experiment Finish Plan, UI Redesign

> Working doc for shipping the `agentic` branch as a separate product from `main` (v4 RAG).
> Status: draft decisions. Not implementation.

---

## 1. Plain language: what is this, who cares, why pay?

### Forget the jargon for a minute

**v4 (`main`) answers questions about your PDFs.**
You upload a paper. You ask “what’s the claim on page 12?” It searches chunks and replies with citations. Chat ends; the answer lives only in the thread.

**v5 (`agentic`) is a work desk for long projects that use those PDFs.**
You still ask questions. But the agent is also allowed to **create, list, and update files in a project folder** that survive across chats. Next week you open the same project and it can continue from last week’s analysis instead of starting from zero.

| | v4 Research Engine | v5 Workspace Agent (this branch) |
|---|---|---|
| Core loop | Ask → retrieve → answer | Ask → research → **write/read project files** → answer |
| Memory | Conversation + vector DB of uploads | That **plus** a persistent project workspace |
| Output | Chat message | Chat message **and** durable notes/analyses/plans |
| Feels like | “Chat with my PDFs” | “Junior research analyst with a shared drive” |

### The user problem (in one sentence)

> People who do deep work on documents keep re-explaining context, re-asking the same analysis, and losing intermediate work inside endless chat threads.

### Who this is for (first customers)

Not “everyone with PDFs.” Focus:

1. **Solo researchers / grad students** — many papers, multi-week literature reviews.
2. **Founders / operators** — policies, competitor PDFs, meeting notes → living briefs.
3. **Consultants / freelancers** — client projects with strict separation (Project A must not leak into Project B).
4. **Technical writers / PMs** — source docs → structured drafts that evolve over sessions.

Non-audience (for now): teams needing collab editing, legal e-discovery, enterprise SSO, “ChatGPT with my Drive” at 10k seats.

### What the user does (core use cases)

**Use case A — Research brief that survives sessions**
- Upload 5 papers on topic X.
- “Analyze auth-related claims and save a structured brief.”
- Agent writes `analysis/auth-claims.md`.
- Three days later: “Update the brief with the new paper I uploaded.”
- Agent **reads the brief**, searches the new paper, **overwrites** the brief.

**Use case B — Multi-project isolation**
- Project “Client-Acme” vs “Thesis-Chapter3”.
- Artifacts and chats stay in their project. Switching projects is switching rooms.

**Use case C — Q&A when you still need a quick fact**
- “What does chapter 4 say about X?” → pure search + answer (v4 behavior, still available).
- No need to write a file for every question.

**Use case D — Plan → execute → accumulate**
- “Make a reading plan for these docs” → `plans/reading-order.md`
- “Summarize doc 1 per the plan” → `summary/doc1.md`
- “What’s left on the plan?” → reads plan + lists summaries.

### User benefit (why not just ChatGPT / Claude + PDFs?)

| Benefit | Why it matters |
|---|---|
| **Work compounds** | Analysis becomes files you can open, edit, version, re-use — not buried in chat scrollback. |
| **Your corpus stays yours** | Uploaded sources + generated workspace, scoped per account/project. Self-host path exists. |
| **Project walls** | Client/thesis separation without “remember not to mix these.” |
| **Tool visibility** | You can see “searched → wrote file → listed files” instead of a black-box monologue. |
| **Citations from sources** | Answers still grounded in your PDFs when research tools are used. |

ChatGPT Projects / Claude Projects are the market comps. Differentiation for a small product:

- Self-host / own data path
- Explicit **artifact filesystem** (path-based workspace you can inspect)
- Hybrid search over **your** uploads + agent-written docs in one project
- Open enough to productize under your brand without being “another ChatGPT wrapper”

### Business plan (honest, stage-appropriate)

**Stage 0 — Validate (now, free)**  
Ship dogfood-quality product to yourself + 5–10 people who already live in PDFs. Success = they create and **re-open** artifacts without you prompting them to.

**Stage 1 — Soft product (separate deploy from `main`)**  
- Brand: **not** “CodexEngine v5 experimental” — something like **Codex Desk / Codex Workspace / Desk** (name TBD).
- Deploy: separate Render service + Vercel project + optional separate Supabase project (cleanest isolation from v4).
- Pricing hypothesis (pick one after validation):
  - **Hobby free + paid “Pro”** for higher rate limits / larger storage / better models
  - Or **self-host open core** + paid hosted
- Do **not** compete on “best general chatbot.” Compete on **persistent document work for individuals**.

**Stage 2 — Monetizable wedge**  
Only if Stage 0 metrics hold:

| Metric | Target before charging strangers |
|---|---|
| Weekly active who write ≥1 artifact | ≥40% of actives |
| Sessions that read a prior artifact | ≥25% |
| “Would be annoyed if this went away” (qual) | ≥ half of dogfood users |
| Cross-project leaks | 0 |

**What you sell**
- Hosted workspace with uploads + agent + projects
- Optional: private deploy for freelancers/small labs
- Later (not now): team workspaces, connectors (Drive/Notion), export packs

**What you do not sell yet**
- Enterprise SSO, compliance packs, multi-tenant admin, agent marketplaces, MCP app store

**Positioning one-liner**

> Your private research desk: upload sources, work with an agent that leaves files behind — not just chat replies.

**Relationship to `main`**

| Branch | Product | Deploy |
|---|---|---|
| `main` | CodexEngine Research (v4 RAG Q&A) | Keep as-is (existing users) |
| `agentic` | New workspace product | **Separate** domain + stack until proven |

Do not merge over `main` until the workspace product has users or you deliberately sunset v4. Parallel products is fine for a long time.

---

## 2. Finish-the-experiment checklist (ordered by leverage)

Goal: get a yes/no on the workspace hypothesis with minimal new architecture.

### P0 — Make continuity real (without this, dogfooding lies)

| # | Task | Touchpoints | Done when |
|---|---|---|---|
| P0.1 | Load last N chat messages into `agent_loop` | `server.py` `/chat/stream` → fetch `chat_messages`; pass `messages=` to `agent_loop` | Same-thread follow-ups use prior turns |
| P0.2 | Inject `user_id` (and optionally `thread_id`) into `search_documents` like `project_id` for workspace tools | `agent_loop.py` `_WORKSPACE_TOOLS` pattern → add research-tool injection | LLM cannot “forget” user scope |
| P0.3 | On each turn (or session start), give agent a short workspace inventory | Either soft inject `list_documents` result into system context, or prompt: “call list_documents before writing if unsure” | Day 3 cold questions have a path to discovery |
| P0.4 | Persist tool events to the client message model | `useChat.ts` handle `tool_call` / `tool_result`; extend `Message` type | UI can show activity; debugging dogfood is possible |

**Code sketch (P0.1)**

```text
server.py chat_stream_endpoint:
  history = SELECT role, content FROM chat_messages WHERE thread ...
  # exclude the user message you just saved, or include and don't double-append
  async for event in agent_loop(..., messages=history[:-1] or history, project_id=...)

agent_loop.py:
  already supports messages: list | None — wire it
```

**Decision:** Start with last **20** user/assistant turns (no tool dumps in DB yet). Tool trajectory in DB is P1 if reuse still fails.

### P1 — Prove building blocks (automated)

| # | Task | Touchpoints | Done when |
|---|---|---|---|
| P1.1 | Phase 1 tests: write/read/overwrite/list/missing | `tests/test_workspace_tools.py` against real or test Postgres | CI green |
| P1.2 | Phase 2 tests: project isolation | `tests/test_project_isolation.py` | 0 cross-project reads |
| P1.3 | Delete or rewrite LangGraph tests | `test_golden.py`, `test_rigorous.py` | No import of dead `create_graph` |
| P1.4 | Agent loop unit tests with mock LLM | `tests/test_agent_loop.py` | Injection + max iterations + tool error path covered |

### P2 — Run the science (manual, 3 days minimum)

| Day | Focus | Ship gate |
|---|---|---|
| 1 | Isolation alpha/beta | Fail if any leak |
| 2 | Write then same-session read | Fail if never calls `read_document` even when asked to use saved work |
| 3 | Cold preference: artifact vs search | **Decision day** — record which tool wins |

Fill `codex-backend/docs/dogfooding-checklist.md` with real checkmarks. No results → no more features.

### P3 — Product surface for the experiment (UI)

See §4. Minimum for dogfood users who are not you:

- Workspace file tree visible without asking the agent
- Chat shows tool steps
- Projects feel first-class
- Upload sources vs agent notes are distinct

### P4 — Ship separately

| # | Task |
|---|---|
| P4.1 | New product name + landing copy (workspace desk, not “RAG research engine”) |
| P4.2 | Separate env: `agentic` deploy, own domain (e.g. `desk.example.com`) |
| P4.3 | Schema migrate `workspace_artifacts` / `tool_invocations` / `chat_messages` on that DB |
| P4.4 | Rate limits + upload caps sized for free tier |
| P4.5 | Privacy/terms one-pager; no claim of “enterprise ready” |

### Explicitly do **not** do before P2 results

- Memory/skills/decisions path hierarchy
- MCP / subagents / workflow engine
- Knowledge graph
- Team collab
- Rebuilding the whole frontend design system for aesthetics alone

---

## 3. Risk deep-dives

### 3.1 History reload design

**Problem**  
Today: messages are saved to `chat_messages`, but `/chat/stream` does not pass history into `agent_loop`. Every backend turn is cold. Frontend *displays* history when you select a thread; the model does not see it on the next send.

**Why it breaks the product story**  
“Persistent workspace” without conversational continuity means the only memory is files. That can work, but only if the agent **discovers** files every time. Small models often don’t.

**Recommended design (minimal)**

```
┌─────────────┐     load last N      ┌─────────────┐
│ chat_messages│ ──────────────────► │ agent_loop  │
└─────────────┘   user/assistant     │ + tools     │
                                      └──────┬──────┘
┌─────────────┐   optional inject           │
│ list paths  │ ────────────────────────────┘
│ for project │   (system or first tool)
└─────────────┘
```

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Pass last N text turns only | Simple; matches current table | No prior tool results | **Do first** |
| B. Also store tool_calls JSON in `chat_messages` or side table | Full trajectory for model | Token bloat; schema change | Later if A fails Day 3 |
| C. Summarize old turns into `memory/session.md` | Bounded context | Depends on write_document working | Only after hypothesis holds |
| D. Rely only on artifacts, no chat history | Pure experiment | Harsh UX; fails product bar | Reject for shipping |

**Implementation notes**

1. After `save_message(user)`, load history **including** that user message, then either:
   - pass `messages=history` and **do not** append user_message again in the loop, or
   - pass `messages=history[:-1]` and keep current append.
2. Cap: `MAX_HISTORY_MESSAGES = 20` (10 turns). Truncate oldest first.
3. Never put secrets/system prompt from client over server system prompt without review — client `system_prompt` already exists; keep server `SYSTEM_PROMPT` as base and append inventory.
4. Thread switch: frontend already loads history for display; backend must independently load so API clients work.

**Token budget rough math**  
20 turns × ~300 tokens ≈ 6k tokens + system + tools. Fine for Groq 8B/70B class.

### 3.2 Search scoping

**Problem**  
Workspace tools are forced to `project_id`. `search_documents` filters by `user_id` / `thread_id` in SQL, but the loop does **not** inject those args. The model may omit them → query falls through to global-ish rows (`metadata user_id/thread_id IS NULL` OR match).

**Risk levels**

| Risk | Severity |
|---|---|
| Missing injection → wrong or empty retrieval | High for product quality |
| Cross-user leak if RLS/metadata wrong | Critical if present |
| Uploads not tied to `project_id` at all | High for multi-project users (all projects share one corpus) |

**Recommended design (phased)**

**Phase A (immediate safety + quality)**  
In `agent_loop`, after parsing tool args:

```python
if tc.name == "search_documents":
    args["user_id"] = user_id
    # thread_id: prefer "" for project-global search, or pass thread only for session files
    args.pop("thread_id", None)  # or set deliberately
    args["user_id"] = user_id
```

Strip LLM-supplied `user_id` always (trust boundary). Same pattern as `project_id`.

**Phase B (project-aligned corpus — needed for real multi-project product)**  
- Tag chunks with `project_id` on ingest (or map documents → project).
- `search_documents` WHERE `metadata->>'project_id' = :project_id` (and user).
- Upload API accepts `project_id`.
- Until then: document in UI that “sources are account-global; notes are per-project.”

**Phase C (optional)**  
Search over `workspace_artifacts` content too (or embed artifacts). Helps “prefer artifact” without the model knowing paths. Strong upgrade after dogfood.

**Decision for ship-separate product**  
Ship with Phase A + honest UX about global sources. Schedule Phase B before charging multi-project users.

### 3.3 Phase 1 automated tests (workspace tools)

**Why first**  
Dogfooding cannot distinguish “agent is dumb” from “write silently failed / wrong project_id / list broken.”

**Minimal suite (implement before more UI)**

```text
tests/test_workspace_tools.py
  test_write_then_read_roundtrip
  test_overwrite_updates_content
  test_read_missing_returns_error_string
  test_list_all
  test_list_pattern
  test_list_empty_project

tests/test_project_isolation.py
  test_write_a_invisible_in_b
  test_list_a_excludes_b
  test_read_wrong_project_errors
```

**Fixtures**  
- Pytest + asyncpg/SQLAlchemy against local Postgres or Testcontainers.
- Or sqlite is **wrong** — use the same JSON/UNIQUE semantics as prod; prefer real Postgres in CI service.

**Agent loop tests (mock provider)**  
- Fake LLM returns tool_call then content.
- Assert `project_id` injected.
- Assert exception in tool → error event + continue.
- Assert iteration cap yields fallback.

**Kill list**  
- `test_golden.py` / `test_rigorous.py` LangGraph imports: delete or quarantine behind `pytest.mark.skip` with reason, then replace with v5 eval later.

---

## 4. UI redesign for the workspace product

### 4.1 What’s wrong with the current UI for this use case

The UI is still a **chat-first RAG app**:

| Current | Problem for v5 |
|---|---|
| Sidebar = threads + project dropdown | Projects secondary; workspace invisible |
| Doc manager = modal of **uploads only** | Agent-written artifacts have **no home** in the UI |
| Chat center stage | Files are first-class work product but hidden |
| CognitionPanel (v4 intent/eval) | Dead concept post-LangGraph; confuses the story |
| Quick prompts = Python/SQL/Big-O | Train users for chatbot, not desk work |
| Landing: “Research Engine / Hybrid Search” | Markets v4, not the workspace bet |
| Tool SSE partially handled | Users don’t see write/read as the product moment |

### 4.2 Design principle

> **Chat is the agent’s hands. The workspace is the product.**

Layout should look closer to **Cursor / Notion AI / Claude Projects** than to ChatGPT-only:

```
┌──────────────┬────────────────────────────┬──────────────────────────┐
│  PROJECT     │  MAIN (tabbed)             │  CONTEXT (optional)      │
│              │                            │                          │
│  Projects    │  [Chat] [Workspace] [Sources] │  Active file preview   │
│  ─────────   │                            │  or citation drawer      │
│  Workspace   │  Chat: messages + tool     │                          │
│  tree        │  steps                     │                          │
│   analysis/  │                            │                          │
│   plans/     │  Workspace: file tree +    │                          │
│   summary/   │  markdown preview/edit     │                          │
│              │                            │                          │
│  Chats       │  Sources: uploads + status │                          │
│  (this proj) │                            │                          │
│              │                            │                          │
│  [Upload]    │  ───────────────────────── │                          │
│  [Settings]  │  Composer (always or chat) │                          │
└──────────────┴────────────────────────────┴──────────────────────────┘
```

Mobile: bottom tabs **Chat | Files | Sources**; project switcher in header.

### 4.3 Information architecture

**Three document kinds (user-facing names)**

| Kind | Storage today | UI name | Actions |
|---|---|---|---|
| Sources | Supabase storage + `prose_chunks` | **Sources** | Upload, reingest, delete, “ask about this” |
| Notes / artifacts | `workspace_artifacts` | **Workspace** | Open, copy path, ask agent to update, download .md |
| Chats | `chat_messages` + threads | **Chats** | New, pin, rename, scoped to project |

Never call agent files “documents” next to PDFs without a qualifier — users will think uploads and notes are the same thing.

### 4.4 Component redesign (concrete)

| Component | Change |
|---|---|
| **LandingPage** | Headline: “A private desk for document-heavy work.” Features: persistent notes, project isolation, cited research. Drop “parametric engine” language. |
| **Sidebar** | Top: **Project switcher** (large). Then **Workspace** tree (from new API). Then **Chats** for project. Collapse uploads into Sources entry. |
| **DocManager** | Split into **Sources panel** (uploads) — not a single “Knowledge Base” modal that pretends to be everything. |
| **New: WorkspacePanel** | File tree by path prefix; click → preview markdown; “Insert path into chat”; refresh after agent writes. |
| **New: ToolTimeline** | Inline under assistant message: chips `search_documents` → `write_document analysis/…`. Replace CognitionPanel. |
| **MessageBubble** | Support `toolSteps[]`; keep citations for sources. |
| **EmptyState / QuickPrompts** | Workspace-native prompts only (see below). |
| **InputBar** | Placeholder: “Ask, or tell the agent what to write into the workspace…”; optional attach source. |
| **ProjectSelector** | Treat as workspace root, not a filter chip. Creating a project = empty workspace + empty chat list. |
| **Settings** | Model/provider; default path conventions; less “system prompt for power users” in v1 marketing. |
| **Onboarding** | 3 steps: Create project → Upload a source → “Summarize and save to workspace.” Celebrate the file appearing in the tree. |

### 4.5 Workspace-native quick prompts (replace current set)

1. “Summarize the uploaded sources and save to `summary/overview.md`.”
2. “Compare the main claims across my sources; write `analysis/comparison.md`.”
3. “List what’s already in this workspace, then propose a reading plan in `plans/next.md`.”
4. “Update `analysis/…` with anything new in the latest upload.”
5. “Answer from the workspace first; only search sources if needed.”

### 4.6 API additions the UI needs

| Endpoint | Purpose |
|---|---|
| `GET /workspace?project_id=` | List artifacts (path, type, updated_at) — **don’t force chat to list** |
| `GET /workspace/content?project_id=&path=` | Read artifact for preview |
| `PUT /workspace` (optional v1.1) | User edits note manually |
| `DELETE /workspace?path=` | User deletes junk paths |
| Existing tools stay for the agent | UI uses REST; agent uses tools |

Without REST list/read, the workspace panel cannot exist; the product remains chat-gated.

### 4.7 Visual / UX tone for a shippable product

- Less “cyber mono terminal / cognition panel,” more **calm productivity** (Notion-dark or Linear-dark is fine).
- Tool activity should feel like **progress**, not debug logs (collapsed by default, expand for detail).
- When agent writes a file: toast **“Saved analysis/foo.md”** + tree highlight + optional open preview.
- Empty workspace illustration: folder with “Nothing saved yet — ask the agent to write its first note.”

### 4.8 Phased UI delivery

| Phase | Scope | Depends on |
|---|---|---|
| **UI-0** | Tool timeline in chat + toast on `write_document` + kill CognitionPanel usage | P0.4 SSE |
| **UI-1** | Workspace panel (list/read APIs) + Sources renamed split | REST endpoints |
| **UI-2** | Three-zone layout + new empty/onboarding/landing | UI-1 |
| **UI-3** | Manual edit/delete in workspace; path breadcrumbs; export zip | After dogfood |

**Ship separate product at UI-1 + P0 + P2 Day1–3 pass.** UI-2 is polish for public launch.

### 4.9 Wireframe (primary desktop)

```
┌─ Acme Research ▾ ─────────────────────────────── [Upload] [⚙] ─┐
│ Sources (3)   Workspace          Chats                          │
│  paper1.pdf   📁 analysis/        ● Brief v2                    │
│  paper2.pdf     auth.md     ←     ○ Sources QA                  │
│  notes.csv      claims.md         ○ (new chat)                  │
│               📁 plans/                                         │
│                 week1.md                                        │
│               📁 summary/                                       │
├─────────────────────────────────────────────────────────────────┤
│ Chat · Brief v2                                                 │
│                                                                 │
│ You: Update the auth analysis with paper2.                      │
│                                                                 │
│ Agent:                                                          │
│  [search_documents] [read_document analysis/auth.md]            │
│  [write_document analysis/auth.md]                              │
│  Updated analysis/auth.md — three new claims from paper2…       │
│  [Open file]                                                    │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Ask to research, write, or update workspace files…          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Recommended decisions (executive)

1. **Product thesis:** Persistent project workspace for document-heavy solo work — not “better RAG chat.”
2. **Brand/deploy:** Separate name + deploy from `main`; keep v4 alive for existing RAG users.
3. **Next engineering order:** P0 history + injection → P1 tests → P2 dogfood Days 1–3 → UI-0/UI-1 → separate deploy.
4. **Kill/defer:** CognitionPanel, generic coding quick prompts, memory/skills paths, MCP, merge to main.
5. **Pricing:** Free dogfood → paid hosted only after reuse metrics; self-host as credibility, not day-1 revenue.
6. **Honest limitation to tell users until Phase B search:** Sources are per-account; workspace notes are per-project.

---

## 6. One-page roadmap

```
Week 1  P0 continuity + search user injection + delete dead tests
        UI-0 tool timeline + write toasts
Week 2  P1 workspace/isolation tests
        GET /workspace (+ content)
        UI-1 workspace panel
Week 3  Dogfood Days 1–3 (record results)
        Landing + onboarding copy for desk product
Week 4  If metrics OK: separate deploy + name
        If Day 3 fails: bootstrap list_documents + stronger prompt; retest once
        If still fails: pivot UI to “manual notes + agent assist” (user creates files; agent fills)
```

---

## 7. Success definition for “we can sell this”

A stranger can:

1. Create a project  
2. Upload 2 PDFs  
3. Get a saved analysis file they can open in the sidebar  
4. Come back next day, open the file, ask a follow-up, see the file update  
5. Switch project and **not** see the first project’s notes  

If step 4 fails systematically, do not market “workspace agent.” Market “chat with docs + optional export” or fix continuity first.
