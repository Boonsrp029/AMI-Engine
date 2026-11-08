"""Operator wall-clock envelope for one granted case; no retries or warmups."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    started=time.monotonic()
    case=sys.argv[1]
    if case not in {"cq-p01","cq-p02"}:raise ValueError("Unknown granted case")
    root=Path(__file__).resolve().parent
    command=[sys.executable,"-m","src.pilot.subtasks.qualify_cli","--contract",str(root/"development-contract-v7.json"),
        "--mode","attempt","--grant",str(root/"development-grant-v7.json"),"--case",case]
    timed_out=False
    with (root/("execution-"+case+".txt")).open("xb") as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=os.name!="nt")
        try:
            code=process.wait(timeout=max(.001,180-(time.monotonic()-started)))
        except subprocess.TimeoutExpired:
            timed_out=True
            if os.name=="nt":
                subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],stdout=log,stderr=subprocess.STDOUT,check=False)
            else:
                os.killpg(process.pid,signal.SIGKILL)
            code=process.wait()
    result={"case_id":case,"returncode":code,"timed_out":timed_out,"wall_limit_seconds":180,
        "elapsed_seconds":time.monotonic()-started,"retry_performed":False,
        "backend_cancellation_verified":False,"termination_targets":"only the process tree owned by this invocation"}
    with (root/("wall-clock-"+case+".json")).open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2);stream.write("\n")
    if timed_out or code!=0:
        output=root/"actual-development-v7";output.mkdir(exist_ok=True)
        marker=output/"stopped.json"
        if not marker.exists():
            with marker.open("x",encoding="utf-8") as stream:
                json.dump({"case_id":case,"reason":"operator execution/deadline failure; allowance closed"},stream)
    print(json.dumps(result))
    return 1 if timed_out else code


if __name__=="__main__":raise SystemExit(main())
