"""Run with -B from the executed snapshot root; no current mapper migration."""
import hashlib
import json
from pathlib import Path
import socket
from unittest.mock import patch


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    snapshot=Path.cwd().resolve()
    manifest=json.loads((snapshot/"manifest.json").read_text(encoding="utf-8"))
    assert all(sha(snapshot/name)==value for name,value in manifest["input_sha256"].items())
    package=snapshot.parent
    contract=package/"development-contract-v7.json"
    mapping=package/"actual-development-v7/cq-p02.mapping.raw.json"
    frozen=json.loads(contract.read_text(encoding="utf-8"))
    expected={"contract":sha(contract),"mapping":sha(mapping),
              "corpus":sha(frozen["cases"]["cq-p02"]["corpus_path"])}
    def forbidden(*args,**kwargs):raise AssertionError("Historical replay cannot open sockets")
    with (patch.object(socket.socket,"connect",forbidden),patch.object(socket.socket,"connect_ex",forbidden),
          patch.object(socket,"create_connection",forbidden),patch.object(socket,"getaddrinfo",forbidden)):
        import scripts._concurrent_composer_capture as helper
        import src.pilot.subtasks.generation as generation
        assert Path(helper.__file__).resolve().is_relative_to(snapshot)
        assert Path(generation.__file__).resolve().is_relative_to(snapshot)
        assert generation.CONCURRENT_MAPPING_VERSION=="cq-mapper-v5-decoder-coverage"
        try:
            helper.capture_composer(contract,"cq-p02",mapping,expected=expected)
        except ValueError as exc:error=str(exc)
        else:raise AssertionError("Original semantic rejection must remain")
    assert error=="Evidence mapping gap anchor is not in the question"
    assert sha(mapping)==expected["mapping"]
    output=package.parent/"question-span-2026-11-07"
    output.mkdir(exist_ok=True)
    result={"source":"exact v7 executed snapshot","mapper_version":generation.CONCURRENT_MAPPING_VERSION,
        "replayed_failure":error,"current_private_wire_used":False,"actual_model_calls":0,
        "nemo_invocations":0,"socket_connections_blocked":True,"original_raw_mapper_unchanged":True,
        "original_mapper_sha256":expected["mapping"],"snapshot_source_hashes_verified":len(manifest["input_sha256"])}
    with (output/"historical-v7-replay.json").open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2);stream.write("\n")
    print(json.dumps(result))


if __name__=="__main__":main()
