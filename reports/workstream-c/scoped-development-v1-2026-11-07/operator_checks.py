"""Owned fake-process checks. Synthetic documents grant no inference."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

import run_case as operator


ROOT = Path(__file__).resolve().parent/'operator-verified-selfcheck-fixtures'


def packet(name):
    root = ROOT/name
    root.mkdir(parents=True, exist_ok=False)
    contract = {'phase': 'development', 'composition_contract': 'cq-scoped-composition-v1',
        'case_ids': ['cq-p01', 'cq-p02'], 'limits': {'main_calls_per_case': 4, 'nemo_per_case': 1,
            'seconds_per_case': 180, 'retries': 0}, 'input_sha256': {}, 'project_root': str(root),
        'output_directory': str(root/'actual-development-v1'), 'authorization_reply': 'SYNTHETIC TEST ONLY'}
    digest = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    contract['contract_sha256'] = digest
    (root/'development-contract.json').write_text(json.dumps(contract))
    grant = root/'SYNTHETIC-grant.json'
    grant.write_text(json.dumps({'contract_sha256': digest, 'case_ids': contract['case_ids'],
        'limits': contract['limits'], 'authorization_reference': 'SYNTHETIC; NOT REAL AUTHORIZATION',
        'human_reply': contract['authorization_reply']}))
    return root, digest, grant


class Checks(unittest.TestCase):
    def test_once_only_success_preserves_source_review_gate(self):
        root, digest, grant = packet('success')
        calls = []
        timeouts = []
        class Process:
            def wait(self, timeout):
                timeouts.append(timeout)
                return 0
        def fake(command, **kwargs):
            calls.append(command)
            return Process()
        result = operator.execute(root, digest, grant, 'cq-p01', popen=fake)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(timeouts), 1)
        self.assertTrue(0 < timeouts[0] <= 180)
        self.assertTrue(result['source_review_pending'])
        with self.assertRaises(FileExistsError):
            operator.execute(root, digest, grant, 'cq-p01', popen=fake)
        with self.assertRaises(FileNotFoundError):
            operator.execute(root, digest, grant, 'cq-p02', popen=fake)
        self.assertEqual(len(calls), 1)

    def test_timeout_closes_and_never_restarts(self):
        root, digest, grant = packet('timeout')
        class Process:
            stopped = False
            def wait(self, timeout):
                if self.stopped:
                    return -9
                raise subprocess.TimeoutExpired('fake owned case', timeout)
        process = Process()
        kills = []
        def terminate(p):
            self.assertIs(p, process)
            p.stopped = True
            kills.append(1)
        result = operator.execute(root, digest, grant, 'cq-p01', popen=lambda *a, **k: process, terminate=terminate)
        self.assertTrue(result['timed_out'])
        self.assertEqual(kills, [1])
        self.assertFalse(result['backend_cancellation_verified'])
        self.assertTrue((root/'actual-development-v1/stopped.json').exists())
        with self.assertRaisesRegex(ValueError, 'already closed'):
            operator.execute(root, digest, grant, 'cq-p02', popen=lambda *a, **k: self.fail('No retry'))

    def test_missing_or_wrong_grant_never_launches(self):
        root, digest, grant = packet('refusal')
        def forbidden(*a, **k):
            self.fail('No process without valid explicit grant')
        with self.assertRaises(FileNotFoundError):
            operator.execute(root, digest, root/'missing.json', 'cq-p01', popen=forbidden)
        value = json.loads(grant.read_text()); value['authorization_reference'] = None
        grant.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'direct user grant'):
            operator.execute(root, digest, grant, 'cq-p01', popen=forbidden)
        self.assertFalse((root/'execution-cq-p01.txt').exists())

    def test_exhausted_preparation_budget_never_launches(self):
        root, digest, grant = packet('preparation-timeout')
        ticks = iter([0, 181, 181])
        result = operator.execute(root, digest, grant, 'cq-p01', clock=lambda: next(ticks),
            popen=lambda *a, **k: self.fail('Preparation exhausted; no child may start'))
        self.assertTrue(result['timed_out'])
        self.assertTrue(result['wall_budget_exceeded'])
        self.assertIsNone(result['returncode'])
        self.assertTrue((root/'actual-development-v1/stopped.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
