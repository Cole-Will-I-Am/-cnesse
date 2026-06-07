"""Canonical JSON serialization for tamper-evident records.

Byte-exact output so that the same logical object always hashes identically,
independent of key order or platform. Mirrors the Babel v0.2.0 rules:
NFC, lexicographic key sort by code point, deterministic separators, single
trailing LF. This is the foundation every audit hash is computed over.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _normalize(node: Any) -> Any:
    if isinstance(node, dict):
        return {_nfc(str(k)): _normalize(v) for k, v in node.items()}
    if isinstance(node, (list, tuple)):
        return [_normalize(v) for v in node]
    if isinstance(node, str):
        return _nfc(node)
    return node


def canonical_json(obj: Any) -> str:
    """Return canonical JSON text (sorted keys, compact separators, trailing LF)."""
    normalized = _normalize(obj)
    body = json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return body + "\n"


def sha256_hex(obj: Any) -> str:
    """Content hash of the canonical form, prefixed `sha256:`."""
    digest = hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
