"""Real-time docs: regenerate CHANGELOG.md and a README status block.

Deterministic and fact-derived (from the audit hash chain + repo), so it runs
outside the gated pipeline — it reports what happened, it doesn't change code.
Called every cycle by the run wrapper after evolve.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

START = "<!-- ECNYSS:STATUS:START -->"
END = "<!-- ECNYSS:STATUS:END -->"


def _payloads(root: Path) -> list[dict[str, Any]]:
    chain = root / "state" / "evolution_chain.jsonl"
    out = []
    if chain.exists():
        for line in chain.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line)["payload"])
    return out


def _modules(root: Path) -> list[str]:
    return sorted(
        str(p.relative_to(root))
        for p in (root / "ecnyss").rglob("*.py")
        if p.name != "__init__.py"
    )


def render_changelog(payloads: list[dict[str, Any]]) -> str:
    lines = ["# Changelog", "",
             "_Auto-generated every cycle from the audit chain. Newest first._", ""]
    for p in reversed(payloads):
        state = p.get("approval_state", "?")
        tag = "merged" if state == "approved" else state
        when = p.get("created_at", "")
        score = p.get("score", {})
        sc = ""
        if isinstance(score, dict) and score:
            sc = " · score " + str(round(sum(score.values()) / len(score), 2))
        prov = (p.get("provenance", {}) or {}).get("why", "")
        lines.append(f"## {when} · `{p.get('cycle_id','')}` · **{tag}**{sc}")
        lines.append(f"- {p.get('proposal','').strip()[:300]}")
        if prov:
            lines.append(f"- _why:_ {prov[:200]}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _bench_line(root: Path) -> str:
    from . import bench
    h = bench.history(root, 6)
    if not h:
        return "- **Benchmark:** (not yet run)"
    last = h[-1]
    delta = ""
    if len(h) >= 2 and h[-2].get("score") is not None:
        d = round(last["score"] - h[-2]["score"], 3)
        delta = f" ({'+' if d >= 0 else ''}{d} vs prev)"
    trend = " → ".join(str(p.get("score")) for p in h)
    return (f"- **Benchmark:** {last['score']} ({last['passed']}/{last['total']}){delta} · "
            f"{last['symbols']} symbols / {last['modules']} modules\n"
            f"- **Benchmark trend:** {trend}")


def render_status(payloads: list[dict[str, Any]], modules: list[str], root: Path | None = None) -> str:
    total = len(payloads)
    approved = sum(1 for p in payloads if p.get("approval_state") == "approved")
    rejected = sum(1 for p in payloads if p.get("approval_state") == "rejected")
    last = payloads[-1] if payloads else {}
    last_merge = next((p for p in reversed(payloads) if p.get("approval_state") == "approved"), {})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = [
        START,
        f"## Live Status (updated {now})",
        "",
        f"- **Cycles:** {total} — merged {approved}, rejected {rejected}",
        f"- **Last cycle:** `{last.get('cycle_id','—')}` [{last.get('approval_state','—')}] {last.get('proposal','')[:80]}",
        f"- **Last merge:** `{last_merge.get('cycle_id','—')}` {last_merge.get('proposal','')[:80]}",
        f"- **Capability modules ({len(modules)}):** " + ", ".join(m.replace('ecnyss/', '') for m in modules),
    ]
    if root is not None:
        rows.append(_bench_line(root))
    rows.append(END)
    return "\n".join(rows)


def _splice_status(readme: str, status: str) -> str:
    if START in readme and END in readme:
        pre = readme.split(START)[0]
        post = readme.split(END, 1)[1]
        return pre + status + post
    # Append a status section if markers are absent.
    return readme.rstrip() + "\n\n" + status + "\n"


def generate(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    payloads = _payloads(root)
    modules = _modules(root)
    (root / "CHANGELOG.md").write_text(render_changelog(payloads), encoding="utf-8")
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "# Ecnyss v2\n"
    readme_path.write_text(_splice_status(readme, render_status(payloads, modules, root)), encoding="utf-8")
    return {"cycles": len(payloads), "modules": len(modules)}


if __name__ == "__main__":
    import sys
    print(generate(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]))
