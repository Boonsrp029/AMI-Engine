"""Exercise verified-field projection on consumed evidence, without changing runtime."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = spec_from_file_location("request_coverage_probe", ROOT / "probe-request-coverage.py")
PROBE = module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def project(kind, raw, verified):
    if set(raw) != set(verified) or any(PROBE.normalize(raw[key]) != PROBE.normalize(value)
                                       for key, value in verified.items()):
        raise ValueError("Each required field must retain its verified source phrase")
    if kind == "counted_capabilities":
        return f"{verified['subject']} can {verified['first']} and {verified['second']}."
    if kind == "example_conditions":
        return f"For example, if {verified['conditions']}, {verified['result']}."
    raise ValueError("Unknown coverage kind")


def main():
    summary = json.loads((ROOT / "qualification-batch-summary.json").read_bytes())
    candidates = {}
    for cid in ("cq1-a26", "cq1-a10"):
        data = PROBE.probe(cid, summary)
        fields = data["source_fields"]
        candidates[cid] = {"result_sha256": data["result_sha256"],
                           "required_fields": fields, "citation_source_id": data["source"],
                           "projected_text": project(data["kind"], fields, fields),
                           "archived_power_or_capability_prose_retained": data["saved_raw_text"]}
    fixtures = [
        ("What two capabilities does the report describe for refrigerated lockers?",
         "Some refrigerated lockers can detect door openings and log temperature remotely.",
         "Some refrigerated lockers can detect door openings and log temperature remotely."),
        ("How much water does the garden sprinkler example use?",
         "For example, if you run a six-liter-per-minute sprinkler for four minutes, you have used 24 liters.",
         "For example, if you run a six-liter-per-minute sprinkler for four minutes, you have used 24 liters."),
    ]
    checks = 0
    for question, quote, expected in fixtures:
        kind, fields = PROBE.coverage_kind(question, quote)
        assert project(kind, fields, fields) == expected
        checks += 1
        for key in fields:
            for invalid in ({k: v for k, v in fields.items() if k != key}, {**fields, key: "unrelated replacement"}):
                try:
                    project(kind, invalid, fields)
                except ValueError:
                    checks += 1
                else:
                    raise AssertionError("Omitted or substituted source field passed")
    print(json.dumps({"model_calls": 0, "runtime_changed": False, "synthetic_checks": checks,
                      "candidates": candidates, "safety_or_persistence_tested": False}, indent=2))


if __name__ == "__main__":
    main()
