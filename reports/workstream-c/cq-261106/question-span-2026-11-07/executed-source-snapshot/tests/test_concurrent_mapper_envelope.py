"""Fake owned processes only; no model, service or actual process termination."""
import subprocess

import pytest

from test_concurrent_mapper_check import packet, grant
from scripts import concurrent_mapper_envelope as envelope
from scripts._mapper_transport import sha


def test_missing_grant_refuses_before_outer_process(packet):
    path, _, _ = packet
    with pytest.raises(FileNotFoundError):
        envelope.run(path, sha(path), path.parent / "absent-grant.json",
            popen=lambda *a, **k: pytest.fail("No process without grant"))
    assert not (path.parent / "operator-envelope").exists()


def test_outer_success_does_not_claim_source_acceptance(packet):
    path, p, _ = packet
    now = [0.0]
    calls = []
    class Process:
        def wait(self, timeout):
            assert 0 < timeout <= 95
            now[0] += 1
            return 0
    def spawn(command, **kwargs):
        calls.append(command)
        return Process()
    auth = grant(path, p)
    result = envelope.run(path, sha(path), auth, popen=spawn, clock=lambda: now[0])
    assert len(calls) == 1 and result["returncode"] == 0 and not result["timed_out"]
    assert result["source_assessment"] == result["owner_adjudication"] == "pending"
    with pytest.raises(FileExistsError):
        envelope.run(path, sha(path), auth, popen=spawn)
    assert len(calls) == 1


def test_outer_timeout_terminates_owned_tree_once_and_never_restarts(packet):
    path, p, _ = packet
    now = [0.0]
    killed = []
    class Process:
        pid = 123
        stopped = False
        def wait(self, timeout):
            if self.stopped:
                return -9
            now[0] = 95
            raise subprocess.TimeoutExpired("synthetic owned process", timeout)
        def poll(self):
            return -9 if self.stopped else None
    process = Process()
    def terminate(target):
        assert target is process
        killed.append(target.pid)
        target.stopped = True
    result = envelope.run(path, sha(path), grant(path, p), popen=lambda *a, **k: process,
        clock=lambda: now[0], terminate_tree=terminate)
    assert killed == [123] and result["timed_out"] and result["returncode"] == -9
    assert result["backend_cancellation_verified"] is False and result["retry_performed"] is False
