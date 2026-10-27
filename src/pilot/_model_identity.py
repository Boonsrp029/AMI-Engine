"""Qualification metadata only: pin the local Ollama tag's content digest."""
import json
import re
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener


MODEL = "ami-llama3.1:8b-4k"
ENDPOINT = "http://localhost:11434"


class ModelIdentityError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ModelIdentityError("Local model metadata redirects are forbidden")


def expected_snapshot(digest):
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("A full lowercase SHA-256 model digest is required")
    return {"provider": "ollama", "model": MODEL, "digest": digest, "endpoint": ENDPOINT}


def inspect_model():
    # Fixed loopback endpoint, no proxies/redirects, no credentials or inference.
    try:
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(ENDPOINT + "/api/tags", timeout=2) as response:
            body = response.read(1_000_001)
        if len(body) > 1_000_000:
            raise ValueError()
        data = json.loads(body)
        if not isinstance(data, dict) or not isinstance(data.get("models"), list):
            raise ValueError()
        matches = [m for m in data["models"] if isinstance(m, dict) and m.get("name", m.get("model")) == MODEL]
        if len(matches) != 1:
            raise ValueError()
        return expected_snapshot(matches[0].get("digest"))
    except (OSError, ValueError, TypeError):
        raise ModelIdentityError("Local model content identity unavailable or ambiguous") from None


def verify_model(snapshot):
    if snapshot != expected_snapshot(snapshot.get("digest")):
        raise ModelIdentityError("Invalid pinned model identity")
    if inspect_model() != snapshot:
        raise ModelIdentityError("Local model content changed after qualification pinning")
