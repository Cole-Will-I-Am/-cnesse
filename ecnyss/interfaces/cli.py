"""CLI for Ecnyss v2.

    python -m ecnyss.interfaces.cli cycle --dry-run --proposal "..." --why "..."
    python -m ecnyss.interfaces.cli verify       # check the audit chain
    python -m ecnyss.interfaces.cli log          # show recorded cycles
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..kernel.orchestrator import Orchestrator
from ..protocol import HashChain


def _root() -> Path:
    # repo root = three levels up from this file (ecnyss/interfaces/cli.py)
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ecnyss", description="Ecnyss v2 — autonomous engineering lab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cycle", help="run one cycle")
    c.add_argument("--dry-run", action="store_true", help="record-only; no mutation (Phase 0 default)")
    c.add_argument("--proposal", default="No-op observation cycle")
    c.add_argument("--why", default="Phase 0 audit-spine smoke cycle")

    sub.add_parser("verify", help="verify the audit hash chain")
    sub.add_parser("log", help="print recorded cycle artifacts")

    args = parser.parse_args(argv)
    root = _root()

    if args.cmd == "cycle":
        if not args.dry_run:
            print("Phase 0 only supports --dry-run (mutation is gated until Phase 1 sandbox lands).", file=sys.stderr)
            return 2
        result = Orchestrator(root).run_dry_cycle(args.proposal, args.why)
        print(json.dumps(result, indent=2))
        return 0 if result["chain_ok"] else 1

    chain = HashChain(root / "state" / "evolution_chain.jsonl")
    if args.cmd == "verify":
        ok, detail = chain.verify()
        print(detail)
        return 0 if ok else 1

    if args.cmd == "log":
        for line in (chain.path.read_text(encoding="utf-8").splitlines() if chain.path.exists() else []):
            block = json.loads(line)
            p = block["payload"]
            print(f"#{block['index']} {p['cycle_id']} [{p['approval_state']}] {p['proposal']}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
