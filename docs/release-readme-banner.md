# Proposed Banner for `release/v4.0` README

> This file is a **proposal only**. The `release/v4.0` branch is frozen and
> should not be modified automatically. If you choose to add a banner to
> the v4 README, insert the following at the top of `README.md` on the
> `release/v4.0` branch.

---

## Proposed Banner

```markdown
> ⚠️ **This is a frozen historical snapshot of CodexEngine v4.0.**
>
> Active development has moved to the [`agentic`](https://github.com/anmolsharma152/CodexEngine/tree/agentic)
> branch (v5 workspace agent).
>
> The `main` branch contains the current stable v4 release with the latest
> documentation at [README.md](../main/README.md).
>
> **You probably want `main` or `agentic`, not this branch.**
```

---

## Rationale

The banner serves three purposes for anyone who finds the `release/v4.0`
branch:

1. **Disambiguation** — Explains this is a historical snapshot, not the
   current codebase.
2. **Navigation** — Points to `main` (stable) and `agentic` (experimental)
   so visitors know where to go.
3. **Context** — States that development has moved on, setting accurate
   expectations about stale code and docs.
