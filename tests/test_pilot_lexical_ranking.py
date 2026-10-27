"""Synthetic retrieval fixtures, not held-out model-quality evidence."""
import json

from src.pilot._retrieval_policy import LEXICAL_VERSION, lexical_terms, rank_evidence
from src.pilot.engine import Corpus


def records():
    return [
        {"source_id": "currency", "content": "Thailand's currency strengthened seasonally as market worries faded and tourism revenue increased."},
        {"source_id": "date", "content": "18 December 2024"},
        {"source_id": "investment", "content": "Foreign investment applications covered tourism infrastructure and electronics projects."},
        {"source_id": "visitors", "content": "The number of foreign tourists after seasonal adjustment stayed stable. Tourism revenue rose as longer-staying visitors increased. Arrivals from Cedar rose while arrivals from Maple fell."}]


def test_intent_fusion_normalises_tourism_terms_without_changing_evidence():
    source = records()
    before = json.loads(json.dumps(source))
    selected, trace = rank_evidence("Thailand seasonally adjusted tourism receipts December 2024 origin markets", source, 3,
        "Why did tourism receipts rise while tourist numbers stayed stable, and which origin markets changed?")
    assert selected[0]["source_id"] == "visitors"
    assert "date" not in trace["source_ids"]
    assert trace["policy"] == LEXICAL_VERSION and trace["tourism_vocabulary_active"]
    assert source == before and selected[0]["content"] == source[3]["content"]


def test_receipts_are_not_rewritten_as_revenue_outside_tourism():
    assert "receipt" in lexical_terms("receipts", tourism=False)
    assert "revenue" not in lexical_terms("receipts", tourism=False)
    source = [{"source_id": "receipt", "content": "Receipt retention requirements cover invoice records."},
              {"source_id": "revenue", "content": "Revenue increased from sales."}]
    selected, trace = rank_evidence("receipt retention requirements", source, 3)
    assert [s["source_id"] for s in selected] == ["receipt"]
    assert not trace["tourism_vocabulary_active"]


def test_generic_ties_limits_and_empty_queries_are_deterministic():
    source = [{"source_id": "a", "content": "Investment increased."}, {"source_id": "b", "content": "Investment increased."}]
    assert [r["source_id"] for r in rank_evidence("investment", source, 1)[0]] == ["a"]
    assert rank_evidence("the and December 2024", source, 2)[0] == []
    assert rank_evidence("unknown topic", source, 2)[0] == []
    # A generic request word such as "changed" need not occur in an answer
    # stating an increase; it must not suppress the available subject match.
    assert rank_evidence("What changed in investment?", source, 2)[0] == source


def test_corpus_raw_search_keeps_legacy_ranking_and_source_metadata(tmp_path):
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([{"feed_id": s["source_id"], "title": "Synthetic source", "clean_content": s["content"]} for s in records()]), encoding="utf-8")
    corpus = Corpus(path)
    original = corpus.search("Thailand seasonally adjusted tourism receipts December 2024 origin markets", 3)
    revised, trace = corpus.search_evidence("origin markets", requested_query="Why did tourism receipts rise while tourist numbers stayed stable?")
    assert revised[0]["source_id"] == "visitors"
    assert original == corpus.search("Thailand seasonally adjusted tourism receipts December 2024 origin markets", 3)
    assert all(row == corpus.sources[row["source_id"]] for row in revised)
