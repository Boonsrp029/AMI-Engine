"""Approved scoped contract with real typed envelopes and fixed model responses."""
from dataclasses import dataclass, replace
import hashlib
import json
import time

import pytest

from src.pilot._evidence import ResolvedEvidenceMap
from src.pilot.schemas import ResearchRequest, ReviewRequest
from src.pilot.store import Store, Conflict
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.scheduler import run_plan, aggregate
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess, run_stored_plan
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash, project_disclosures
from src.pilot.subtasks._scoped_generation import ScopedConcurrentComposer, WIRE_VERSION


QUESTION = 'Describe solar generation in Chile in 2012 and provide Chile retail gas tariffs today.'
FACT = 'In Chile, solar supplied 12% of total electricity generation in 2012.'
REORDERED_FACT = 'In 2012, solar supplied 12% of total electricity generation in Chile.'
BINDINGS = {'r1': ['s01', 's02']}


def scopes(plan, *, unresolved=False):
    spans = ['solar generation in Chile in 2012', 'Chile retail gas tariffs today']
    return DisclosureScopes.model_validate_json(json.dumps({
        'plan_id': plan.plan_id, 'corpus_sha256': plan.corpus_sha256,
        'question_sha256': hashlib.sha256(plan.query.encode()).hexdigest(),
        'bindings_sha256': bindings_hash(BINDINGS),
        'declaration_ref': 'Synthetic caller-declared scope, not owner acceptance',
        'annotations': [{'component_id': 'r1', 'subtask_id': f's0{i}', 'question_span': None if unresolved else
            {'start': plan.query.index(text), 'end': plan.query.index(text) + len(text)}}
            for i, text in enumerate(spans, 1)]}))


def fixture(tmp_path, *, optional=False, empty=False):
    path = tmp_path / 'corpus.json'
    path.write_text(json.dumps([{'feed_id': 'solar', 'title': 'Solar', 'clean_content': FACT}]), encoding='utf-8')
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    plan = Plan(query=QUESTION, corpus_sha256=sha, subtasks=(
        Subtask(subtask_id='s01', operation='retrieve', query='unknownsolar' if empty else 'solar'),
        Subtask(subtask_id='s02', operation='retrieve', query='unknowntariffs', required=not optional)))
    report = run_plan(plan, 'a'*32, 'b'*32, LocalBM25Adapter(path))
    return path, plan, report


@dataclass
class FixedScoped:
    mode: str = 'partial'

    def __call__(self, stage, schema, instruction, inputs):
        if stage == 'mapping':
            assert 'question_spans' not in inputs
            assert 'requested_branch_scopes' in inputs
            span_ids = [s['span_id'] for record in inputs['evidence'] for s in record['spans']]
            parsed = {'wire_version': WIRE_VERSION, 'components': [{'component_id': 'r1',
                'status': 'missing' if self.mode == 'missing' else 'supported' if self.mode == 'supported' else 'conflicting' if self.mode == 'conflicting' else 'partial',
                'evidence': [] if self.mode == 'missing' else span_ids}],
                'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'Fixed offline fixture.'}}
            if self.mode == 'gap_injection':
                parsed['components'][0]['gap'] = {'start': 0, 'end': 8}
            if self.mode == 'action_injection':
                parsed['approve_export'] = True
            if self.mode == 'old_wire':
                parsed['wire_version'] = 'cq-question-span-v1'
            if self.mode == 'unknown_source':
                parsed['components'][0]['evidence'] = ['invented']
            if self.mode == 'duplicate_source':
                parsed['components'][0]['evidence'] *= 2
            if self.mode == 'supported_omission':
                parsed['components'][0]['status'] = 'supported'
            if self.mode == 'malformed':
                return {'parsed': None, 'raw': '{broken'}
        else:
            parsed = {'title': 'Analyst research brief', 'claims': [{'component_id': u['component_id'],
                'unit_id': u['unit_id'], 'text': u['evidence'][0]['quote']} for u in inputs['units']]}
            if self.mode == 'fallback':
                parsed['claims'] = []
            if self.mode == 'wrong_number':
                parsed['claims'][0]['text'] = FACT.replace('12%', '82%')
            if self.mode == 'reordered_scope':
                parsed['claims'][0]['text'] = REORDERED_FACT
        return {'parsed': parsed, 'raw': json.dumps(parsed), 'usage': None}


def compose(plan, report, *, mode='partial', scope=None):
    access = ModelAccess(time.monotonic() + 30)
    captured = []
    callback = ScopedConcurrentComposer(plan, BINDINGS, '2026-11-07', FixedScoped(mode),
        scope or scopes(plan), capture=captured.append, complete_required_branches=BINDINGS)
    return callback, access, captured


@pytest.mark.parametrize(('mode', 'claim'), [('partial', FACT), ('reordered_scope', REORDERED_FACT)])
def test_partial_uses_explicit_requested_scope_and_preserves_supported_fact(tmp_path, mode, claim):
    _, plan, report = fixture(tmp_path)
    callback, access, captured = compose(plan, report, mode=mode)
    result = callback(report, access)
    assert result.draft['claims'][0]['text'] == claim
    assert result.diagnostics['fallback_unit_ids'] == []
    assert access.calls == 2 and access.guards == 0 and not result.safety_passed
    warning = next(w for w in result.draft['warnings'] if 'Subtask s02' in w)
    assert 'Chile retail gas tariffs today' in warning and QUESTION in warning
    assert 'does not establish absence in the database' in warning
    assert not any('do not establish the following' in w for w in result.draft['warnings'])
    raw = result.diagnostics['scoped_mapper_raw_selection']['components'][0]
    assert 'gap' not in raw and 'gap_anchor' not in raw
    assert 'gap_anchor' in result.diagnostics['application_source_selection']['components'][0]
    assert all('gap_anchor' not in json.loads(r['raw'])['components'][0] for r in captured if r['stage'] == 'mapping')
    assert result.diagnostics['scoped_disclosures']['semantic_support_proven'] is False
    assert result.diagnostics['scoped_disclosures']['owner_acceptance'] == 'not inferred'


@pytest.mark.parametrize('damage', ['plan', 'corpus', 'question', 'bindings', 'duplicate', 'missing', 'bounds', 'boolean', 'unknown', 'blank_ref'])
def test_scope_contract_failure_starts_zero_model_calls(tmp_path, damage):
    _, plan, report = fixture(tmp_path)
    value = scopes(plan).model_dump(mode='json')
    key = {'plan': 'plan_id', 'corpus': 'corpus_sha256', 'question': 'question_sha256', 'bindings': 'bindings_sha256'}.get(damage)
    if key:
        value[key] = 'f'*64
    elif damage == 'duplicate':
        value['annotations'][1] = value['annotations'][0]
    elif damage == 'missing':
        value['annotations'].pop()
    elif damage == 'unknown':
        value['annotations'][1]['subtask_id'] = 's05'
    elif damage == 'blank_ref':
        value['declaration_ref'] = ' '
    else:
        value['annotations'][1]['question_span']['start'] = True if damage == 'boolean' else 500
    access = ModelAccess(time.monotonic() + 30)
    with pytest.raises(ValueError):
        contract = DisclosureScopes.model_validate_json(json.dumps(value))
        ScopedConcurrentComposer(plan, BINDINGS, '2026-11-07', FixedScoped(), contract)(report, access)
    assert access.calls == 0


@pytest.mark.parametrize('mode', ['gap_injection', 'action_injection', 'old_wire', 'unknown_source', 'duplicate_source', 'supported_omission', 'malformed'])
def test_invalid_mapper_stops_without_composer_or_repair(tmp_path, mode):
    _, plan, report = fixture(tmp_path)
    callback, access, captured = compose(plan, report, mode=mode)
    with pytest.raises(ValueError):
        callback(report, access)
    assert access.calls == 1 and access.guards == 0
    assert [r['stage'] for r in captured] == ['mapping']


def test_missing_all_uses_one_call_and_exact_no_information_policy(tmp_path):
    from src.pilot._evidence import NO_INFORMATION
    _, plan, report = fixture(tmp_path, empty=True)
    callback, access, _ = compose(plan, report, mode='missing')
    result = callback(report, access)
    assert result.draft['claims'] == [] and access.calls == 1 and access.guards == 0
    assert result.draft['warnings'][0] == NO_INFORMATION


def test_fallback_is_labeled_and_wrong_numbers_still_fail(tmp_path):
    _, plan, report = fixture(tmp_path)
    callback, access, _ = compose(plan, report, mode='fallback')
    result = callback(report, access)
    assert result.draft['claims'][0]['text'] == FACT and result.diagnostics['fallback_unit_ids']
    assert result.diagnostics['raw_composer_output']['claims'] == ()
    assert json.loads(result.diagnostics['model_responses'][1]['raw'])['claims'] == []
    assert any('verbatim' in w for w in result.draft['warnings'])
    callback, access, _ = compose(plan, report, mode='wrong_number')
    with pytest.raises(ValueError):
        callback(report, access)


def test_explicit_null_scope_remains_honestly_unresolved(tmp_path):
    _, plan, report = fixture(tmp_path)
    callback, access, _ = compose(plan, report, scope=scopes(plan, unresolved=True))
    result = callback(report, access)
    assert any('requested scope not established' in w for w in result.draft['warnings'])
    assert result.draft['claims'][0]['text'] == FACT


def test_complete_evidence_has_no_required_branch_gap(tmp_path):
    path, _, _ = fixture(tmp_path)
    plan = Plan(query='Describe solar generation in Chile in 2012.',
        corpus_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), subtasks=(Subtask(subtask_id='s01', operation='retrieve', query='solar'),))
    bindings = {'r1': ['s01']}
    contract = DisclosureScopes.model_validate_json(json.dumps({'plan_id': plan.plan_id,
        'corpus_sha256': plan.corpus_sha256, 'question_sha256': hashlib.sha256(plan.query.encode()).hexdigest(),
        'bindings_sha256': bindings_hash(bindings), 'declaration_ref': 'Synthetic complete task',
        'annotations': [{'component_id': 'r1', 'subtask_id': 's01', 'question_span': {'start': 0, 'end': len(plan.query)}}]}))
    report = run_plan(plan, 'a'*32, 'b'*32, LocalBM25Adapter(path))
    access = ModelAccess(time.monotonic()+30)
    result = ScopedConcurrentComposer(plan, bindings, '2026-11-07', FixedScoped('supported'), contract,
        complete_required_branches=bindings)(report, access)
    assert result.draft['claims'][0]['text'] == FACT
    assert result.diagnostics['scoped_disclosures']['warnings'] == []
    assert result.diagnostics['scoped_disclosures']['semantic_support_proven'] is False


def test_valid_scope_membership_does_not_become_semantic_acceptance(tmp_path):
    _, plan, report = fixture(tmp_path)
    value = scopes(plan).model_dump(mode='json')
    start = QUESTION.index(' and ')+1
    value['annotations'][1]['question_span'] = {'start': start, 'end': start+3}
    contract = DisclosureScopes.model_validate_json(json.dumps(value))
    callback, access, _ = compose(plan, report, scope=contract)
    result = callback(report, access)
    record = result.diagnostics['scoped_disclosures']['records'][1]
    assert record['requested_scope'] == 'and' and record['scope_semantics_proven'] is False
    assert result.diagnostics['scoped_disclosures']['owner_acceptance'] == 'not inferred'


def test_required_failure_is_diagnostic_only_and_never_authorizes_drafting(tmp_path):
    _, plan, report = fixture(tmp_path)
    callback, access, _ = compose(plan, report)
    result = callback(report, access)
    mapping = ResolvedEvidenceMap.model_validate_json(json.dumps(result.diagnostics['resolved_evidence_mapping']))
    first = report.results[0]
    failed = replace(report, status='failed', states=(('s01', 'completed'), ('s02', 'failed')),
        results=(first,), sources=aggregate((first,)), missing_branches=('s02',), can_compose=False)
    projection = project_disclosures(plan, failed, mapping, BINDINGS, scopes(plan))
    assert not projection['drafting_allowed']
    assert any('unverified' in w for w in projection['warnings'])
    callback, access, _ = compose(plan, failed)
    with pytest.raises(ValueError, match='drafting blocked'):
        callback(failed, access)
    assert access.calls == 0


def test_dependency_result_hash_is_checked_before_model_calls(tmp_path):
    path, base, _ = fixture(tmp_path)
    plan = base.model_copy(update={'subtasks': (base.subtasks[0], base.subtasks[1].model_copy(update={'dependencies': ('s01',)}))})
    report = run_plan(plan, 'a'*32, 'b'*32, LocalBM25Adapter(path))
    callback, access, _ = compose(plan, report)
    assert callback(report, access).draft['claims'][0]['text'] == FACT
    first, second = report.results
    dependency = second.dependencies[0].model_copy(update={'result_sha256': 'f'*64})
    changed = replace(report, results=(first, second.model_copy(update={'dependencies': (dependency,)})))
    callback, access, _ = compose(plan, changed)
    with pytest.raises(ValueError, match='dependency result lineage'):
        callback(changed, access)
    assert access.calls == 0


def test_mapper_conflict_is_not_hidden_by_a_separate_missing_branch(tmp_path):
    path, _, _ = fixture(tmp_path)
    records = [{'feed_id': 'solar12', 'clean_content': FACT},
        {'feed_id': 'solar14', 'clean_content': FACT.replace('12%', '14%')}]
    path.write_text(json.dumps(records), encoding='utf-8')
    plan = Plan(query=QUESTION, corpus_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), subtasks=(
        Subtask(subtask_id='s01', operation='retrieve', query='solar'),
        Subtask(subtask_id='s02', operation='retrieve', query='unknowntariffs')))
    report = run_plan(plan, 'a'*32, 'b'*32, LocalBM25Adapter(path))
    # Retrieval reports evidence; the fixed mapper separately marks its selected
    # passages conflicting. Missing tariffs must not hide that conflict signal.
    assert report.results[0].outcome == 'evidence'
    callback, access, _ = compose(plan, report, mode='conflicting')
    result = callback(report, access)
    assert result.draft['claims'] == [] and access.calls == 1
    assert any('Subtask s02' in warning for warning in result.draft['warnings'])
    assert any('conflicting' in warning for warning in result.draft['warnings'])


@pytest.mark.parametrize('outcome', ['unselected', 'conflicting', 'failed', 'cancelled', 'blocked'])
def test_real_report_diagnostic_distinctions_and_optional_policy(tmp_path, outcome):
    _, plan, report = fixture(tmp_path, optional=True)
    callback, access, _ = compose(plan, report)
    result = callback(report, access)
    mapping = ResolvedEvidenceMap.model_validate_json(json.dumps(result.diagnostics['resolved_evidence_mapping']))
    first, second = report.results
    if outcome in {'failed', 'cancelled', 'blocked'}:
        changed = replace(report, status='partial', states=(('s01', 'completed'), ('s02', outcome)),
            results=(first,), sources=aggregate((first,)), missing_branches=('s02',))
    else:
        second = second.model_copy(update={'outcome': 'conflicting' if outcome == 'conflicting' else 'evidence',
            'sources': tuple(s.model_copy(update={'source_id': 'other'}) for s in first.sources)})
        changed = replace(report, results=(first, second), sources=aggregate((first, second)))
    projection = project_disclosures(plan, changed, mapping, BINDINGS, scopes(plan))
    item = projection['records'][1]
    expected = {'unselected': 'unselected_evidence', 'conflicting': 'reported_conflict',
        'failed': 'unverified_execution', 'cancelled': 'unverified_execution', 'blocked': 'unverified_execution'}[outcome]
    assert item['kind'] == expected
    assert not any('Subtask s02' in warning for warning in projection['warnings'])
    # A model-declared partial component stays partial even when its unselected
    # branch is optional. Do not erase this separate completeness limitation.
    assert any('Component r1 remains partial' in warning for warning in projection['warnings'])


@pytest.mark.parametrize('damage', ['plan_identity', 'source_hash', 'aggregate', 'state', 'attempt', 'order'])
def test_report_tampering_fails_before_model_calls(tmp_path, damage):
    _, plan, report = fixture(tmp_path)
    if damage == 'plan_identity':
        report = replace(report, identity=report.identity.model_copy(update={'plan_id': 'f'*64}))
    elif damage == 'source_hash':
        first = report.results[0]
        source = first.sources[0].model_copy(update={'content': 'Modified source'})
        report = replace(report, results=(first.model_copy(update={'sources': (source,)}), report.results[1]))
    elif damage == 'aggregate':
        report = replace(report, sources=())
    elif damage == 'state':
        report = replace(report, states=(('s01', 'running'), ('s02', 'completed')))
    elif damage == 'attempt':
        report = replace(report, results=(report.results[0], report.results[1].model_copy(update={'child_attempt_id': report.results[0].child_attempt_id})))
    else:
        report = replace(report, results=tuple(reversed(report.results)))
    callback, access, _ = compose(plan, report)
    with pytest.raises(ValueError):
        callback(report, access)
    assert access.calls == 0


def allow(draft, sources):
    return True


def deny(draft, sources):
    return False


@pytest.mark.parametrize('safety', [allow, deny])
def test_existing_runner_safety_and_exact_revision_lifecycle(tmp_path, safety):
    path, plan, _ = fixture(tmp_path)
    store = Store(tmp_path/'history.sqlite3')
    rid, _ = store.create(ResearchRequest(query=QUESTION, request_key='scoped-case'), plan.corpus_sha256)
    callback = ScopedConcurrentComposer(plan, BINDINGS, '2026-11-07', FixedScoped(), scopes(plan), complete_required_branches=BINDINGS)
    if safety is deny:
        with pytest.raises(ValueError, match='Worker failed'):
            run_stored_plan(store, rid, plan, path, LocalBM25Adapter(path), callback, safety)
        row = store.get(rid)
        assert row['draft'] is None and row['status'] != 'needs_review'
        with pytest.raises(Conflict):
            store.export(rid)
        return
    run_stored_plan(store, rid, plan, path, LocalBM25Adapter(path), callback, safety)
    row = store.get(rid)
    assert row['status'] == 'needs_review'
    assert row['metrics']['model_calls'] == 2 and row['metrics']['guardrail_invocations'] == 1
    assert row['metrics']['composition_diagnostics']['scoped_disclosures']['scope_contract']['plan_id'] == plan.plan_id
    with pytest.raises(Conflict):
        store.export(rid)
    store.review(rid, ReviewRequest(revision=1, decision='approve', reviewer='synthetic-test', support_confirmed=True))
    exported = store.export(rid)
    assert store.export(rid) == exported
    store.save_draft(rid, row['draft'], row['sources'], {}, expected_revision=1)
    with pytest.raises(Conflict):
        store.export(rid)
