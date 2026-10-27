"""Synthetic local identity/permission contracts; no real reviewer decisions."""
import hashlib
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from src.pilot._identity import allowed, authenticate, load_principals
from src.pilot.api import create_app
from src.pilot.engine import Corpus


TOKENS = {role: "synthetic-test-token-only-" + role for role in ("reader", "analyst", "reviewer", "operator")}


@pytest.fixture
def configured(monkeypatch, tmp_path):
    path = tmp_path / "identities.json"
    path.write_text(json.dumps([{"identity": role + "-test", "role": role,
        "token_sha256": hashlib.sha256(token.encode()).hexdigest()} for role, token in TOKENS.items()]), encoding="utf-8")
    monkeypatch.setenv("AMI_PILOT_IDENTITY_FILE", str(path))
    corpus = Corpus("tests/fixtures/release/smoke_corpus.json")
    sid = next(iter(corpus.sources))
    calls = []
    def run(query, event):
        calls.append(query)
        return {"draft": {"title": "Synthetic identity fixture", "claims": [{"text": corpus.sources[sid]["content"],
            "source_ids": [sid]}], "warnings": []}, "sources": corpus.sources, "metrics": {"model_calls": 0}}
    app = create_app(engine=SimpleNamespace(corpus=corpus, run=run), database_path=tmp_path / "pilot.sqlite3", run_inline=True)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        yield app, client, calls, path


def headers(role):
    return {"X-Pilot-Token": TOKENS[role]}


def create(client):
    response = client.post("/api/runs", headers=headers("analyst"), json={"query": "Synthetic identity request", "request_key": "synthetic-identity-key"})
    assert response.status_code == 202
    return response.json()["id"]


def test_configured_home_never_distributes_bootstrap_or_principal_token(configured):
    app, client, _, _ = configured
    html = client.get("/").text
    assert app.state.token not in html
    assert all(token not in html for token in TOKENS.values())
    assert client.get("/api/runs").status_code == 403
    assert client.get("/api/runs", headers={"X-Pilot-Token": app.state.token}).status_code == 403
    assert client.get("/api/runs", headers=headers("reader")).status_code == 200
    assert client.get("/api/session", headers=headers("reviewer")).json() == {
        "identity": "reviewer-test", "role": "reviewer", "mode": "principal-tokens"}


def test_roles_and_exact_authenticated_review_identity(configured):
    app, client, calls, _ = configured
    for role in ("reader", "reviewer"):
        assert client.post("/api/runs", headers=headers(role), json={"query": "blocked", "request_key": "blocked-request"}).status_code == 403
    assert not calls
    rid = create(client)
    payload = {"revision": 1, "decision": "approve", "reviewer": "reviewer-test", "support_confirmed": True}
    assert client.post(f"/api/runs/{rid}/review", headers=headers("analyst"), json=payload).status_code == 403
    forged = {**payload, "reviewer": "somebody-else"}
    assert client.post(f"/api/runs/{rid}/review", headers=headers("reviewer"), json=forged).status_code == 403
    assert app.state.store.get(rid)["status"] == "needs_review"
    assert client.post(f"/api/runs/{rid}/review", headers=headers("reviewer"), json=payload).status_code == 200
    assert client.get(f"/api/runs/{rid}/export", headers=headers("reader")).status_code == 403
    exported = client.get(f"/api/runs/{rid}/export", headers=headers("reviewer"))
    assert exported.status_code == 200
    assert client.get(f"/api/runs/{rid}/export", headers=headers("analyst")).content == exported.content
    row = app.state.store.get(rid)
    serialized = json.dumps(row)
    assert "reviewer-test" in serialized and "somebody-else" not in serialized
    assert all(token not in serialized for token in TOKENS.values())
    attempts = [e["payload"] for e in row["events"] if e["kind"] == "authorized_action_attempt"]
    assert attempts[0] == {"identity": "analyst-test", "role": "analyst", "action": "create"}
    assert {"identity": "reviewer-test", "role": "reviewer", "action": "review"} in attempts


def test_rotation_is_effective_after_explicit_restart_and_logs_no_digests(configured):
    _, _, _, path = configured
    principals = load_principals(path)
    assert authenticate(TOKENS["reader"], principals).identity == "reader-test"
    assert authenticate("wrong", principals) is None
    records = json.loads(path.read_text(encoding="utf-8"))
    records[0]["token_sha256"] = hashlib.sha256(b"replacement-synthetic-token-only").hexdigest()
    path.write_text(json.dumps(records), encoding="utf-8")
    assert authenticate(TOKENS["reader"], load_principals(path)) is None
    assert authenticate(TOKENS["reader"], principals) is not None  # Explicit reload/restart required.


@pytest.mark.parametrize("records", [[], {}, [{"identity": "x", "role": "owner", "token_sha256": "a" * 64}],
    [{"identity": "x", "role": "reader", "token": "plaintext-never-allowed", "token_sha256": "a" * 64}],
    [{"identity": "x", "role": "reader", "token_sha256": "a" * 64}] * 2])
def test_bad_configuration_fails_without_leaking_inputs(tmp_path, records):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(ValueError) as error:
        load_principals(path)
    assert str(error.value) == "Invalid pilot identity configuration; startup refused"
    assert load_principals(None) is None


def test_unknown_actions_are_denied_even_for_operator():
    assert not allowed("operator", "DELETE", "/api/runs/" + "a" * 32)
    assert not allowed("operator", "POST", "/api/approve-all")
    assert allowed("reader", "GET", "/api/runs/" + "a" * 32)


def test_provisioning_never_prints_or_overwrites_credentials(tmp_path, capsys):
    from scripts.provision_pilot_identity import main
    directory = tmp_path / "private"
    assert main(["--output", str(directory), "--principal", "synthetic=reviewer"]) == 0
    token = json.loads((directory / "private-tokens.json").read_text(encoding="utf-8"))["synthetic"]
    config = load_principals(directory / "identities.json")
    assert authenticate(token, config).identity == "synthetic"
    output = capsys.readouterr().out
    assert token not in output and config[0].token_sha256 not in output
    before = (directory / "private-tokens.json").read_bytes()
    with pytest.raises(SystemExit):
        main(["--output", str(directory), "--principal", "synthetic=reviewer"])
    assert (directory / "private-tokens.json").read_bytes() == before


def test_invalid_config_refuses_startup_before_touching_database(monkeypatch, tmp_path):
    monkeypatch.setenv("AMI_PILOT_IDENTITY_FILE", str(tmp_path / "not-present.json"))
    database = tmp_path / "not-created.sqlite3"
    with pytest.raises(ValueError, match="startup refused"):
        create_app(database_path=database)
    assert not database.exists()
