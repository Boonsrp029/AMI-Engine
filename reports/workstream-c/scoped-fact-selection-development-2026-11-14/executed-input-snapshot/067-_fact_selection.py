"""Private fact decisions for the opt-in concurrent workflow."""
import re
from typing import Literal

from pydantic import Field, create_model

from src.utils._periods import _COMMAND
from .._evidence import GeographySelection, _resolve_span
from ..schemas import StrictModel


WIRE_VERSION = "cq-fact-selection-v1"
_COORDINATED_COST = re.compile(
    r"what (?:were|are) the (?P<first>[a-z ]+?) and (?P<second>[a-z ]+?) costs\b", re.I)
INSTRUCTION = (
    "Use the supplied facts in order. For each fact, select direct evidence and exact character offsets "
    "within each span, with an exclusive end. Keep necessary same-record context separate from answers. "
    "Exclude background and preserve source time, scope, measure and modality. Multiple spans can jointly "
    "answer one fact. For supported use one group; for missing use no groups; for conflicting use separate "
    "groups for opposing records about the same requested fact. Respect branch bindings and request_focus. "
)


class DirectSpan(StrictModel):
    span_id: str = Field(min_length=1, max_length=100)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    context: list[str] = Field(max_length=2)


class FactDecision(StrictModel):
    fact_id: str = Field(min_length=1, max_length=30)
    state: Literal["supported", "missing", "conflicting"]
    alternatives: list[list[DirectSpan]] = Field(max_length=3)


def fact_slots(requests):
    slots = []
    for request in requests:
        component = request["component_id"]
        anchor = request["question_anchor"]
        match = _COORDINATED_COST.match(anchor)
        if match and any(" and " in match[key].lower() for key in ("first", "second")):
            match = None
        subjects = [match["first"], match["second"]] if match else [None]
        for index, subject in enumerate(subjects, 1):
            slot = {**request, "fact_id": f"{component}.{index}"}
            if subject:
                slot["requested_measure"] = f"{subject} cost"
            slots.append(slot)
    if len(slots) > 5:
        raise ValueError("Fact selection exceeds the five-fact limit")
    return slots


def fact_schema(slots, geography_type=GeographySelection):
    entries = tuple(create_model(f"FactDecision{index}", __base__=FactDecision,
        fact_id=(Literal[slot["fact_id"]], ...)) for index, slot in enumerate(slots))
    return create_model("ConcurrentFactSelection", __base__=StrictModel,
        wire_version=(Literal[WIRE_VERSION], ...), facts=(tuple[entries], ...),
        geography=(geography_type, ...))


def resolve_facts(value, slots, bindings, catalog, sources, report, focuses):
    support = {branch.subtask_id: branch for branch in report.results}
    components = {}
    resolved = []
    for slot, fact in zip(slots, value["facts"], strict=True):
        cid = slot["component_id"]
        state = fact["state"]
        groups = fact["alternatives"]
        if fact["fact_id"] != slot["fact_id"]:
            raise ValueError("Fact decisions differ from the requested facts")
        if (state not in {"supported", "missing", "conflicting"}
                or (state == "missing" and groups) or (state == "supported" and len(groups) != 1)
                or (state == "conflicting" and len(groups) < 2)
                or any(not 1 <= len(group) <= 5 for group in groups)):
            raise ValueError("Invalid fact evidence groups")
        outcomes = {"evidence", "conflicting"} if state == "conflicting" else {"evidence"}
        allowed = {source.source_id for bid in bindings[cid]
                   if (branch := support.get(bid)) and branch.outcome in outcomes
                   for source in branch.sources if source.role == "support"}
        seen = set()
        alternatives = []
        for group in groups:
            extracts = []
            for part in group:
                span_id = part["span_id"]
                if span_id in seen or len(set([span_id, *part["context"]])) != 1 + len(part["context"]):
                    raise ValueError("Duplicate fact evidence role")
                seen.add(span_id)
                quote = _resolve_span(span_id, catalog, sources)
                if quote["source_id"] not in allowed:
                    raise ValueError("Fact evidence crosses its bound support branches")
                contexts = []
                for context_id in part["context"]:
                    context = _resolve_span(context_id, catalog, sources)
                    if context["source_id"] != quote["source_id"]:
                        raise ValueError("Fact context crosses its direct source record")
                    context_span = catalog[context_id]
                    contexts.append({**context, "span_id": context_id,
                                     "source_offsets": [context_span["start"], context_span["end"]],
                                     "content_sha256": context_span["content_sha256"]})
                if any(_COMMAND.search(item["quote"]) for item in [quote, *contexts]):
                    raise ValueError("Selected fact evidence contains instruction-like source content")
                start, end = part["start"], part["end"]
                answer = quote["quote"][start:end]
                if not 0 <= start < end <= len(quote["quote"]) or not answer.strip():
                    raise ValueError("Invalid fact answer offsets")
                extracts.append({**quote, "span_id": span_id, "answer": answer,
                                 "start": start, "end": end, "context": contexts,
                                 "source_offsets": [catalog[span_id]["start"], catalog[span_id]["end"]],
                                 "content_sha256": catalog[span_id]["content_sha256"]})
            alternatives.append(extracts)
        if state == "conflicting":
            records = [{part["source_id"] for part in group} for group in alternatives]
            if sum(map(len, records)) != len(set().union(*records)):
                raise ValueError("Fact conflict alternatives must use distinct source records")
        focus = focuses.get(cid)
        if focus and state == "supported" and seen != {focus["span_id"]}:
            raise ValueError("Fact selection does not retain its verified focus")
        if focus and focus["kind"] == "table_row" and state == "supported":
            answer = alternatives[0][0]["answer"]
            # Optional numeric footnote markers can precede the amount.
            row = (r"\b" + re.escape(focus["label"]) + r"\s+(?:[1-9]\s+)?"
                   + re.escape(focus["amount"]) + r"\s+" + re.escape(focus["share"]))
            if re.search(row + r"(?![\d.])", answer, re.I) is None:
                raise ValueError("Selected table excerpt does not contain its verified row")
        resolved.append({**slot, "state": state, "alternatives": alternatives})
        components.setdefault(cid, []).append((state, seen))

    projected = []
    for cid, entries in components.items():
        supported = set().union(*(ids for state, ids in entries if state == "supported"))
        conflicting = set().union(*(ids for state, ids in entries if state == "conflicting"))
        if supported:
            state = "supported" if all(state == "supported" for state, _ in entries) else "partial"
        else:
            state = "conflicting" if conflicting else "missing"
        selected = supported or conflicting
        projected.append({"component_id": cid, "status": state,
                          "evidence": [sid for sid in catalog if sid in selected]})
    return {"components": projected, "geography": value["geography"], "period": ""}, resolved


def attach_fact_context(inputs, facts):
    """Give only matching units the context for their selected direct spans."""
    for unit in inputs["units"]:
        components = {origin["component_id"] for origin in unit["origins"]}
        evidence = {(item["source_id"], item["quote"]) for item in unit["evidence"]}
        selected = [{"fact_id": fact["fact_id"], "requested_measure": fact.get("requested_measure"),
                     "source_literal_answer": extract["answer"],
                     "context": [item["quote"] for item in extract["context"]]}
                    for fact in facts if fact["component_id"] in components and fact["state"] == "supported"
                    for extract in fact["alternatives"][0]
                    if (extract["source_id"], extract["quote"]) in evidence]
        if selected:
            unit["selected_facts"] = selected


def check_fact_claims(result, facts, rendered_rows):
    """Check literal retention and reject loss of an explicit could qualifier."""
    coverage = result.diagnostics.get("public_claim_coverage", [])
    units = result.diagnostics.get("canonical_composition_units", [])
    originals = {origin["unit_id"]: unit for unit in units for origin in unit["origins"]}
    row_ids = {row["unit_id"] for row in rendered_rows}
    for fact in facts:
        if fact["state"] != "supported":
            continue
        for direct in fact["alternatives"][0]:
            claims = []
            for item in coverage:
                for unit_id in item["unit_ids"]:
                    unit = originals.get(unit_id)
                    if unit and fact["component_id"] in {o["component_id"] for o in unit["origins"]} and {
                        "source_id": direct["source_id"], "quote": direct["quote"]
                    } in unit["evidence"]:
                        claims.append((unit["unit_id"], result.draft["claims"][item["claim_index"]]["text"]))
            literal = " ".join(direct["answer"].casefold().split())
            if not any(uid in row_ids or (
                    re.search(r"(?<!\w)" + re.escape(literal) + r"(?!\w)", " ".join(text.casefold().split()))
                    and (not re.search(r"\bcould\b", direct["quote"], re.I) or re.search(r"\bcould\b", text, re.I)))
                    for uid, text in claims):
                raise ValueError("Projected claim loses a selected fact literal or capability qualifier")
