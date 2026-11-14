"""One granted case with an owned 180-second process envelope. Default: inspect."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(root, expected):
    path = root/'development-contract.json'
    c = json.loads(path.read_text(encoding='utf-8'))
    body = {k: v for k, v in c.items() if k != 'contract_sha256'}
    actual = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if actual != expected or c.get('contract_sha256') != expected:
        raise ValueError('Frozen contract identity changed')
    if (c['phase'] != 'development' or c['case_ids'] != ['cq-hint01', 'cq-hint02']
            or c['composition_contract'] != 'cq-scoped-composition-v1'
            or c['limits'] != {'main_calls_per_case': 4, 'nemo_per_case': 1, 'seconds_per_case': 180, 'retries': 0}
            or Path(c['output_directory']).resolve() != (root/'actual-development-v1').resolve()):
        raise ValueError('Execution scope changed')
    for name, digest in c['input_sha256'].items():
        if sha(name) != digest:
            raise ValueError('Frozen input changed')
    return c


def execute(root, expected, grant_path, case, *, popen=subprocess.Popen, clock=time.monotonic, terminate=None):
    started = clock()
    c = inspect(root, expected)
    grant_path = Path(grant_path).resolve()
    g = json.loads(grant_path.read_text(encoding='utf-8'))
    if (g.get('contract_sha256') != expected or g.get('case_ids') != c['case_ids']
            or g.get('limits') != c['limits'] or not isinstance(g.get('authorization_reference'), str)
            or not g['authorization_reference'].strip()
            or g.get('human_reply') != c['authorization_reply']):
        raise ValueError('New direct user grant required')
    if case not in c['case_ids']:
        raise ValueError('Unknown case')
    output = Path(c['output_directory'])
    if (output/'stopped.json').exists():
        raise ValueError('Allowance already closed')
    if case == 'cq-hint02':
        a = json.loads((output/'cq-hint01.assessment.json').read_text())
        if a.get('verdict') != 'pass' or a.get('result_sha256') != sha(output/'cq-hint01.result.json'):
            raise ValueError('First case source gate has not passed')
    command = [sys.executable, '-m', 'src.pilot.subtasks.qualify_cli', '--contract', str(root/'development-contract.json'),
        '--mode', 'attempt', '--grant', str(grant_path), '--case', case]
    timed_out = False
    with (root/f'execution-{case}.txt').open('xb') as log:
        process = None
        try:
            if clock()-started >= 180:
                raise subprocess.TimeoutExpired(command, 180)
            process = popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=c['project_root'], start_new_session=os.name != 'nt')
            remaining = 180-(clock()-started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, 180)
            code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            timed_out = True
            if process is None:
                code = None
            elif terminate:
                terminate(process)
            elif os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=log,
                    stderr=subprocess.STDOUT, timeout=5, check=False)
                if process.poll() is None:
                    process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            if process is not None:
                code = process.wait(timeout=5)
    record = {'case_id': case, 'returncode': code, 'timed_out': timed_out, 'wall_limit_seconds': 180,
        'retry_performed': False, 'source_review_pending': True,
        'backend_cancellation_verified': False, 'termination_targets': 'only this invocation owned process tree'}
    try:
        inspect(root, expected)
    except Exception as error:
        record['identity_error'] = type(error).__name__
    elapsed = clock()-started
    record.update(elapsed_seconds=elapsed, wall_budget_exceeded=elapsed > 180)
    with (root/f'wall-clock-{case}.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(record, indent=2)+'\n')
    if timed_out or code != 0 or record['wall_budget_exceeded'] or 'identity_error' in record:
        output.mkdir(exist_ok=True)
        if not (output/'stopped.json').exists():
            with (output/'stopped.json').open('x', encoding='utf-8') as handle:
                json.dump({'case_id': case, 'reason': 'operator failure/deadline/identity; allowance closed'}, handle)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--grant', type=Path)
    parser.add_argument('--case')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if not args.execute:
        inspect(root, args.contract_sha256)
        print(json.dumps({'status': 'verified only; no inference', 'execution_authorized': False}))
        return 0
    if not args.grant or not args.case:
        parser.error('Execution requires a direct applicable grant and explicit case')
    record = execute(root, args.contract_sha256, args.grant, args.case)
    print(json.dumps(record))
    return 1 if record['timed_out'] or record['returncode'] != 0 or record['wall_budget_exceeded'] or 'identity_error' in record else 0


if __name__ == '__main__':
    raise SystemExit(main())
