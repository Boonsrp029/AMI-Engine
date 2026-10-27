"""Synthetic metadata and release gates; no actual model calls or remote traffic."""
import io
import json
from types import SimpleNamespace

import pytest

from src.pilot import _model_identity as model


def install_metadata(monkeypatch, body):
    requests = []
    def open_metadata(url, timeout):
        requests.append((url, timeout))
        return io.BytesIO(body)
    monkeypatch.setattr(model, "build_opener", lambda *handlers: SimpleNamespace(open=open_metadata))
    return requests


def test_metadata_uses_fixed_loopback_and_no_inference(monkeypatch):
    requests = install_metadata(monkeypatch, json.dumps({"models": [{"name": model.MODEL, "digest": "a" * 64}]}).encode())
    snapshot = model.inspect_model()
    assert snapshot == model.expected_snapshot("a" * 64)
    assert requests == [(model.ENDPOINT + "/api/tags", 2)]
    model.verify_model(snapshot)
    assert all(url.endswith("/api/tags") for url, _ in requests)
    install_metadata(monkeypatch, json.dumps({"models": [{"name": model.MODEL, "digest": "b" * 64}]}).encode())
    with pytest.raises(model.ModelIdentityError, match="changed"):
        model.verify_model(snapshot)


@pytest.mark.parametrize("body", [b"not-json", b"[]", b'{"models":{}}', b'{"models":[]}',
    json.dumps({"models": [{"name": model.MODEL, "digest": "not-a-digest"}]}).encode(),
    json.dumps({"models": [{"name": model.MODEL, "digest": "a" * 64}] * 2}).encode(), b"x" * 1_000_001],
    ids=["invalid-json", "array", "models-object", "missing-model", "invalid-digest", "duplicate-model", "oversize"])
def test_metadata_failure_is_sanitized_and_never_repairs_a_digest(monkeypatch, body):
    install_metadata(monkeypatch, body)
    with pytest.raises(model.ModelIdentityError) as error:
        model.inspect_model()
    assert str(error.value) == "Local model content identity unavailable or ambiguous"
    with pytest.raises(model.ModelIdentityError, match="redirects"):
        model._NoRedirect().redirect_request(None, None, None, None, None)


