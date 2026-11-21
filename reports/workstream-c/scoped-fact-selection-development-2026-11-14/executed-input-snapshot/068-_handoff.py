"""Private typed composition boundary and exact-content candidate fingerprints."""
import hashlib
import json


def snapshot(value):
    """Detach mutable callback state and reject non-JSON/NaN values."""
    return json.loads(json.dumps(value,ensure_ascii=False,allow_nan=False))


def fingerprint(draft,sources,lineage):
    payload={'draft':draft,'sources':sources,'lineage':lineage}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,
        allow_nan=False,separators=(',',':')).encode('utf-8')).hexdigest()


def seal(draft,sources,lineage,identity):
    """Build a detached candidate artifact, never approval or publication proof."""
    from .contracts import Identity
    identity=Identity.model_validate_json(json.dumps(identity)).model_dump()
    if not isinstance(lineage,dict) or set(lineage)!={'identity','claim_provenance','diagnostics'}:
        raise ValueError('Malformed candidate lineage')
    if not isinstance(lineage['diagnostics'],dict) or not isinstance(lineage['claim_provenance'],list):
        raise ValueError('Malformed candidate attribution')
    if lineage['identity']!=identity or lineage['diagnostics'].get('identity')!=identity:
        raise ValueError('Candidate lineage identity mismatch')
    return snapshot({'status':'candidate; publication and approval are separate',
        'identity':identity,'claim_provenance':lineage['claim_provenance'],
        'diagnostics':lineage['diagnostics'],
        'draft_sources_sha256':fingerprint(draft,sources,None),
        'content_sha256':fingerprint(draft,sources,lineage)})


def verify_seal(draft,sources,artifact,identity):
    """Parent-side consistency check of exact transported guarded content."""
    if not isinstance(artifact,dict) or set(artifact)!={
            'status','identity','claim_provenance','diagnostics','draft_sources_sha256','content_sha256'}:
        raise ValueError('Malformed composition candidate')
    if artifact['status']!='candidate; publication and approval are separate':
        raise ValueError('Invalid composition candidate status')
    lineage={k:artifact[k] for k in ('identity','claim_provenance','diagnostics')}
    expected=seal(draft,sources,lineage,identity)
    if artifact!=expected:raise ValueError('Composition candidate content changed')
    return snapshot(lineage)


def prepare(value,report):
    """Accept old dictionaries or unguarded typed composition from this Report.

    Validates attribution identities, not semantic entailment. No safety call,
    persistence or model call is performed here.
    """
    from .synthesis import SynthesisResult
    if isinstance(value,dict):return snapshot(value),None
    if not isinstance(value,SynthesisResult):raise ValueError('Unsupported composition result')
    if value.safety_passed is not False or value.guarded_sha256!='':
        raise ValueError('Runner requires an unguarded composition result')
    if not isinstance(value.diagnostics,dict) or not isinstance(value.draft,dict):
        raise ValueError('Malformed composition result')
    if value.diagnostics.get('identity')!=report.identity.model_dump():
        raise ValueError('Composition identity differs from active report')
    from src.pilot.schemas import Draft
    draft=snapshot(Draft.model_validate(value.draft).model_dump())
    lineage=snapshot({'identity':report.identity.model_dump(),
        'claim_provenance':value.provenance,'diagnostics':value.diagnostics})
    if not isinstance(draft.get('claims'),list) or not isinstance(lineage['claim_provenance'],list):
        raise ValueError('Malformed composition claims or lineage')
    accepted={(r.subtask_id,r.child_attempt_id,s.source_id,s.content_sha256,s.corpus_sha256)
        for r in report.results for s in r.sources if s.role=='support'}
    indices=[]
    for claim in lineage['claim_provenance']:
        if not isinstance(claim,dict):raise ValueError('Malformed claim lineage')
        index=claim.get('claim_index')
        if type(index) is not int or not 0<=index<len(draft['claims']):
            raise ValueError('Invalid lineage claim index')
        indices.append(index)
        if not isinstance(claim.get('origins'),list) or not claim['origins']:
            raise ValueError('Claim lineage has no origin')
        for origin in claim['origins']:
            if not isinstance(origin,dict):raise ValueError('Malformed lineage origin')
            if not all(isinstance(origin.get(k),str) for k in
                    ('subtask_id','child_attempt_id','source_id','content_sha256','corpus_sha256')):
                raise ValueError('Malformed lineage identity')
            key=tuple(origin.get(k) for k in ('subtask_id','child_attempt_id','source_id','content_sha256','corpus_sha256'))
            if key not in accepted or origin['source_id'] not in draft['claims'][index]['source_ids']:
                raise ValueError('Lineage source differs from accepted evidence')
            if not all(isinstance(origin.get(k),str) and origin[k].strip() for k in ('unit_id','component_id')):
                raise ValueError('Lineage lacks evidence-unit identity')
    if sorted(indices)!=list(range(len(draft['claims']))):
        raise ValueError('Composition lineage must cover every claim exactly once')
    return draft,lineage
