import hashlib
import io
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.pilot import _readiness as checks
from src.pilot.api import create_app
from src.pilot.engine import Corpus
from src.pilot.store import Store


def test_storage_probe_does_not_change_database_or_create_missing_file(tmp_path):
    path = tmp_path / "state.db"
    assert not checks.storage_available(path) and not path.exists()
    Store(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    assert checks.storage_available(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_model_probe_checks_metadata_without_inference_and_fails_closed(monkeypatch):
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("AGENT_LLM_MODEL", "pilot-model")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")
    calls = []
    def tags(url, timeout):
        calls.append((url, timeout))
        return io.BytesIO(json.dumps({"models": [{"name": "pilot-model:latest"}]}).encode())
    monkeypatch.setattr(checks, "urlopen", tags)
    assert checks.model_available()
    assert calls == [("http://localhost:11434/api/tags", 2)]
    monkeypatch.setattr(checks, "urlopen", lambda *args, **kw: io.BytesIO(b'{"models": []}'))
    assert not checks.model_available()
    monkeypatch.setattr(checks, "urlopen", lambda *args, **kw: io.BytesIO(b'not JSON'))
    assert not checks.model_available()
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "openai")
    monkeypatch.setattr(checks, "urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("No cloud requests")))
    assert not checks.model_available()


def test_readiness_endpoint_reports_model_failure_without_changing_liveness(monkeypatch, tmp_path):
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(json.dumps([{"feed_id": "s", "clean_content": "Synthetic readiness source."}]))
    engine = SimpleNamespace(corpus=Corpus(corpus_path))
    monkeypatch.setattr(checks, "model_available", lambda: False)
    app = create_app(database_path=tmp_path / "state.db", engine=engine)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/health").status_code == 200
        response = client.get("/ready")
        assert response.status_code == 503 and response.json()["checks"]["model"] == "unavailable"
        monkeypatch.setattr(checks, "model_available", lambda: True)
        assert client.get("/ready").status_code == 200
        assert client.get("/api/runs").status_code == 403
