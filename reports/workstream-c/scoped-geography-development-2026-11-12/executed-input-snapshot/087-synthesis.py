"""Opt-in synthesis boundary over A's aggregate; no inference or persistence."""
import copy
import re
from dataclasses import dataclass
from .contracts import Plan, Result
from .scheduler import Report, aggregate
from .._evidence import validate_mapping, unavailable_draft, evidence_gaps, EvidenceQuote
from .._composition import project, composition_units, response_schema
from .._scope import validate_claim_measure_and_numbers
from ..schemas import Draft
from ._relationships import validate_relationships
from ._title_scope import qualify_title


@dataclass(frozen=True)
class SynthesisResult:
    draft: dict
    provenance: tuple
    diagnostics: dict
    safety_passed: bool = False
    guarded_sha256: str = ""


def project_report(plan: Plan, report: Report, mapping, composed, bindings, *, as_of,
                   is_current, geographic_resolution=None, disclosure_scopes=None):
    """Caller provides mapped selection and composition; these are not trusted facts.

    bindings maps every requested component to its declared branch IDs. This returns
    a safety-pending projection; caller must validate safety before persistence.
    """
    plan = Plan.model_validate_json(plan.model_dump_json())
    if not is_current(): raise ValueError('Stale or cancelled synthesis attempt')
    if report.identity.plan_id != plan.plan_id or report.identity.corpus_sha256 != plan.corpus_sha256:
        raise ValueError('Aggregate identity mismatch')
    states = dict(report.states)
    declared = {s.subtask_id for s in plan.subtasks}
    required_unavailable = [s.subtask_id for s in plan.subtasks if s.required and states.get(s.subtask_id) != "completed"]
    if required_unavailable:
        raise ValueError("Required branch unavailable; drafting blocked: " + ", ".join(required_unavailable))
    if set(states) != declared or len(report.states) != len(declared) or report.status not in {"completed","partial"}:
        raise ValueError("Aggregate terminal state mismatch")
    if report.sources != aggregate(report.results):
        raise ValueError("Aggregate sources disagree with branch results")
    if not report.can_compose or any(s.required and states.get(s.subtask_id) != 'completed' for s in plan.subtasks):
        raise ValueError('Required branch unavailable; drafting blocked: ' + ', '.join(s.subtask_id for s in plan.subtasks if s.required and states.get(s.subtask_id) != 'completed'))
    if any(states.get(s.subtask_id) not in {'completed','failed','cancelled','blocked'} for s in plan.subtasks):
        raise ValueError('Branches are not terminal')
    results = {}
    sources = {}
    for raw in report.results:
        result = Result.model_validate_json(raw.model_dump_json())
        if result.identity != report.identity or result.subtask_id not in declared or result.subtask_id in results or states.get(result.subtask_id) != 'completed':
            raise ValueError('Invalid branch result identity or state')
        results[result.subtask_id] = result
        for source in result.sources:
            record = source.model_dump(exclude={'role'})
            if source.source_id in sources and sources[source.source_id] != record:
                raise ValueError('Source collision')
            sources[source.source_id] = record
    if any(states.get(s.subtask_id)=='completed' and s.subtask_id not in results for s in plan.subtasks):
        raise ValueError('Completed branch has no result')
    if len({r.child_attempt_id for r in results.values()}) != len(results):
        raise ValueError("Duplicate child attempt identity")
    if tuple(results) != tuple(s.subtask_id for s in plan.subtasks if s.subtask_id in results):
        raise ValueError("Results are not in declared plan order")
    selected = validate_mapping(mapping, plan.query, sources, as_of)
    if set(bindings) != {c.component_id for c in selected.components}:
        raise ValueError('Every component requires an explicit branch binding')
    declared = {s.subtask_id for s in plan.subtasks}
    if set().union(*(set(b) for b in bindings.values())) != declared:
        raise ValueError('Unbound branch coverage would be omitted')
    for component in selected.components:
        branches = bindings[component.component_id]
        if not branches or len(set(branches)) != len(branches) or not set(branches) <= declared:
            raise ValueError('Invalid component branch binding')
        allowed = {s.source_id for bid in branches if bid in results and results[bid].outcome in ({'evidence','conflicting'} if component.status=='conflicting' else {'evidence'})
                   for s in results[bid].sources if s.role=='support'}
        if any(e.source_id not in allowed for e in component.evidence):
            raise ValueError('Component evidence crosses branch or support boundary')
        if component.status in {'supported','partial'} and not component.evidence:
            raise ValueError('Supported component lacks evidence')
    diagnostics = {'identity':report.identity.model_dump(), 'raw_composer_output':copy.deepcopy(composed), 'editorial_correction':False,
                   'branch_states':states, 'missing_branches':list(report.missing_branches)}
    supported = [c for c in selected.components if c.status in {'supported','partial'}]
    if supported:
        parsed = response_schema(selected).model_validate(composed)
        units = {u['unit_id']:u for u in composition_units(selected)}
        components = {c.component_id:c for c in selected.components}
        for claim in parsed.claims:
            unit = units[claim.unit_id]
            component = components[unit['component_id']].model_copy(update={'evidence':[
                EvidenceQuote.model_validate(e) for e in unit['evidence']]})
            validate_claim_measure_and_numbers(claim.text, component, plan.query)
            validate_relationships(claim.text, component.evidence)
            quoted = ' '.join(e.quote for e in component.evidence)
            projected = bool(re.search(r'\b(?:forecast|projected)\b',quoted,re.I))
            observed = bool(re.search(r'\b(?:observed|recorded)\b',quoted,re.I))
            assertion_projected = bool(re.search(r'\b(?:forecast|projected)\b',claim.text,re.I))
            if projected != observed and assertion_projected != projected:
                raise ValueError('Observation/forecast basis mismatch')
        draft, fallback = project(composed, selected, plan.query, {}, diagnostics, source_records=sources)
        diagnostics['fallback_unit_ids'] = fallback
    else:
        draft = unavailable_draft(evidence_gaps(selected, plan.query))
        diagnostics['fallback_unit_ids'] = []
    warnings = [f'Subtask {s.subtask_id} did not complete ({states[s.subtask_id]}); its requested coverage is unresolved.'
                for s in plan.subtasks if states[s.subtask_id] != 'completed']
    for bid, result in results.items():
        if result.outcome in {'missing','conflicting'}:
            anchors = list(dict.fromkeys(c.question_anchor for c in selected.components if bid in bindings[c.component_id]))
            warnings.append(f'Subtask {bid} returned {result.outcome} evidence for: ' + '; '.join(anchors))
    if disclosure_scopes is not None:
        from ._disclosures import project_disclosures
        projection = project_disclosures(plan, report, selected, bindings, disclosure_scopes)
        # Replace only the known legacy gap messages; retain fallback, geographic,
        # period and no-information messages. Never let the composer write gaps.
        legacy_gaps = set(evidence_gaps(selected, plan.query))
        draft['warnings'] = [w for w in draft['warnings'] if w not in legacy_gaps]
        warnings = projection['warnings']
        diagnostics['scoped_disclosures'] = projection
    if len(draft['warnings']) + len(warnings) > 10:
        raise ValueError('Warning capacity exceeded; no silent truncation')
    draft['warnings'] += warnings
    provenance = []
    for coverage in diagnostics.get('public_claim_coverage',[]):
        origins = []
        for uid in coverage['unit_ids']:
            unit = next(u for u in composition_units(selected) if u['unit_id']==uid)
            for evidence in unit['evidence']:
                for bid in bindings[unit['component_id']]:
                    result = results.get(bid)
                    if result:
                        for source in result.sources:
                            if source.source_id==evidence['source_id'] and source.role=='support':
                                origins.append({'unit_id':uid,'component_id':unit['component_id'],'subtask_id':bid,
                                    'child_attempt_id':result.child_attempt_id,'source_id':source.source_id,
                                    'content_sha256':source.content_sha256,'corpus_sha256':source.corpus_sha256})
        provenance.append({'claim_index':coverage['claim_index'],'origins':origins})
    if supported and draft['claims']:
        draft, title_scope = qualify_title(draft, parsed.title, selected, sources, geographic_resolution)
        diagnostics['title_geography'] = title_scope
    draft = Draft.model_validate(draft).model_dump()
    if not is_current(): raise ValueError('Stale or cancelled synthesis attempt')
    return SynthesisResult(draft, tuple(provenance), diagnostics)


def _guard_fingerprint(report, result):
    import hashlib
    import json
    value = {'draft':result.draft, 'provenance':result.provenance,
        'diagnostics':result.diagnostics, 'sources':[r.model_dump(mode='json') for r in report.results]}
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def compose_report(plan, report, mapping, composed, bindings, *, as_of, guard, is_current):
    result = project_report(plan, report, mapping, composed, bindings, as_of=as_of, is_current=is_current)
    fingerprint = _guard_fingerprint(report, result)
    sources = {s.source_id:s.content for r in report.results for s in r.sources}
    if result.draft['claims']:
        verdict = guard.validate_output(user_input=plan.query, raw_report='\n'.join(c['text'] for c in result.draft['claims']),
            context='\n'.join(sources.values()))
        if verdict.get('passed_guardrails') is not True: raise ValueError('Final safety check failed')
    if not is_current(): raise ValueError('Stale or cancelled synthesis attempt')
    return SynthesisResult(result.draft, result.provenance, result.diagnostics, True, fingerprint)


def persist_synthesis(store, report, result):
    """Persist a guarded candidate and its lineage using existing fenced Store APIs.

    The event is a candidate artifact, never an approval or proof of publication.
    Store.save_draft rechecks the attempt atomically before publishing the revision.
    """
    import hashlib
    import json
    if not result.safety_passed or result.diagnostics.get('identity') != report.identity.model_dump():
        raise ValueError('Guarded synthesis identity required')
    if not result.guarded_sha256 or result.guarded_sha256 != _guard_fingerprint(report, result):
        raise ValueError('Guarded synthesis changed after safety validation')
    row = store.get(report.identity.run_id)
    if row['corpus_sha'] != report.identity.corpus_sha256:
        raise ValueError('Stored corpus differs from synthesis')
    sources = {s.source_id:s.model_dump(exclude={'role'}) for r in report.results for s in r.sources}
    fingerprint = hashlib.sha256((json.dumps(result.draft,ensure_ascii=False)+json.dumps(sources,ensure_ascii=False)).encode()).hexdigest()
    artifact = {'status':'candidate; publication and approval are separate',
        'draft_sources_sha256':fingerprint, 'identity':report.identity.model_dump(),
        'claim_provenance':list(result.provenance), 'diagnostics':result.diagnostics}
    if not store.attempt_event(report.identity.run_id, report.identity.attempt_id, 'composition_candidate', artifact):
        raise ValueError('Stale synthesis cannot be persisted')
    return store.save_draft(report.identity.run_id, result.draft, sources,
        {'composition_provenance':list(result.provenance),'composition_diagnostics':result.diagnostics},
        attempt_id=report.identity.attempt_id)
