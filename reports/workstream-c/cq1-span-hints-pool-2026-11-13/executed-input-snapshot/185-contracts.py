"""ami-subtasks-v1: structural validation, never evidence entailment."""
import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

VERSION = 'ami-subtasks-v1'
Status = Literal['queued', 'waiting_on_dependency', 'running', 'completed', 'failed', 'cancelled', 'blocked']
TERMINAL = frozenset({'completed', 'failed', 'cancelled', 'blocked'})
TRANSITIONS = {
    'queued': frozenset({'waiting_on_dependency', 'running', 'cancelled', 'blocked'}),
    'waiting_on_dependency': frozenset({'running', 'blocked', 'cancelled'}),
    'running': frozenset({'completed', 'failed', 'cancelled'}),
}


def transition(previous: Status, following: Status):
    if following not in TRANSITIONS.get(previous, ()):
        raise ValueError('Invalid subtask status transition')


def digest(text: str):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)


class Subtask(Contract):
    subtask_id: str = Field(pattern=r'^s0[1-5]$')
    operation: Literal['retrieve', 'inspect_sources']
    query: str | None = Field(default=None, min_length=1, max_length=500)
    source_ids: tuple[str, ...] = Field(default=(), max_length=5)
    dependencies: tuple[str, ...] = Field(default=(), max_length=4)
    required: bool = True
    timeout_seconds: float = Field(default=30.0, gt=0, le=180, allow_inf_nan=False)

    @model_validator(mode='after')
    def operation_inputs(self):
        if len(set(self.dependencies)) != len(self.dependencies) or self.subtask_id in self.dependencies:
            raise ValueError('Duplicate or self dependency')
        if self.operation == 'retrieve':
            if self.query is None or not self.query.strip() or self.source_ids:
                raise ValueError('Retrieval requires a query and no source IDs')
        elif self.query is not None or not self.source_ids:
            raise ValueError('Inspection requires source IDs and no query')
        if len(set(self.source_ids)) != len(self.source_ids) or any(not s.strip() or len(s)>200 for s in self.source_ids):
            raise ValueError('Invalid inspection source IDs')
        return self


class Plan(Contract):
    version: Literal['ami-subtasks-v1'] = VERSION
    query: str = Field(min_length=3, max_length=1200)
    corpus_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    subtasks: tuple[Subtask, ...] = Field(min_length=1, max_length=5)
    retrieval_concurrency: int = Field(default=2, ge=1, le=2)
    deadline_seconds: float = Field(default=180.0, gt=0, le=180, allow_inf_nan=False)
    model_concurrency: Literal[1] = 1
    maximum_main_calls: Literal[4] = 4

    @field_validator('query')
    @classmethod
    def nonblank_query(cls, value):
        if not value.strip(): raise ValueError('Research query cannot be blank')
        return value

    @model_validator(mode='after')
    def graph(self):
        ids = [s.subtask_id for s in self.subtasks]
        if ids != [f's{i:02}' for i in range(1,len(ids)+1)]:
            raise ValueError('IDs must follow declared order s01 through s05')
        graph = {s.subtask_id: s.dependencies for s in self.subtasks}
        visited, visiting = set(), set()
        def visit(node):
            if node not in graph: raise ValueError('Unknown dependency')
            if node in visiting: raise ValueError('Cyclic dependency')
            if node in visited: return
            visiting.add(node)
            for parent in graph[node]: visit(parent)
            visiting.remove(node); visited.add(node)
        for node in graph: visit(node)
        return self

    @property
    def plan_id(self):
        return digest(json.dumps(self.model_dump(mode='json'), sort_keys=True, separators=(',',':'), ensure_ascii=False))


class Identity(Contract):
    run_id: str = Field(pattern=r'^[0-9a-f]{32}$')
    attempt_id: str = Field(pattern=r'^[0-9a-f]{32}$')
    plan_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    corpus_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class Source(Contract):
    source_id: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    corpus_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    role: Literal['support', 'context']
    title: str = ''
    url: str = ''
    published: str | None = None
    doc_name: str | None = None
    page_num: int | None = Field(default=None, ge=0)

    @model_validator(mode='after')
    def exact_content(self):
        if digest(self.content) != self.content_sha256:
            raise ValueError('Source content hash mismatch')
        return self


class DependencyRef(Contract):
    subtask_id: str = Field(pattern=r'^s0[1-5]$')
    child_attempt_id: str = Field(pattern=r'^[0-9a-f]{32}$')
    result_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class Result(Contract):
    identity: Identity
    subtask_id: str = Field(pattern=r'^s0[1-5]$')
    child_attempt_id: str = Field(pattern=r'^[0-9a-f]{32}$')
    dependencies: tuple[DependencyRef, ...] = Field(default=(), max_length=4)
    outcome: Literal['evidence', 'missing', 'conflicting']
    sources: tuple[Source, ...] = Field(default=(), max_length=5)
    elapsed_seconds: float = Field(ge=0, allow_inf_nan=False)
    diagnostic: Literal['none', 'no_matching_evidence', 'conflicting_evidence'] = 'none'

    @model_validator(mode='after')
    def evidence_identity(self):
        if len({d.subtask_id for d in self.dependencies}) != len(self.dependencies):
            raise ValueError('Duplicate dependency provenance')
        if any(s.corpus_sha256 != self.identity.corpus_sha256 for s in self.sources):
            raise ValueError('Result corpus mismatch')
        if len({s.source_id for s in self.sources}) != len(self.sources):
            raise ValueError('Duplicate source ID within result')
        support = any(s.role=='support' for s in self.sources)
        if self.outcome in {'evidence','conflicting'} and not support:
            raise ValueError('Evidence outcome requires supporting records')
        if self.outcome=='missing' and support:
            raise ValueError('Missing outcome cannot assert supporting evidence')
        return self


class Progress(Contract):
    version: Literal['ami-subtasks-v1'] = VERSION
    identity: Identity
    subtask_id: str = Field(pattern=r'^s0[1-5]$')
    child_attempt_id: str = Field(pattern=r'^[0-9a-f]{32}$')
    ordinal: int = Field(ge=1)
    status: Status
    created_at: datetime
    reason: Literal['none','dependency_failed','branch_deadline','parent_deadline','parent_cancelled','operation_failed','interrupted','required_branch_failed'] = 'none'

    @field_validator('created_at')
    @classmethod
    def aware(cls,value):
        if value.utcoffset() is None: raise ValueError('Progress time must be timezone-aware')
        return value
