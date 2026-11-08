"""Importable E/D browser workers: fixed public-fiction facts, no inference.

Filesystem gates are synchronization inputs, never evidence or production state.
Waiting polls for explicit release; tests assert state, never elapsed duration.
"""
from dataclasses import dataclass
from pathlib import Path
import threading
import time

_composition_identity = None


def key(run_id, attempt_id, stage):
    if (len(run_id) != 32 or len(attempt_id) != 32
            or any(c not in '0123456789abcdef' for c in run_id + attempt_id)
            or stage not in {'s01', 's02', 's03', 's04', 's05', 'composition', 'safety'}):
        raise ValueError('Invalid synthetic gate identity')
    return f'{run_id}.{attempt_id}.{stage}'


def gate(root, run_id, attempt_id, stage, cancelled=lambda: False):
    stem = Path(root) / key(run_id, attempt_id, stage)
    stem.with_suffix(stem.suffix + '.entered').touch()
    deadline = time.monotonic() + 170
    wait = threading.Event()
    while not Path(str(stem) + '.release').exists():
        if cancelled() or time.monotonic() >= deadline:
            raise TimeoutError('Synthetic controlled gate stopped')
        wait.wait(.01)
    if Path(str(stem) + '.fail').exists():
        raise ValueError('Synthetic controlled failure')


@dataclass(frozen=True)
class Operation:
    controls: str
    corpus_path: str

    def __call__(self, ctx):
        from src.pilot.engine import Corpus
        from src.pilot.subtasks.contracts import Result, Source, digest
        gate(self.controls, ctx.identity.run_id, ctx.identity.attempt_id, ctx.task.subtask_id, ctx.cancelled)
        corpus = Corpus(self.corpus_path)
        if corpus.sha != ctx.identity.corpus_sha256:
            raise ValueError('Synthetic corpus changed')
        number = int(ctx.task.subtask_id[-1])
        raw = corpus.sources[f'fiction-{number}']
        source = Source(**raw, content_sha256=digest(raw['content']), role='support')
        return Result(identity=ctx.identity, subtask_id=ctx.task.subtask_id,
                      child_attempt_id=ctx.child_attempt_id, dependencies=ctx.dependency_refs,
                      outcome='evidence', sources=(source,), elapsed_seconds=0.0)


@dataclass(frozen=True)
class Composer:
    controls: str

    def __call__(self, report, access):
        global _composition_identity
        _composition_identity = report.identity

        def fixed_response():
            gate(self.controls, report.identity.run_id, report.identity.attempt_id, 'composition')
            return {'title': 'Synthetic analyst workflow — not market evidence',
                    'claims': [{'text': item.source.content, 'source_ids': [item.source.source_id]}
                               for item in report.sources], 'warnings': []}
        # Uses the real stage/call-budget instrumentation, but invokes no model.
        return access.main(fixed_response)


@dataclass(frozen=True)
class Safety:
    controls: str

    def __call__(self, draft, sources):
        if _composition_identity is None:
            raise ValueError('Synthetic safety requires composition identity')
        gate(self.controls, _composition_identity.run_id, _composition_identity.attempt_id, 'safety')
        return True  # Fixed test callback; never a claim of real NeMo validation.


def sequential(job, connection):
    """Real sequential IPC protocol with a fixed response, no analyst engine."""
    from src.pilot.engine import Corpus
    from src.pilot._worker import send
    try:
        corpus = Corpus(job['corpus_path'])
        if corpus.sha != job['corpus_sha']:
            raise ValueError('Synthetic corpus changed')
        source = corpus.sources['fiction-1']
        send(connection, 'result', {
            'draft': {'title': 'Synthetic sequential brief',
                      'claims': [{'text': source['content'], 'source_ids': ['fiction-1']}], 'warnings': []},
            'sources': {'fiction-1': source},
            'metrics': {'model_calls': 0, 'guardrail_invocations': 0, 'synthetic_only': True,
                        'corpus_sha256': corpus.sha}})
    finally:
        connection.close()
