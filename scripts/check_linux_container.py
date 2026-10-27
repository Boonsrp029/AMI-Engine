"""Offline Linux tests from a sanitized source snapshot, with networking disabled."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import uuid


FOLDERS = ("src", "config", "scripts", "tests", "data", ".github")
SUFFIXES = {".py", ".json", ".yml", ".yaml", ".co", ".html", ".txt"}
SECRET = re.compile(rb"\bdapi[a-fA-F0-9]{32}\b|\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")


def prepare(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination == root or any(destination.is_relative_to(root / folder) for folder in FOLDERS):
        raise ValueError("Test snapshot must be outside the selected source folders")
    paths = set()
    for folder in FOLDERS:
        paths.update(p for p in (root / folder).rglob("*") if p.is_file() and (p.suffix in SUFFIXES or p.name == "Modelfile")
                     and "__pycache__" not in p.parts and not p.is_relative_to(root / "data/external"))
    for pattern in ("requirements*.txt", "constraints*.txt", "*.py", "databricks.yml", "pytest.ini", ".env.example"):
        paths.update(root.glob(pattern))
    contents = {}
    for path in sorted(paths):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("Source snapshot cannot follow external links")
        payload = path.read_bytes()
        if SECRET.search(payload):
            raise ValueError("Credential-shaped data found in selected source file: " + path.relative_to(root).as_posix())
        contents[path.relative_to(root).as_posix()] = payload
    destination.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name, payload in contents.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        hashes[name] = hashlib.sha256(payload).hexdigest()
    manifest = {"sha256": hashes, "context_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                "excluded": ["credentials", "reports/review databases", "virtualenvs", "data/external", "Git metadata"]}
    (destination / "offline-context.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    context = args.output / "context"
    manifest = prepare(Path.cwd(), context)
    name = "ami-linux-tests-" + uuid.uuid4().hex
    report = {"image": args.image, "context_sha256": manifest["context_sha256"], "network": "none", "status": "started",
              "remote_github_ci": False, "credentials_or_owner_reports_mounted": False}
    program = """import hashlib,json,os,sys
from pathlib import Path
m=json.loads(Path('/workspace/offline-context.json').read_text())
for name,digest in m['sha256'].items():
 if name.startswith(('src/','config/')):
  image_file=Path('/app')/name
  assert image_file.is_file() and hashlib.sha256(image_file.read_bytes()).hexdigest()==digest, 'Image/source mismatch: '+name
os.execv(sys.executable,[sys.executable,'-m','pytest','-q','--basetemp','/tmp/ami-pytest','-o','cache_dir=/tmp/pytest-cache'])
"""
    command = ["docker", "run", "--rm", "--name", name, "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,exec,mode=1777",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--mount", f"type=bind,source={context.resolve()},target=/workspace,readonly",
               "--workdir", "/workspace", "--env", "NEMO_GUARDRAILS_NO_USAGE_STATS=1", "--env", "HF_HUB_DISABLE_TELEMETRY=1",
               "--env", "LANGCHAIN_TRACING_V2=false", "--env", "LANGSMITH_TRACING=false", args.image, "python", "-c", program]
    try:
        with (args.output / "linux-pytest.txt").open("w", encoding="utf-8") as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
        report.update(status="passed" if completed.returncode == 0 else "failed", returncode=completed.returncode)
    except subprocess.TimeoutExpired:
        report.update(status="timed_out", returncode=None)
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, check=False)
        (args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
