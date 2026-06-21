# v5 Testing Roadmap

## Purpose

The v5 workspace experiment has three layers of evaluation, each serving a different purpose:

- **Manual dogfooding**: A human operator runs scripted prompts, observes agent behavior, and records qualitative observations. Catches what automated tests cannot — does the agent _naturally_ prefer artifacts over search? Does the output _feel_ coherent? Dogfooding validates the hypothesis, not the implementation.
- **Validation checklists**: Structured step-by-step procedures (e.g., project isolation validation) that a human follows to verify a specific mechanism is working. More reproducible than freeform dogfooding but still manual.
- **Automated testing**: Deterministic, repeatable assertions that run in CI. These catch regressions and prove that tools, isolation, and persistence work correctly in isolation. Automated tests do not validate the workspace hypothesis — they validate that the building blocks are sound.

This roadmap identifies what is covered today and what automated test coverage is missing. It is a planning document only — no tests are implemented here.

---

## Existing Validation

### Workspace Experiment

Document: [workspace-experiment.md](workspace-experiment.md)

The workspace experiment defines the hypothesis (the agent can produce and reuse persistent artifacts) and the metrics to evaluate it:
- **Artifact creation rate**: `write_document` calls per session.
- **Artifact reuse rate**: `read_document` calls per unique artifact written earlier.
- **Artifact discovery rate**: `list_documents` calls per session.
- **Artifact vs. search preference**: When the agent could answer from an artifact or from a fresh retrieval, which does it choose?

These are validated through the dogfooding protocol, not automated tests.

### Project Isolation Validation

Document: [project-isolation-validation.md](project-isolation-validation.md)

Five manual tests that verify:
- `project_id` is correctly propagated from `ChatRequest` through `agent_loop` into tool calls.
- `read_document` returns artifacts only from the active project.
- `list_documents` returns artifacts only from the active project.
- Cross-session reads within the same project succeed.
- Cross-project reads are blocked at the database level.

Each test includes exact steps, expected outcomes, failure signals, and cleanup SQL.

### Dogfooding

Documents: [dogfooding-checklist.md](dogfooding-checklist.md), [../../docs/7-day-dogfooding-plan.md](../../docs/7-day-dogfooding-plan.md)

A 7-day manual evaluation protocol. Each day covers a specific aspect of the workspace experiment:
- Days 1–2: Project isolation baseline and same-session artifact reuse.
- Day 3: Artifact vs. search preference (the most important single test).
- Day 4: Overwrite awareness and path conventions.
- Day 5: Cross-session reuse (24-hour gap).
- Day 6: Project switching and cross-project isolation.
- Day 7: Retrospective and evidence compilation.

Each day has exact prompts, expected tool call sequences, failure signals, and SQL queries for evidence.

### Tool Invocation Logging

The `tool_invocations` database table captures every tool call in production:
- **Tool name** and **arguments** (including `project_id`).
- **Result** (truncated to 500 characters) or **error** message.
- **Duration** in milliseconds.
- **Thread ID** and **user ID** for correlation.

This supports evaluation in two ways:
1. **Evidence gathering**: The dogfooding plan includes SQL queries that read from `tool_invocations` to verify tool usage patterns (e.g., was `read_document` called, or only `search_documents`?).
2. **Debugging**: Error logging on tool failures is non-blocking — a failed tool call is logged and the loop continues.

The logging layer is passive instrumentation. It proves what happened but does not assert correctness — that is the role of testing.

---

## Missing Automated Test Coverage

The following areas have no automated tests. All coverage today is manual.

### Workspace Tools

**Coverage needed for `write_document`, `read_document`, `list_documents`:**

| Scenario | What to assert |
|---|---|
| Create artifact | `write_document(path, content)` inserts a row; `read_document(path)` returns the content. |
| Overwrite artifact | `write_document` with an existing path updates content; `updated_at` changes. |
| Read missing artifact | `read_document` with a nonexistent path returns an error string, does not raise. |
| List all artifacts | `list_documents` returns all paths for the active project. |
| List with pattern | `list_documents(pattern="analysis/%")` returns only matching paths. |
| List empty project | `list_documents` on a project with no artifacts returns a "no artifacts" message. |

### Project Isolation

**Coverage needed for `project_id` scoping:**

| Scenario | What to assert |
|---|---|
| Write to project A | Artifact appears only when querying project A. |
| Write to project B | Artifact appears only when querying project B. |
| Read from wrong project | `read_document(path, project_id="B")` returns error for artifact in project A. |
| Default project isolation | Artifacts written with `project_id=""` are invisible from `project_id="default"`. |
| List isolation | `list_documents(project_id="A")` does not return artifacts from project B. |

### Artifact Persistence

**Coverage needed for storage durability:**

| Scenario | What to assert |
|---|---|
| Write then immediate read | Content round-trips correctly. |
| Overwrite with new content | Old content is replaced, not appended. |
| Persistence across connections | New database connection reads the same artifact. |
| Concurrent writes | Two sequential writes to the same path — last write wins. |
| Large content | Artifacts with multi-page content are stored and retrieved without truncation. |

### Agent Loop

**Coverage needed for the execution engine:**

| Scenario | What to assert |
|---|---|
| Tool execution | When the LLM returns a tool call, the agent loop executes the function and appends the result. |
| Tool error handling | When a tool raises an exception, the loop logs it, streams an error event, and continues. |
| Iteration limit | When `MAX_ITERATIONS` is reached, the loop produces a fallback response and exits. |
| `project_id` injection | Workspace tool calls without a `project_id` argument receive the active project ID. |
| Non-workspace tools | `search_documents` and `search_web` are not modified by `project_id` injection. |

### Tool Invocation Logging

**Coverage needed for the logging layer:**

| Scenario | What to assert |
|---|---|
| Success is logged | A row is inserted with `error IS NULL` and `duration_ms > 0`. |
| Failure is logged | A row is inserted with a non-null `error` field. |
| Arguments are captured | The `arguments` JSONB column contains the tool's input parameters. |
| Duration is recorded | `duration_ms` reflects actual wall-clock time. |

---

## Proposed Test Order

Phases are ordered by dependency — each phase builds on the previous one. Within a phase, tests can run in parallel.

### Phase 1 — Workspace Tools

**Goal:** Validate that the three workspace tools (`write_document`, `read_document`, `list_documents`) behave deterministically and correctly in isolation.

**Why first:** Every subsequent test (isolation, reuse, loop integration) depends on these tools working. If artifact storage is broken, nothing else can be validated.

**Success criteria:**
- All create, read, overwrite, and list operations return expected results.
- Missing artifacts return error strings, not exceptions.
- Pattern filtering works correctly.

---

### Phase 2 — Project Isolation

**Goal:** Prevent cross-project leakage of artifacts.

**Why second:** Project isolation depends on Phase 1 tools working correctly. Isolation tests use the same `write`/`read`/`list` operations but across multiple project IDs.

**Success criteria:**
- No artifact is visible outside its own project.
- `project_id` is correctly respected by all three workspace tools.
- Default project (`""`) is isolated from named projects.

---

### Phase 3 — Artifact Reuse

**Goal:** Validate the workspace experiment hypothesis that the agent can read artifacts it created earlier.

**Why third:** Reuse requires correct tool behavior (Phase 1) and project scoping (Phase 2). The reuse tests focus on the agent's ability to write an artifact, then later read it back — either in the same session or across sessions.

**Success criteria:**
- Agent successfully reads an artifact it wrote in the same conversation.
- Agent successfully reads an artifact written in a prior conversation.
- Content round-trips without corruption.

---

### Phase 4 — Agent Loop Integration

**Goal:** Validate that the agent loop correctly orchestrates tool execution, handles errors, and injects `project_id`.

**Why fourth:** Integration tests require all lower-layer tests to pass first. The agent loop is the highest-level component — it depends on correct tool behavior, isolation, and persistence.

**Success criteria:**
- Tool calls from the LLM are dispatched to the correct function.
- Errors are logged and streamed without crashing the loop.
- `project_id` is injected into workspace tools and omitted from non-workspace tools.
- The loop terminates within `MAX_ITERATIONS`.

---

## Success Criteria

Practical, measurable outcomes that define whether the v5 workspace experiment is verifiably correct:

| Criterion | How to measure | Phase |
|---|---|---|
| No cross-project leakage | Project isolation tests: 0 failures | Phase 2 |
| Deterministic artifact reads | Same path + same project always returns same content | Phase 1 |
| Deterministic artifact overwrites | Overwrite test: content changes, path stays same | Phase 1 |
| Tool invocation logs reflect execution | Every tool call in `tool_invocations` matches actual execution | Phase 4 |
| Artifact reuse observed during dogfooding | Day 2, Day 3, Day 5 of dogfooding plan pass | Dogfooding |
| Agent retrieves prior work across sessions | Day 5 of dogfooding plan passes | Dogfooding |
| Loop handles errors gracefully | No crash on tool failure | Phase 4 |
| `project_id` is correct on all tool calls | Phase 2 tests pass | Phase 2 |

---

## Out of Scope

The following are explicitly excluded from this testing roadmap. They are future concerns and not required for validating the current workspace experiment:

- **MCP** — No JSON-RPC tool adapters. Our `@tool` decorator + registry is sufficient for MVP.
- **Subagents** — No `spawn_subagent` tool or child agent lifecycle.
- **Memory systems** — No separate `memory/`, `skills/`, `decisions/` stores.
- **Knowledge graphs** — No entity extraction or graph database.
- **Workflow engines** — No DAG, no pipeline, no state machine.
- **Benchmark leaderboards** — No leaderboard, leaderboard integration, or golden query dashboard.
- **Frontend tests** — Testing the Next.js UI is outside the scope of backend validation.
- **Performance benchmarks** — Throughput, latency percentiles, and scalability are not being measured at this stage.
- **Security audits** — No penetration testing, dependency scanning, or auth hardening.
