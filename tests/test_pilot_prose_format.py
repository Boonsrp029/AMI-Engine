"""Owner-requested prose formatting; exact evidence and approval remain separate."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.pilot._presentation import without_bullet_glyphs
from src.pilot.schemas import Draft, ResearchRequest, ReviewRequest
from src.pilot.store import Conflict, Store


@pytest.mark.parametrize("glyph", list("•▪▫‣⁃●○◦"))
def test_bullet_glyphs_removed_without_changing_facts_or_citations(glyph):
    raw = {"title": f"{glyph} Thailand report", "claims": [{
        "text": f"Thailand, August 2026: {glyph} Demand rose 4% to 2,000 TWh.", "source_ids": ["s"]}],
        "warnings": [f"{glyph} Check scope."]}
    value = Draft.model_validate(raw)
    assert value.claims[0].text == "Thailand, August 2026: Demand rose 4% to 2,000 TWh."
    assert value.claims[0].source_ids == ["s"]
    assert value.title == "Thailand report" and value.warnings == ["Check scope."]
    assert glyph in raw["claims"][0]["text"]  # Original evidence/input is not mutated.


def test_plain_prose_math_dates_and_hyphens_unchanged():
    text = "Month-to-month: -0.1%, 4% × 2, 2026-08-01, 1.3 TWh.\nSecond sentence."
    assert without_bullet_glyphs(text) == text
    with pytest.raises(ValidationError, match="prose"):
        Draft.model_validate({"title": "Report", "claims": [{"text": "▪ •", "source_ids": ["s"]}]})


def test_new_exports_are_paragraphs_cached_exports_unchanged_and_edits_require_approval(tmp_path):
    store = Store(tmp_path / "review.db")
    run, _ = store.create(ResearchRequest(query="What changed?", request_key="prose-format-test"), "corpus")
    assert store.claim(run)
    sources = {"s": {"title": "Report", "published": "2026-09-30", "page_num": 0,
                     "content": "▪ Demand rose 4%.", "url": "https://example.invalid/report"}}
    draft = {"title": "Report", "claims": [{"text": "▪ Demand rose 4%.", "source_ids": ["s"]}],
             "warnings": ["• Check reporting period."]}
    store.save_draft(run, draft, sources, {})
    store.review(run, ReviewRequest(revision=1, decision="approve", reviewer="synthetic-test", support_confirmed=True))
    content, revision = store.export(run)
    assert revision == 1 and "Demand rose 4%. [s]" in content and "PDF page 1" in content
    assert not any(line.startswith(("- ", "* ")) for line in content.splitlines())
    assert "▪" not in content and "•" not in content
    assert store.get(run)["sources"] == sources
    with store.connection() as db:
        db.execute("UPDATE exports SET content=? WHERE run_id=?", ("- historic cached export ▪\n", run))
    assert store.export(run) == ("- historic cached export ▪\n", 1)
    store.save_draft(run, draft, sources, {}, expected_revision=1)
    with pytest.raises(Conflict, match="approved"):
        store.export(run)


def test_browser_brief_and_warnings_use_paragraphs():
    html = Path("src/pilot/index.html").read_text(encoding="utf-8")
    assert '<div id="warnings"></div>' in html
    assert "text('p',c.text+" in html
    assert "warnings.map(w=>text('p',w))" in html
