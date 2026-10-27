"""Necessary evidence-date gate for exact relative-date price observations."""
import re
from datetime import date

from src.pilot._evidence import relative_dates


def price_observation_catalog(question, as_of, catalog):
    dates = relative_dates(question, as_of)
    if not dates or not re.search(r"\bprices?\b", question, re.I):
        return catalog, None
    exact_observation = re.search(r"\b(?:exact|actual|observed|were|was)\b", question, re.I)
    if not exact_observation and re.search(r"\b(?:forecast|project\w*|expected|estimated|reports?|outlook)\b", question, re.I):
        return catalog, None
    qualifiers = [word for word in ("retail", "electricity", "wholesale", "household")
                  if re.search(r"\b" + word + r"\b", question, re.I)]
    forms = []
    for value in dates.values():
        day = date.fromisoformat(value)
        forms += [value, day.strftime("%Y/%m/%d")]
        for month in (day.strftime("%B"), day.strftime("%b")):
            forms += [f"{day.day} {month} {day.year}", f"{month} {day.day}, {day.year}", f"{month} {day.day} {day.year}"]
    accepted = {}
    for sid, span in catalog.items():
        text = " ".join(span["text"].split())
        if not any(re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", text, re.I) for value in forms):
            continue
        if (not re.search(r"\b(?:prices?|tariffs?|rates?|costs?)\b", text, re.I)
                or any(not re.search(r"\b" + word + r"\b", text, re.I) for word in qualifiers)
                or re.search(r"\b(?:forecast\w*|project\w*|expected|estimated)\b", text, re.I)):
            continue
        accepted[sid] = span
    return accepted, {"requested_dates": dates, "required_measure_words": qualifiers,
        "eligible_span_ids": list(accepted), "checked_span_count": len(catalog),
        "result": "necessary_date_and_measure_match" if accepted else "requested_dated_price_evidence_unavailable",
        "limitation": "Exact source date and price terms are necessary, not a semantic support guarantee; publication metadata alone is insufficient."}
