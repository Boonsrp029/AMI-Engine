"""Unapplied A activation adapter; fixed transports only, no inference."""
import hashlib
import json

import pytest

from test_scoped_disclosures import fixture, scopes, BINDINGS, FixedScoped, FACT
from src.pilot.subtasks._scoped_activation import prepare_composer, CONTRACT_VERSION
from src.pilot.subtasks.generation import ConcurrentComposer
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
import time


def packet(tmp_path):
    path, plan, _ = fixture(tmp_path)
    sidecar = tmp_path/'scopes.json'
    sidecar.write_text(scopes(plan).model_dump_json(), encoding='utf-8')
    sha = hashlib.sha256(sidecar.read_bytes()).hexdigest()
    frozen = {'plan': plan.model_dump(mode='json'), 'bindings': BINDINGS,
        'requested_scopes': str(sidecar), 'requested_scopes_sha256': sha,
        'complete_required_branches': BINDINGS}
    contract = {'composition_contract': CONTRACT_VERSION, 'as_of': '2026-11-07',
        'input_sha256': {str(sidecar.resolve()): sha}}
    return path, plan, sidecar, frozen, contract


def test_deadline_cap_retains_original_and_executed_provenance(tmp_path):
    path, plan, _, frozen, contract = packet(tmp_path)
    runtime = plan.model_copy(update={'deadline_seconds': 150.0})
    callback = prepare_composer(contract, frozen, runtime, FixedScoped(), None)
    report = run_plan(runtime, 'a'*32, 'b'*32, LocalBM25Adapter(path))
    access = ModelAccess(time.monotonic()+30)
    result = callback(report, access)
    assert result.draft['claims'][0]['text'] == FACT and access.calls == 2 and access.guards == 0
    lineage = result.diagnostics['scope_deadline_binding']
    assert lineage['declared_plan_id'] == plan.plan_id
    assert lineage['runtime_plan_id'] == runtime.plan_id != plan.plan_id
    assert lineage['declared_scope_contract']['plan_id'] == plan.plan_id
    assert result.diagnostics['scoped_disclosures']['scope_contract']['plan_id'] == runtime.plan_id


@pytest.mark.parametrize('damage', ['increase', 'query', 'branch', 'corpus', 'binding', 'scope_drift', 'unpinned', 'unknown_kind', 'no_kind'])
def test_only_deadline_reduction_is_permitted(tmp_path, damage):
    _, plan, sidecar, frozen, contract = packet(tmp_path)
    runtime = plan.model_copy(update={'deadline_seconds': 150.0})
    if damage == 'increase':
        runtime = runtime.model_copy(update={'deadline_seconds': 181.0})
    elif damage == 'query':
        runtime = runtime.model_copy(update={'query': 'Different request'})
    elif damage == 'branch':
        runtime = runtime.model_copy(update={'subtasks': tuple(reversed(plan.subtasks))})
    elif damage == 'corpus':
        runtime = runtime.model_copy(update={'corpus_sha256': 'f'*64})
    elif damage == 'binding':
        frozen['bindings'] = {'r1': ['s02', 's01']}
    elif damage == 'scope_drift':
        sidecar.write_text(sidecar.read_text()+' ')
    elif damage == 'unpinned':
        contract['input_sha256'] = {}
    elif damage == 'unknown_kind':
        contract['composition_contract'] = 'unknown'
    else:
        contract.pop('composition_contract')
    with pytest.raises(ValueError):
        prepare_composer(contract, frozen, runtime, FixedScoped(), None)


def test_old_contract_keeps_old_callback(tmp_path):
    _, plan, _, frozen, _ = packet(tmp_path)
    frozen.pop('requested_scopes'); frozen.pop('requested_scopes_sha256')
    callback = prepare_composer({'as_of': '2026-11-07'}, frozen, plan, FixedScoped(), None)
    assert type(callback) is ConcurrentComposer


def test_deadline_adapter_survives_existing_spawned_runner(tmp_path):
    from test_scoped_disclosures import allow
    from src.pilot.schemas import ResearchRequest, ReviewRequest
    from src.pilot.store import Store
    from src.pilot.subtasks.runner import run_stored_plan
    path, plan, _, frozen, contract = packet(tmp_path)
    runtime = plan.model_copy(update={'deadline_seconds': 150.0})
    callback = prepare_composer(contract, frozen, runtime, FixedScoped(), None)
    store = Store(tmp_path/'history.sqlite3')
    run_id, _ = store.create(ResearchRequest(query=plan.query, request_key='deadline-binding'), plan.corpus_sha256)
    run_stored_plan(store, run_id, runtime, path, LocalBM25Adapter(path), callback, allow)
    row = store.get(run_id)
    assert row['status'] == 'needs_review'
    assert row['metrics']['model_calls'] == 2 and row['metrics']['guardrail_invocations'] == 1
    lineage = row['metrics']['composition_diagnostics']['scope_deadline_binding']
    assert lineage['declared_plan_id'] == plan.plan_id
    assert lineage['runtime_plan_id'] == runtime.plan_id
    with pytest.raises(ValueError, match='current human-approved revision'):
        store.export(run_id)
    store.review(run_id, ReviewRequest(revision=1, decision='approve',
        reviewer='synthetic-test', support_confirmed=True))
    exported = store.export(run_id)
    assert store.export(run_id) == exported
    store.save_draft(run_id, row['draft'], row['sources'], {}, expected_revision=1)
    with pytest.raises(ValueError, match='current human-approved revision'):
        store.export(run_id)


def test_activated_development_entry_retains_original_scope_identity(tmp_path, monkeypatch):
    from src.pilot.subtasks.qualification import DevelopmentLedger
    from src.pilot.subtasks.qualification_runner import execute_development
    from test_scoped_disclosures import allow
    _, plan, sidecar, frozen, contract = packet(tmp_path)
    contract.update(case_ids=['p01', 'p02'], cases={'p01': frozen, 'p02': frozen},
        model_snapshot={'synthetic': True}, limits={'main_calls_per_case': 4,
            'nemo_per_case': 1, 'seconds_per_case': 180, 'retries': 0})
    corpus = tmp_path/'corpus.json'
    frozen['corpus_path'] = str(corpus)
    contract['input_sha256'][str(corpus)] = hashlib.sha256(corpus.read_bytes()).hexdigest()
    contract['contract_sha256'] = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    grant = {'contract_sha256': contract['contract_sha256'], 'case_ids': contract['case_ids'],
        'limits': contract['limits'], 'authorization_reference': 'SYNTHETIC TEST ONLY; no inference authorization'}
    ledger = DevelopmentLedger(tmp_path/'out', contract, grant)
    def identity(value):
        assert value == {'synthetic': True}
    # Model one second of preparation deterministically; do not depend on the
    # host clock's resolution or sleep to force a changed plan ID.
    real_clock = time.monotonic
    first = [True]
    def prepared_clock():
        if first[0]:
            first[0] = False
            return real_clock()-1
        return real_clock()
    monkeypatch.setattr(time, 'monotonic', prepared_clock)
    result = execute_development(ledger, 'p01', FixedScoped(), allow, identity)
    assert result['technical_pass'] and result['main_calls'] == 2 and result['nemo_invocations'] == 1
    provenance = result['stored_run']['metrics']['composition_diagnostics']['scope_deadline_binding']
    assert provenance['declared_plan_id'] == plan.plan_id
    assert provenance['runtime_plan_id'] != plan.plan_id
    assert 0 < provenance['runtime_deadline_seconds'] < provenance['declared_deadline_seconds']
    assert result['source_assessment'] == result['owner_adjudication'] == 'pending'
    raw = json.loads((ledger.output/'p01.mapping.raw.json').read_text())
    assert json.loads(raw['raw'])['wire_version'] == 'cq-scoped-selection-v1'
    with pytest.raises(ValueError, match='review is pending'):
        execute_development(ledger, 'p02', FixedScoped(), allow, identity)
