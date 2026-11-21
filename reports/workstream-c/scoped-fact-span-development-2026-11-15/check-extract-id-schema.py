"""Probe the existing ID-only response slots for the proposed extract contract."""
from pathlib import Path
import sys

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.pilot._evidence import EvidenceMap
from src.pilot.subtasks._scoped_generation import table_composition_schema


def main():
    mapping = EvidenceMap.model_validate({
        "components": [
            {"component_id": "r1", "question_anchor": "report", "status": "supported",
             "short_answer": "Previously, harbor transmitters could send manifests weekly.",
             "evidence": [{"source_id": "port-log", "quote": "Previously, harbor transmitters could send manifests weekly."}]}
        ]
    })
    schema = table_composition_schema(mapping, {"u1": "r1"})
    selection = {"unit_id": "u1", "component_id": "r1"}
    title = "Analyst research brief"
    assert schema.model_validate({"title": title, "claims": [selection]}).model_dump(mode="json")["claims"] == [selection]
    for claims in ([], [{**selection, "unit_id": "u9"}], [{**selection, "component_id": "r9"}],
                   [{**selection, "text": "Currently reports weekly."}], [selection, selection]):
        try:
            schema.model_validate({"title": title, "claims": claims})
        except ValidationError:
            continue
        raise AssertionError(f"Unexpectedly accepted {claims}")
    print("6 offline schema checks passed")


if __name__ == "__main__":
    main()


