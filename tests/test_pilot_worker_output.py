"""Exercise actual native worker output channels with zero model calls."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest


@pytest.mark.parametrize("closed", [False, True])
def test_worker_discards_python_native_and_dependency_console_but_keeps_failure(tmp_path, closed):
    output = tmp_path / "failure.json"
    program = ("import sys;sys.path.insert(0,'tests/fixtures/workers');"
        "from output_privacy import run;run(sys.argv[1],sys.argv[2]=='closed')")
    env = {k:v for k,v in os.environ.items() if k.upper() in {"PATH","PATHEXT","SYSTEMROOT","WINDIR","COMSPEC"}}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run([sys.executable,"-c",program,str(output),"closed" if closed else "open"],cwd=Path.cwd(),env=env,
        capture_output=True,text=True,timeout=25,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
    assert result.returncode == 1
    assert json.loads(output.read_text()) == {"kind":"failure","payload":{"type":"RuntimeError"}}
    assert result.stdout == result.stderr == ""
