"""Compare v9 prose enforcement with verified membership rendering offline."""
import json
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from src.pilot.subtasks._request_focus import REQUIRED_TARGET_FIELDS, membership_prose
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(path.read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("Offline probe cannot open a socket")


def render_verified_members(texts, focus):
    if list(texts) != list(REQUIRED_TARGET_FIELDS):
        raise ValueError("Both bound membership fields are required")
    members = focus["members"]
    if [" ".join(texts[field].casefold().split()) for field in REQUIRED_TARGET_FIELDS] != members:
        raise ValueError("Membership fields differ from exact source groups")
    first, second = members
    return f"The {focus['category']} category includes {first} and {second}."


def main():
    socket.socket.connect = socket.create_connection = blocked
    packet = read(ROOT / "development-contract.json")
    assert all(digest(path) == sha for path, sha in packet["input_sha256"].items())
    case = packet["cases"]["cq1-a24"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    paths = {stage: ROOT / "actual-development-v1" / f"cq1-a24.{stage}.raw.json"
             for stage in ("mapping", "composition")}
    saved = {stage: read(path)["raw"] for stage, path in paths.items()}

    def fixed(stage, schema, instruction, inputs):
        raw = saved[stage]
        return {"raw": raw, "parsed": schema.model_validate_json(raw).model_dump()}

    def project():
        return prepare_composer(packet, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))

    try:
        project()
    except ValueError as error:
        assert "complete source member" in str(error)
    else:
        raise AssertionError("The historical v9 result was not rejected")

    with patch("src.pilot.subtasks._scoped_generation.membership_prose", render_verified_members):
        projection = project()
    assert projection.draft["claims"] == [{"text": "The other gases category includes blast furnace gas and "
                                           "other manufactured and waste gases derived from fossil fuels.",
                                           "source_ids": ["eia-generation-2023"]}]
    assert json.loads(json.dumps(projection.diagnostics["raw_composer_output"])) == json.loads(saved["composition"])
    assert not projection.diagnostics["fallback_unit_ids"] and not projection.diagnostics["editorial_correction"]

    focus = {"category": "reclaimed aggregates", "members": [
        "crushed stone", "other recycled minerals sourced from retired concrete"]}
    first, second = focus["members"]
    valid = {"target_1": first, "target_2": second}
    assert render_verified_members(valid, focus).endswith(f"{first} and {second}.")
    prose = {field: f"The reclaimed aggregates category includes {item}." for field, item in valid.items()}
    assert membership_prose(prose, focus) == " ".join(prose.values())
    negatives = [{"target_1": first}, {"target_1": second, "target_2": first},
                 {**valid, "target_2": "other recycled minerals"},
                 {**valid, "target_2": "other recycled minerals sourced from asphalt"}]
    for target in negatives:
        try:
            render_verified_members(target, focus)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed member group was accepted")
    print(json.dumps({"actual_model_calls": 0, "sockets_blocked": True, "runtime_changed": False,
                      "v9_saved_response_rejected": True, "distinct_fact_checks": 2 + len(negatives),
                      "raw_capture_sha256": {k: digest(p) for k, p in paths.items()},
                      "application_rendered_candidate": projection.draft,
                      "actual_safety_or_persistence_tested": False}, indent=2))


if __name__ == "__main__":
    main()
