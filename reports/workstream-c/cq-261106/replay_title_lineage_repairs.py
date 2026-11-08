"""Replay the preserved actual composer response through repaired projection offline."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts._concurrent_composer_capture import capture_composer, sha


ROOT=Path(__file__).resolve().parent


def main():
    old=ROOT/"unit-local-composer-v2"
    frozen=json.loads((old/"protocol-v2.json").read_text(encoding="utf-8"))
    expected=frozen["replay_identity"]
    service_path=old/"actual/service/service-result.json"
    service_sha=sha(service_path)
    service=json.loads(service_path.read_text(encoding="utf-8"))
    prior=json.loads((old/"actual/validation/validation-result.json").read_text(encoding="utf-8"))["replay"]
    result=capture_composer(Path(frozen["frozen_contract"]),"cq-p01",Path(frozen["frozen_mapping"]),
        expected=expected,response=json.loads(service["content"]))
    assert result["status"].startswith("composition validated")
    assert result["actual_model_calls"]==result["nemo_invocations"]==0
    assert result["draft"]["title"]=="Analyst research brief"
    assert result["draft"]["claims"]==prior["draft"]["claims"]
    assert result["draft"]["warnings"]==prior["draft"]["warnings"]==[]
    assert result["diagnostics"]["fallback_unit_ids"]==[]
    assert result["diagnostics"]["geography_resolution"]==prior["diagnostics"]["geography_resolution"]
    assert result["captured"]==prior["captured"]
    assert sha(service_path)==service_sha
    target=ROOT/"title-lineage-2026-11-07"
    target.mkdir()
    with (target/"offline-retained-response-replay.json").open("x",encoding="utf-8") as stream:
        json.dump({"label":"fixed-response engineering replay; not fresh generation or owner acceptance",
            "original_actual_service_sha256":service_sha,"original_actual_title":prior["draft"]["title"],
            "repaired_title":result["draft"]["title"],"claims_and_warnings_unchanged":True,
            "mapper_resolution_unchanged":True,"request_schema_messages_unchanged":True,
            "actual_model_calls":0,"nemo_invocations":0,"result":result},stream,ensure_ascii=False,indent=2)
        stream.write("\n")
    print(json.dumps({"fixed_response_replay":"passed","title_before":prior["draft"]["title"],
        "title_after":result["draft"]["title"],"actual_model_calls":0,"claims_unchanged":True}))


if __name__=="__main__":main()
