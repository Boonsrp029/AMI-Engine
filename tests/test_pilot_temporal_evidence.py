"""Necessary dated-price evidence checks, not a general temporal-reasoning guarantee."""
import json
from datetime import date
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from src.pilot._evidence import NO_INFORMATION, build_span_catalog
from src.pilot._temporal import price_observation_catalog
from src.pilot.engine import Corpus, PilotEngine
from src.pilot.schemas import ResearchRequest, ReviewRequest
from src.pilot.store import Conflict, Store


QUESTION = "What were Thailand's exact retail electricity prices yesterday?"


@pytest.mark.parametrize("text,accepted", [
    ("Retail electricity prices were 4 units on 2026-10-25.", True),
    ("Retail electricity tariffs were 4 units on 25 October 2026.", True),
    ("Retail electricity prices were 4 units on October 25, 2026.", True),
    ("Retail electricity prices in August 2026 were 4 units.", False),
    ("Food prices on 2026-10-25 were 4 units.", False),
    ("Retail electricity prices are projected for 2026-10-25 at 4 units.", False),
])
def test_date_and_measure_must_occur_in_source_text_not_only_metadata(text, accepted):
    catalog = build_span_catalog({"a": {"content": text, "published": "2026-10-26"}})
    selected, trace = price_observation_catalog(QUESTION, "2026-10-26", catalog)
    assert bool(selected) is accepted and trace["requested_dates"] == {"yesterday": "2026-10-25"}
    assert all(selected[sid] is catalog[sid] for sid in selected)


def test_forecast_request_is_not_reclassified_as_current_observation():
    catalog = build_span_catalog({"a": {"content": "Projected prices in 2035 are 4 units."}})
    selected, trace = price_observation_catalog("What does today's report project for 2035 electricity prices?", "2026-10-26", catalog)
    assert selected is catalog and trace is None


def test_missing_exact_price_evidence_abstains_before_mapper_and_cannot_export(tmp_path, monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls): return cls(2026, 10, 26)
    monkeypatch.setattr("src.pilot.engine.date", FixedDate)
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([{"feed_id": "a", "clean_content": "Historical retail electricity prices in 2020 were 4 units.",
                                "published": "2026-10-26"}]), encoding="utf-8")
    corpus = Corpus(path)
    responses = iter([AIMessage(content="", tool_calls=[{"name": "search_sources", "args": {"query": "retail electricity prices"}, "id": "one"}]), AIMessage(content="done")])
    def forbidden(*args, **kwargs): raise AssertionError("Known missing evidence must not consume mapping/composition or guardrail calls")
    model = SimpleNamespace(bind_tools=lambda _: SimpleNamespace(invoke=lambda _: next(responses)), with_structured_output=forbidden)
    events = []
    result = PilotEngine(corpus, model, SimpleNamespace(validate_output=forbidden)).run(QUESTION, lambda *e: events.append(e))
    assert result["draft"]["claims"] == [] and result["metrics"]["model_calls"] == 2
    assert result["draft"]["warnings"] == [NO_INFORMATION, "The retrieved documents do not establish an answer to: " + QUESTION]
    assert any(kind == "dated_price_evidence_gate" for kind, _ in events)
    store = Store(tmp_path / "review.sqlite3")
    run, _ = store.create(ResearchRequest(query=QUESTION, request_key="price-absence"), corpus.sha)
    store.claim(run)
    store.save_draft(run, result["draft"], result["sources"], result["metrics"])
    with pytest.raises(Conflict):
        store.review(run, ReviewRequest(revision=1, decision="approve", reviewer="synthetic-owner", support_confirmed=True))
    with pytest.raises(Conflict): store.export(run)
