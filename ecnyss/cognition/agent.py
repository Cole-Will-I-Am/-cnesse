"""Agent client — calls a per-agent custom Ollama (cloud) model.

Each agent has its own model, temperature/num_predict (baked into the Modelfile)
and a prompt_char_budget that bounds how much context we send. Thinking models
(e.g. Kimi/architect) get small budgets so reasoning can't blow the window. The
client returns only the response text (the `thinking` field is discarded).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import request, error

import yaml


class Agent:
    def __init__(self, role: str, registry: dict[str, Any], ollama_url: str):
        cfg = registry[role]
        self.role = role
        self.model = cfg["model"]
        self.prompt_char_budget = int(cfg.get("prompt_char_budget", 24000))
        self.num_predict = int(cfg.get("num_predict", 4096))
        self.temperature = float(cfg.get("temperature", 0.3))
        self.timeout_sec = int(cfg.get("timeout_sec", 180))
        self.ollama_url = ollama_url.rstrip("/")

    def run(self, prompt: str) -> str:
        """Send a (budget-clipped) prompt; return response text only."""
        if len(prompt) > self.prompt_char_budget:
            head = int(self.prompt_char_budget * 0.7)
            tail = self.prompt_char_budget - head
            prompt = prompt[:head] + "\n...[context truncated to budget]...\n" + prompt[-tail:]
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.num_predict},
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.ollama_url}/api/generate",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_sec) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return f"__AGENT_ERROR__: {type(exc).__name__}: {exc}"
        resp_text = body.get("response", "")
        return resp_text if isinstance(resp_text, str) else ""


def load_registry(config_path: str | Path) -> tuple[dict[str, Any], str]:
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    return data.get("agents", {}), data.get("ollama_url", "http://127.0.0.1:11434")


def extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first valid JSON object out of model output (handles think/fences)."""
    marker = "...done thinking."
    if marker in text:
        text = text.split(marker, 1)[1]
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    return None
