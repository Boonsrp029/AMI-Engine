"""Offline probe for selecting one explicit, complete conversion statement."""
import json
from pathlib import Path
import re
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from pydantic import ValidationError
from src.pilot.subtasks._fact_selection import fact_schema
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


QUESTION = re.compile(
    r"how many (?P<first>[a-z]+) and (?P<second>[a-z]+) "
    r"(?:does [\w ]+ say )?are equivalent to one (?P<base>[a-z]+)\?",
    re.I,
)
NUMBER = r"(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"
STATEMENT = re.compile(
    rf"(?<!\w)(?:one|1) (?P<base>[a-z]+) (?:is|equals) "
    rf"(?P<first>{NUMBER}) (?P<first_unit>[a-z]+)(?:,? or| and) "
    rf"(?P<second>{NUMBER}) (?P<second_unit>[a-z]+)\.(?!\d)",
    re.I,
)
ALIASES = {"kilowatts": "kw", "watts": "w", "megawatt": "mw",
           "minutes": "minute", "seconds": "second"}


def key(word):
    word = word.casefold()
    return ALIASES.get(word, word)


def unique_conversion_span(question, catalog):
    """Only offer statements containing both requested units and the base unit."""
    request = QUESTION.fullmatch(question.strip())
    if request is None:
        return None
    targets = {key(request["first"]), key(request["second"])}
    if len(targets) != 2 or key(request["base"]) in targets:
        return None
    matches = []
    for span_id, span in catalog.items():
        for candidate in STATEMENT.finditer(span["text"]):
            units = {key(candidate["first_unit"]), key(candidate["second_unit"])}
            if key(candidate["base"]) == key(request["base"]) and units == targets:
                matches.append((span_id, candidate.group(0)))
    return matches[0] if len(matches) == 1 else None


def blocked(*args, **kwargs):
    raise AssertionError("Offline probe cannot open a socket")


def main():
    socket.socket.connect = socket.create_connection = blocked
    unit_question = "How many minutes and seconds are equivalent to one hour?"
    source = "One hour equals 60 minutes, or 3,600 seconds."
    fixtures = [
        ({"correct": {"text": source}, "unrelated": {"text": "One minute is 60 seconds."}}, "correct"),
        ({"missing": {"text": "One hour is 60 minutes."}}, None),
        ({"wrong_base": {"text": "One day is 60 minutes, or 3,600 seconds."}}, None),
        ({"wrong_target": {"text": "One hour is 60 minutes, or 3,600 milliseconds."}}, None),
        ({"correct": {"text": source}, "conflict": {"text": source.replace("3,600", "3,000")}}, None),
        ({"repetition": {"text": source + " " + source}}, None),
    ]
    for candidates, expected in fixtures:
        found = unique_conversion_span(unit_question, candidates)
        assert (found[0] if found else None) == expected

    contract = json.loads((ROOT / "qualification-contract.json").read_bytes())
    case = contract["cases"]["cq1-a22"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    catalog = {}

    class MappingCaptured(Exception):
        pass

    def capture_input(stage, schema, instruction, inputs):
        assert stage == "mapping"
        for record in inputs["evidence"]:
            for span in record["spans"]:
                catalog[span["span_id"]] = {**span, "source_id": record["source_id"]}
        raise MappingCaptured

    try:
        prepare_composer(contract, case, plan, capture_input, None)(report, ModelAccess(time.monotonic() + 30))
    except MappingCaptured:
        pass
    span_id, quote = unique_conversion_span(plan.query, catalog)
    assert span_id == "s_d1ad042cf9ed1c0a"
    # Use the existing exact-focus schema constraint to simulate a single verified direct choice.
    # This fixture does not activate a conversion focus or alter composition behavior.
    schema = fact_schema([{"fact_id": "r1.1", "component_id": "r1"}], catalog=catalog,
                         bindings=case["bindings"], report=report,
                         focuses={"r1": {"kind": "table_row", "span_id": span_id}})
    capture = ROOT / "actual-cq1/cq1-a22.mapping.raw.json"
    raw = json.loads(json.loads(capture.read_bytes())["raw"])
    try:
        schema.model_validate_json(json.dumps(raw))
    except ValidationError:
        pass
    else:
        raise AssertionError("Repeated unrelated choices passed the focused schema")
    raw["facts"][0]["alternatives"] = [[{"span_id": span_id, "context": []}]]
    schema.model_validate_json(json.dumps(raw))
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "synthetic_fixtures": len(fixtures),
                      "retrieved_spans_checked": len(catalog), "selected_span_id": span_id, "direct_quote": quote,
                      "saved_bad_selection_rejected": True, "fixed_direct_selection_parsed": True,
                      "runtime_changed": False, "qualification_credit": False}, indent=2))


if __name__ == "__main__":
    main()
