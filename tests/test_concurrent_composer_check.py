"""Mocked process/admission checks. Synthetic grant documents authorize no runs."""
import json
from pathlib import Path

import pytest
from test_concurrent_composer_capture import frozen, response

from scripts import concurrent_composer_check as controller
from scripts._concurrent_composer_capture import capture_composer, sha
from scripts._mapper_transport import request_body


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def protocol(tmp_path, monkeypatch):
    project = Path.cwd()
    for name in controller.REQUIRED_PROJECT_FILES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((project/name).read_bytes())
    contract, mapping, expected = frozen(tmp_path)
    captured = capture_composer(contract,"p01",mapping,expected=expected)
    # The production contract roster uses cq-p01; preserve exactly that case key.
    value = json.loads(contract.read_text())
    value["cases"]["cq-p01"] = value["cases"].pop("p01")
    write(contract,value)
    expected["contract"] = sha(contract)
    folder = tmp_path / "packet"
    folder.mkdir()
    write(folder/"input.json",captured["captured"])
    write(folder/"native.json",request_body(captured["captured"]))
    p = {"kind":"concurrent-composer-only-v1", "limits":controller.LIMITS, "model":controller.MODEL,
        "case_id":"cq-p01", "output_directory":"actual", "input":"input.json", "native_body":"native.json",
        "native_body_sha256":sha(folder/"native.json"), "frozen_contract":str(contract),
        "frozen_mapping":str(mapping), "replay_identity":expected,
        "authorization_reply":"SYNTHETIC TEST ONLY", "model_digest":"a"*64,
        "project_files":{name:sha(tmp_path/name) for name in controller.REQUIRED_PROJECT_FILES},
        "files":{name:sha(folder/name) for name in ("input.json","native.json")}}
    path = folder / "protocol.json"
    write(path,p)
    monkeypatch.chdir(tmp_path)
    return path,p


def service(content=None):
    return {"status":"completed_transport", "model_calls_started":1, "response_complete":True,
        "identity_before":True, "identity_after":True, "finish":{"done_reason":"stop"},
        "content":json.dumps(content or response()), "usage":{"input_tokens":30,"output_tokens":20,"total_tokens":50},
        "inflight_usage_unknown":False}


def grant(path,p):
    target = path.parent/"synthetic-grant.json"
    write(target,{"contract_sha256":sha(path), "human_reply":p["authorization_reply"],
                  "authorization_reference":"SYNTHETIC TEST ONLY; no actual authorization"})
    return target


def test_default_inspection_has_no_output_or_service(tmp_path,monkeypatch):
    path,p = protocol(tmp_path,monkeypatch)
    monkeypatch.setattr(controller,"supervise",lambda *a:pytest.fail("No service in inspect mode"))
    assert controller.main(["--protocol",str(path),"--sha256",sha(path)]) == 0
    assert not (path.parent/"actual").exists()


def test_request_hash_drift_prevents_execution(tmp_path,monkeypatch):
    path,p = protocol(tmp_path,monkeypatch)
    (path.parent/"input.json").write_bytes((path.parent/"input.json").read_bytes()+b" ")
    with pytest.raises(ValueError,match="request changed"):
        controller.check_protocol(path,sha(path))


def test_missing_user_reference_refuses_before_output(tmp_path,monkeypatch):
    path,p = protocol(tmp_path,monkeypatch)
    auth = grant(path,p)
    g = json.loads(auth.read_text());g["authorization_reference"] = ""
    write(auth,g)
    with pytest.raises(ValueError,match="user grant"):
        controller.execute(path,sha(path),auth)
    assert not (path.parent/"actual").exists()


def test_timeout_closes_once_without_validation_or_retry(tmp_path,monkeypatch):
    path,p = protocol(tmp_path,monkeypatch)
    calls = []
    def timeout(command,output,seconds):
        calls.append(command)
        output.mkdir()
        write(output/"service-progress.json",{"model_calls_started":1,"response_complete":False})
        return {"timed_out":True,"returncode":-1}
    monkeypatch.setattr(controller,"supervise",timeout)
    auth = grant(path,p)
    result = controller.execute(path,sha(path),auth)
    assert result["status"].startswith("failed") and result["model_calls_started"] == 1
    assert result["inflight_usage_unknown"] is True and len(calls) == 1
    with pytest.raises(FileExistsError):
        controller.execute(path,sha(path),auth)
    assert len(calls) == 1


def test_fixed_service_response_validates_without_safety_or_auto_workflow(tmp_path,monkeypatch):
    path,p = protocol(tmp_path,monkeypatch)
    calls = []
    def fixed(command,output,seconds):
        calls.append(command)
        output.mkdir()
        if output.name == "service":
            write(output/"service-result.json",service())
        else:
            validated = controller.validate_response(path,sha(path),output.parent/"service/service-result.json",output)
            assert validated["network_blocked"] is True
            assert validated["replay"]["safety_passed"] is False
        return {"timed_out":False,"returncode":0}
    monkeypatch.setattr(controller,"supervise",fixed)
    result = controller.execute(path,sha(path),grant(path,p))
    assert result["status"].startswith("validated;") and len(calls) == 2
    assert result["model_calls_started"] == 1 and result["nemo_invocations"] == 0
    assert result["conditional_workflow_authorized"] is False
    assert result["source_assessment"] == "pending" and result["owner_adjudication"] == "pending"
    assert result["approvals_created"] == result["exports_created"] == 0


def test_invalid_retained_prose_stays_failure_under_socket_block(tmp_path,monkeypatch):
    path,p = protocol(tmp_path,monkeypatch)
    out = tmp_path/"validation";out.mkdir()
    retained = tmp_path/"service.json"
    write(retained,service(response("Observed electricity demand increased 45.9% in 2014.")))
    result = controller.validate_response(path,sha(path),retained,out)
    assert result["status"] == "failed" and "numeric value absent" in result["error"]
    assert result["actual_model_calls"] == result["nemo_invocations"] == 0
