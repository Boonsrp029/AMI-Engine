"""Compile only after two exact current development passes; never run inference."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
SHARED = ROOT.parent / 'cq1-fact-span-pool-2026-11-15'
sys.path.insert(0, str(SHARED))
from build_qualification import build


def blocked(*args, **kwargs):
    raise AssertionError('Contract preparation cannot open sockets')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--development-sha256', required=True)
    args = parser.parse_args()
    socket.socket.connect = socket.create_connection = blocked
    audit = json.loads((ROOT / 'pool-freeze-audit.json').read_text(encoding='utf-8'))
    scopes = json.loads((ROOT / 'question-scopes/manifest.json').read_text(encoding='utf-8'))
    contract = build(development_path=ROOT / 'development-contract.json',
        expected_identity=args.development_sha256, pool=ROOT / 'pool',
        destination=ROOT / 'qualification-contract.json', output_directory=ROOT / 'actual-cq1',
        as_of=args.as_of, expected_pool_sha256=audit['manifest_sha256'],
        expected_plans_sha256=scopes['plans_sha256'],
        scope_manifest_path=ROOT / 'question-scopes/manifest.json',
        expected_scopes_sha256=hashlib.sha256((ROOT / 'question-scopes/manifest.json').read_bytes()).hexdigest(),
        review_protocol=ROOT / 'source-review-protocol.md',
        execution_artifacts=(Path(__file__), ROOT / 'run_qualification_case.py',
                             ROOT / 'new-source-provenance.json', ROOT / 'pool-freeze-audit.json'))
    print(json.dumps({'contract_sha256': contract['contract_sha256'], 'execution_authorized': False}))


if __name__ == '__main__':
    main()
