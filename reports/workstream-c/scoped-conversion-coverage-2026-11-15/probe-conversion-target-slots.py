"""Prototype two required model-written conversion sentences without activating them."""
import json
from pathlib import Path
import re
import socket
import sys
import time
from typing import Literal
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from pydantic import ValidationError, create_model
from src.pilot.schemas import StrictModel
from src.pilot.subtasks._request_focus import _CLAIM_VALUE, _conversion_unit
from src.pilot._quantities import _number, _SCALES
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


SENTENCE = re.compile(
    rf"(?:one|1) (?P<base>[a-z]+) (?:equals|is|is equal to|is equivalent to) "
    rf"(?P<value>{_CLAIM_VALUE}) (?P<target>[a-z]+)\.", re.I)
SLOTS = ("target_1", "target_2")


def response_type(unit_id, component_id):
    targets = create_model("ConversionTargets", __base__=StrictModel,
                           **{slot: (str, ...) for slot in SLOTS})
    claim = create_model("ConversionClaim", __base__=StrictModel, unit_id=(Literal[unit_id], ...),
                         component_id=(Literal[component_id], ...), targets=(targets, ...))
    return create_model("ConversionResponse", __base__=StrictModel,
                        title=(Literal["Analyst research brief"], ...), claims=(tuple[claim], ...))


def join_targets(value, focus):
    texts = []
    for slot, (unit, expected) in zip(SLOTS, focus["targets"].items(), strict=True):
        text = value[slot]
        match = SENTENCE.fullmatch(" ".join(text.split()))
        if not match or _conversion_unit(match["base"]) != focus["base_unit"] or _conversion_unit(match["target"]) != unit:
            raise ValueError("Conversion slot has the wrong relation or unit")
        amount = match["value"].casefold().split()
        numeral = "1" if amount[0] == "one" else amount[0]
        if _number(numeral) * _SCALES[amount[1] if len(amount) == 2 else ""] != _number(expected):
            raise ValueError("Conversion slot has the wrong value")
        texts.append(text.strip())
    return " ".join(texts)


def blocked(*args, **kwargs):
    raise AssertionError("Offline probe cannot open a socket")


def main():
    socket.socket.connect = socket.create_connection = blocked
    alternate = {"base_unit": "hour", "targets": {"minute": "60", "second": "3600"}}
    alternate_text = {"target_1": "One hour equals 60 minutes.", "target_2": "One hour equals 3,600 seconds."}
    assert join_targets(alternate_text, alternate) == " ".join(alternate_text.values())
    try:
        join_targets({"target_1": alternate_text["target_2"], "target_2": alternate_text["target_1"]}, alternate)
    except ValueError:
        pass
    else:
        raise AssertionError("Swapped synthetic slots passed")
    packet = json.loads((ROOT / "development-contract.json").read_bytes())
    case = packet["cases"]["cq1-a22"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    raw = {stage: json.loads(json.loads(
        (ROOT / "actual-development-v1" / f"cq1-a22.{stage}.raw.json").read_bytes())["raw"])
        for stage in ("mapping", "composition")}
    validations = {}

    def fixed(stage, schema, instruction, inputs):
        if stage == "mapping":
            value = raw[stage]
        else:
            unit, = inputs["units"]
            envelope = response_type(unit["unit_id"], unit["component_id"])
            assert set(envelope.model_json_schema()["$defs"]["ConversionTargets"]["required"]) == set(SLOTS)
            fixed_targets = {"target_1": raw[stage]["claims"][0]["text"],
                             "target_2": "One megawatt equals one million watts."}
            ids = {key: unit[key] for key in ("unit_id", "component_id")}

            def parse(targets):
                return envelope.model_validate_json(json.dumps({"title": "Analyst research brief",
                                                               "claims": [{**ids, "targets": targets}]}))

            for missing in SLOTS:
                try:
                    parse({k: v for k, v in fixed_targets.items() if k != missing})
                except ValidationError:
                    validations[f"missing_{missing}_rejected"] = True
                else:
                    raise AssertionError("Missing slot was accepted")
            for name, substitute in [
                ("swapped_unit", "One megawatt equals one million kilowatts."),
                ("wrong_value", "One megawatt equals one thousand watts."),
                ("unrelated_base", "One kilowatt equals one million watts."),
                ("negation", "One megawatt does not equal one million watts."),
            ]:
                try:
                    join_targets({**fixed_targets, "target_2": substitute}, unit["required_conversion"])
                except ValueError:
                    validations[f"{name}_rejected"] = True
                else:
                    raise AssertionError(f"{name} was accepted")
            parsed = parse(fixed_targets).model_dump()
            text = join_targets(parsed["claims"][0]["targets"], unit["required_conversion"])
            value = {"title": parsed["title"], "claims": [{**ids, "text": text}]}
        return {"parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

    # The prototype checks the two sentences before projection. Replace only the live
    # single-sentence rule in this local process so other projection gates still run.
    with patch("src.pilot.subtasks._scoped_generation.validate_conversion_claim"):
        result = prepare_composer(packet, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    assert result.draft["claims"] == [{"text": "One megawatt equals one thousand kilowatts. "
                                     "One megawatt equals one million watts.", "source_ids": ["eia-measurement"]}]
    assert not result.diagnostics["fallback_unit_ids"]
    print(json.dumps({"model_calls": 0, "sockets_blocked": True, "runtime_changed": False,
                      "validations": validations, "distinct_fact_fixture_checks": 2,
                      "fixed_projection": result.draft}, indent=2))


if __name__ == "__main__":
    main()
