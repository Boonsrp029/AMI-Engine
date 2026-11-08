"""Freeze revised composer input and replay failed prose offline, without inference."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts._concurrent_composer_capture import capture_composer, sha
from scripts._llama_token_count import encoding
from scripts._mapper_transport import request_body
from src.pilot.subtasks._composition_instruction import CONCURRENT_COMPOSITION_VERSION


ROOT = Path(__file__).resolve().parent


def write_once(path, data):
    if path.exists():
        # Resume offline preparation only when the partial artifact is identical.
        assert json.loads(path.read_text(encoding="utf-8")) == json.loads(json.dumps(data)), path
        return
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    contract_path = ROOT / "development-contract-v6.json"
    mapping_path = ROOT / "actual-development-v5/cq-p01.mapping.raw.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    case = contract["cases"]["cq-p01"]
    expected = {"contract":sha(contract_path), "mapping":sha(mapping_path),
                "corpus":sha(case["corpus_path"])}
    recorded = json.loads((ROOT / "v6-diagnostic-findings.json").read_text(encoding="utf-8"))
    assert expected["mapping"] == recorded["evidence_sha256"][mapping_path.name]
    captured = capture_composer(contract_path,"cq-p01",mapping_path,expected=expected)
    assert captured["status"] == "captured without inference"
    failed_path = ROOT / "actual-development-v5/cq-p01.composition.raw.json"
    assert sha(failed_path) == recorded["evidence_sha256"][failed_path.name]
    bad = json.loads(json.loads(failed_path.read_text(encoding="utf-8"))["raw"])
    replay = capture_composer(contract_path,"cq-p01",mapping_path,expected=expected,response=bad)
    assert replay["status"] == "composition validation failed"
    assert replay["error"] == "Draft introduces a numeric value absent from its selected evidence"
    original_inputs = json.loads((ROOT / "v6-offline-replay.json").read_text(encoding="utf-8"))["composition_inputs"]
    assert json.loads(captured["captured"]["messages"][1]["content"]) == original_inputs
    folder = ROOT / "unit-local-composer-v2"
    folder.mkdir(exist_ok=True)
    write_once(folder / "capture.json", captured)
    write_once(folder / "input.json", captured["captured"])
    write_once(folder / "native-body.json", request_body(captured["captured"]))
    write_once(folder / "retained-failure-replay.json", replay)
    counter = encoding(json.loads((ROOT / "tokenizer-metadata.json").read_text(encoding="utf-8")))
    content_tokens = sum(len(counter.encode(m["content"])) for m in captured["captured"]["messages"])
    old_tokens = len(counter.encode(json.dumps(original_inputs,ensure_ascii=False,separators=(",",":"))))
    # The prior system message is retained in the exact failed runtime snapshot.
    from src.pilot._evidence import COMPOSITION_INSTRUCTION
    old_tokens += len(counter.encode(COMPOSITION_INSTRUCTION))
    schema_tokens = len(counter.encode(json.dumps(captured["captured"]["schema"])))
    budget = {"composition_version":CONCURRENT_COMPOSITION_VERSION,"message_content_tokens":content_tokens,
        "previous_message_content_tokens":old_tokens,"framing_allowance":256,
        "completion_reservation":900,"total_budget":content_tokens+256+900,"limit":4096,
        "schema_format_tokens_not_in_messages":schema_tokens,
        "within_conservative_allowance":content_tokens+256+900<=4096,
        "count_scope":"exact frozen cq-p01 mapping only; not every future mapping",
        "generation_calls":0,"actual_backend_latency":"unverified",
        "payload_unchanged_from_v6":True,"retained_bad_composer_rejects":True}
    assert budget["within_conservative_allowance"]
    write_once(folder / "context-audit.json", budget)
    write_once(folder / "manifest.json", {p.name:sha(p) for p in folder.iterdir() if p.is_file()})
    print(json.dumps(budget))


if __name__ == "__main__":
    main()
