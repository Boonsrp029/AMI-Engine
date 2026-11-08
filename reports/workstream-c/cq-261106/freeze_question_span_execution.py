"""Offline protocol preparation only. Does not create a grant or run a service."""
import json
from pathlib import Path
import socket

from scripts.concurrent_mapper_check import check_protocol, LIMITS, REQUIRED_PROJECT_FILES
from scripts._mapper_transport import read_json, sha, MODEL
from scripts._llama_token_count import encoding


def main():
    def forbidden(*args, **kwargs):
        raise AssertionError("Protocol preparation is offline")
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = socket.getaddrinfo = forbidden
    root = Path(__file__).resolve().parent
    folder = root / "question-span-2026-11-07"
    proposal = read_json(folder / "mapper-preflight-proposal.json")
    frozen = read_json(folder / "mapper-input.json")
    metadata = root / "tokenizer-metadata.json"
    assert sha(metadata) == "fa1ba7031fa5853b7f1f766c35c2627b5e56235939d52c2694e5f8744ae71cf5"
    counter = encoding(json.loads(metadata.read_text(encoding="utf-8")))
    content = sum(len(counter.encode(m["content"])) for m in frozen["messages"])
    audit = {"message_content_tokens": content, "framing_reservation": 256,
        "completion_reservation": 900, "conservative_total": content + 1156,
        "limit": 4096, "within_conservative_allowance": content + 1156 <= 4096,
        "schema_format_tokens_separate": len(counter.encode(json.dumps(frozen["schema"]))),
        "server_observed_tokens": False, "grammar_processing_latency": "unverified",
        "tokenizer_metadata_sha256": sha(metadata), "actual_model_calls": 0}
    assert audit["within_conservative_allowance"]
    with (folder / "mapper-context-audit.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(audit, indent=2) + "\n")
    project_names = REQUIRED_PROJECT_FILES | {"tests/test_concurrent_mapper_check.py",
        "tests/test_concurrent_mapper_envelope.py", "scripts/_llama_token_count.py"}
    files = ("mapper-input.json", "mapper-request-body.json", "mapper-preflight-proposal.json", "mapper-context-audit.json")
    protocol = {"kind": "concurrent-mapper-only-v1", "limits": LIMITS,
        "model": MODEL, "case_id": "cq-p02", "output_directory": "actual-mapper",
        "input": files[0], "native_body": files[1], "proposal": files[2],
        "native_body_sha256": sha(folder / files[1]),
        "model_digest": proposal["model_snapshot"]["digest"],
        "authorization_reply": "Authorize one cq-p02 question-span mapper diagnostic",
        "project_files": {name: sha(Path(name)) for name in sorted(project_names)},
        "files": {name: sha(folder / name) for name in files},
        "acceptance": proposal["acceptance"], "as_of": proposal["as_of"],
        "source_review": {"after_response": "assistant checks exact selected facts, denominator, geography, period and unresolved price span before any later grant",
            "technical_validation_is_quality_acceptance": False,
            "raw_selection": "retain unchanged", "application_resolution": "retain separately",
            "editorial_correction": "none authorized; never count as raw success", "owner_acceptance": "not inferred"},
        "excluded": proposal["excluded"],
        "prior_allowances": "all closed; unused calls cannot be reused",
        "output_policy": "new immutable operator-envelope and actual-mapper directories; no retry, warmup or conditional workflow",
        "process_boundary": "95-second Windows owned-controller envelope includes pin checks and child CLI startup; timeout terminates owned process tree; backend cancellation unverified"}
    path = folder / "execution-protocol.json"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n")
    check_protocol(path, sha(path))
    print(json.dumps({"protocol_sha256": sha(path), "actual_model_calls": 0, "execution_authorized": False,
        "conservative_total": audit["conservative_total"], "grammar_tokens": audit["schema_format_tokens_separate"]}))


if __name__ == "__main__":
    main()
