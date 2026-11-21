"""Metadata/storage readiness without inference or changes to task history."""
import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3
from urllib.request import urlopen


def storage_available(path):
    if not Path(path).is_file():
        return False
    try:
        with closing(sqlite3.connect(path, timeout=1)) as db:
            db.execute("BEGIN IMMEDIATE")
            # Exercise SQLite's write permission without touching any row.
            db.execute("UPDATE runs SET revision=revision WHERE 0")
            db.rollback()
        return True
    except (OSError, sqlite3.Error):
        return False


def model_available():
    provider = os.getenv("AGENT_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
    if provider != "ollama":
        return False
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("AGENT_LLM_MODEL", os.getenv("OLLAMA_MODEL", "ami-llama3.1:8b-4k"))
    expected = model if ":" in model else model + ":latest"
    try:
        with urlopen(base_url + "/api/tags", timeout=2) as response:
            # Refuse an unexpectedly large metadata response; never log its body.
            body = response.read(1_000_001)
        if len(body) > 1_000_000:
            return False
        data = json.loads(body)
        return isinstance(data, dict) and any(
            isinstance(item, dict) and item.get("name", item.get("model")) in {model, expected}
            for item in data.get("models", [])
        )
    except (OSError, ValueError, TypeError):
        return False


def readiness(path):
    checks = {"storage": storage_available(path), "model": model_available()}
    return {"status": "ready" if all(checks.values()) else "not-ready",
            "checks": {name: "ready" if value else "unavailable" for name, value in checks.items()},
            "model_readiness": "metadata-only; inference and policy quality not probed"}
