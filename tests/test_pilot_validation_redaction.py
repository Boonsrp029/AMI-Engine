"""Rejected synthetic values must not be reflected; no inference or real PII."""
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from src.pilot.api import create_app
from src.pilot.engine import Corpus
from src.pilot._validation_errors import public_validation_details

PRIVATE = "synthetic-private-person@example.invalid"


@pytest.fixture
def client(tmp_path):
    # No run method: an invalid request reaching generation fails this fixture.
    engine = SimpleNamespace(corpus=Corpus("tests/fixtures/release/smoke_corpus.json"))
    app = create_app(database_path=tmp_path / "synthetic.sqlite3", engine=engine, run_inline=True)
    with TestClient(app, base_url="http://localhost") as browser:
        browser.headers["x-pilot-token"] = app.state.token
        yield browser, app


@pytest.mark.parametrize("query", [PRIVATE, "Synthetic account 1234567890123"])
def test_rejected_personal_material_not_reflected_or_stored(client, query):
    browser, app = client
    response = browser.post("/api/runs", json={"query": query, "request_key": "redaction-test"})
    assert response.status_code == 422
    assert query not in response.text
    assert response.json()["detail"] == [{"type": "value_error", "loc": ["body", "query"],
        "msg": "Enter a public research question without personal contact or identity information"}]
    assert app.state.store.list() == []


def test_extra_keys_and_bad_request_key_not_reflected(client):
    browser, app = client
    response = browser.post("/api/runs", json={"query": "Synthetic research question",
        "request_key": PRIVATE, PRIVATE: "synthetic-private-value"})
    assert response.status_code == 422
    assert PRIVATE not in response.text and "synthetic-private-value" not in response.text
    assert {e["type"] for e in response.json()["detail"]} == {"string_pattern_mismatch", "extra_forbidden"}
    assert any(e["loc"] == ["body", "field"] for e in response.json()["detail"])
    assert app.state.store.list() == []


def test_malformed_json_context_and_body_not_reflected(client):
    browser, _ = client
    response = browser.post("/api/runs", content='{"query": "'+PRIVATE+'",',
        headers={"content-type": "application/json"})
    assert response.status_code == 422 and PRIVATE not in response.text
    assert response.json()["detail"][0]["type"] == "json_invalid"
    assert all(set(e) == {"type", "loc", "msg"} for e in response.json()["detail"])


def test_nested_errors_keep_public_field_and_index_not_private_values(client):
    browser, _ = client
    response = browser.put("/api/runs/synthetic-run/draft", json={"revision": PRIVATE,
        "draft": {"title": "Synthetic", "claims": [{"text": "Synthetic", "source_ids": [], PRIVATE: PRIVATE}], "warnings": []}})
    assert response.status_code == 422 and PRIVATE not in response.text
    locations = [e["loc"] for e in response.json()["detail"]]
    assert ["body", "draft", "claims", 0, "source_ids"] in locations
    assert ["body", "draft", "claims", 0, "field"] in locations


def test_missing_field_error_and_authentication_boundary_retained(client):
    browser, _ = client
    response = browser.post("/api/runs", json={})
    assert response.status_code == 422
    assert {tuple(e["loc"]) for e in response.json()["detail"]} == {("body", "query"), ("body", "request_key")}
    response = browser.post("/api/runs", json={"query": PRIVATE}, headers={"x-pilot-token": "invalid-synthetic-token"})
    assert response.status_code == 403 and PRIVATE not in response.text


def test_error_context_message_type_and_unknown_location_are_not_reflected():
    errors = [{"type": PRIVATE, "loc": ("body", "draft", "claims", 0, PRIVATE),
        "msg": PRIVATE, "ctx": {"error": RuntimeError(PRIVATE)}, "input": PRIVATE}]
    detail = public_validation_details(errors)
    assert PRIVATE not in json.dumps(detail)
    assert detail == [{"type": "value_error", "loc": ["body", "draft", "claims", 0, "field"], "msg": "Invalid field value"}]


def test_validation_formatter_does_not_stringify_supplied_objects():
    class Hostile:
        def __str__(self):raise AssertionError("Private input stringified")
        def __repr__(self):raise AssertionError("Private input represented")
    assert public_validation_details([{"type": Hostile(), "loc": ("body", Hostile()),
        "input": Hostile(), "ctx": Hostile(), "msg": Hostile()}]) == [
        {"type": "value_error", "loc": ["body", "field"], "msg": "Invalid field value"}]
