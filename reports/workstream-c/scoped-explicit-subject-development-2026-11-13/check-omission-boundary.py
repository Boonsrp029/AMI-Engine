"""Exercise omission boundaries without calling the application or a model."""
import json

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location("omission_prototype", Path(__file__).with_name("check-omission-contract.py"))
prototype = module_from_spec(spec)
spec.loader.exec_module(prototype)


def main():
    origins = {"u1": {"r1"}, "u2": {"r1"}}
    decisions = {"emitted": ["u1"], "omitted": ["u2"]}
    scenarios = [
        {
            "question": "What could the harbor transmitter send weekly, and to whom?",
            "kept": "The harbor transmitter could send weekly manifests to the port clerk.",
            "omitted": "The harbor office kept a separate log of vessel arrivals.",
            "should_allow_omission": True,
        },
        {
            "question": "What were the installation and annual maintenance costs?",
            "kept": "Installation cost 24,000 baht.",
            "omitted": "Annual maintenance cost 3,500 baht.",
            "should_allow_omission": False,
        },
    ]
    for case in scenarios:
        case["accounting_guard_allows_omission"] = (
            prototype.check_omissions(origins, **decisions) == {"u2"}
        )
    assert all(case["accounting_guard_allows_omission"] for case in scenarios)
    assert not scenarios[1]["should_allow_omission"]
    print(json.dumps({
        "synthetic_cases": scenarios,
        "component_coverage_is_not_fact_coverage": True,
        "runtime_activated": False,
        "model_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
