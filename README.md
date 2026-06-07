# Ecnyss v2 — Autonomous Engineering Lab

Not "an AI that edits itself" — a **sandboxed, multi-agent software organism
governed by Babel-style immutable protocol records.**

> Design rule #1: **Make it maximally auditable first, not maximally autonomous
> first.** Raw autonomy is easy; reliable autonomy is hard. Every change must be
> able to answer: *Why did I do this? What evidence justified it?*

<!-- ECNYSS:STATUS:START -->
## Live Status (updated 2026-06-07T06:44:31+00:00)

- **Cycles:** 18 — merged 5, rejected 11
- **Last cycle:** `8bbb59f87e33` [approved] Created ecnyss/util/trees.py with get_in, set_in, update_in, walk functions and 
- **Last merge:** `8bbb59f87e33` Created ecnyss/util/trees.py with get_in, set_in, update_in, walk functions and 
- **Capability modules (23):** cognition/agent.py, evolution/fitness.py, evolution/merge_gate.py, interfaces/cli.py, interfaces/docs.py, kernel/orchestrator.py, kernel/permission_model.py, kernel/sandbox.py, kernel/self_world.py, memory/entry.py, memory/episodic_store.py, memory/roadmap.py, memory/semantic_index.py, protocol/babel_manifest.py, protocol/canonical.py, protocol/hash_chain.py, protocol/provenance.py, util/collections.py, util/dicts.py, util/test_collections.py, util/test_dicts.py, util/test_trees.py, util/trees.py
<!-- ECNYSS:STATUS:END -->

## Pipeline

```
observe -> model -> propose -> simulate -> verify -> implement -> review -> merge -> learn
```

No single agent both proposes and approves its own evolution.

## Architecture

```
ecnyss/
  kernel/      orchestrator, permission_model, sandbox, rollback
  cognition/   planner, critic, verifier, red_team, maintainer
  memory/      episodic, semantic, strategic (auditable, versioned)
  evolution/   proposal, patch_generator, impact_predictor, merge_gate
  protocol/    babel_manifest, provenance, hash_chain, canonical   <- Babel = law
  interfaces/  cli, github_prs, dashboard
config/        permissions.yaml, objectives.yaml
state/         evolution_chain.jsonl  (append-only audit ledger)
```

## Status — Phase 0 (audit spine)

Implemented and tested:
- **protocol/** — canonical hashing, append-only **hash chain** with tamper
  detection, **provenance** (why + evidence) enforcement, Babel-compatible
  **cycle artifact** emitter.
- **kernel/permission_model** — capability scopes (allow / gated /
  human_required / forbidden), default-deny.
- **orchestrator + CLI** — runs one record-only **dry-run cycle** that emits a
  grounded, pending artifact to the chain.

Not yet built (Phase 1+): sandbox (fork→patch→test→score→PR→merge gate),
cognition agents, memory tiers, impact prediction, GitHub PR interface.

## Use

```bash
python -m ecnyss.interfaces.cli cycle --dry-run --proposal "..." --why "..."
python -m ecnyss.interfaces.cli verify
python -m ecnyss.interfaces.cli log
python -m unittest discover -s tests
```

## Governance invariants (enforced or planned)

- `push_to_main`: **forbidden** — the organism never writes production directly.
- `modify_auth_or_secrets`: **forbidden**.
- `delete_files`: **human_required**.
- Core-logic changes: **gated** through sandbox + merge gate.
- Every cycle emits a hash-chained, grounded audit record before any mutation.
