"""Synthetic scope metadata only; no actual generation, labels or grants."""
import hashlib
import json
from pathlib import Path

import pytest
from test_builder import setup, write
from build_qualification import scoped_cases, build
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
from src.pilot.subtasks._development_lineage import canonical_hash
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest


def package(tmp_path):
    args=setup(tmp_path)
    plans=json.loads((args['pool']/'plans.json').read_text())
    cases={cid:{k:entry[k] for k in ('plan','bindings','corpus_path','complete_required_branches')} for cid,entry in plans.items()}
    folder=tmp_path/'scope-data';folder.mkdir()
    bundle={'version':'cq1-requested-scopes-v1','pool_manifest_sha256':args['expected_pool_sha256'],
        'plans_sha256':args['expected_plans_sha256'],'case_ids':list(cases),'cases':{}}
    for cid,case in cases.items():
        plan=Plan.model_validate_json(json.dumps(case['plan']))
        scope=DisclosureScopes.model_validate_json(json.dumps({'plan_id':plan.plan_id,'corpus_sha256':plan.corpus_sha256,
            'question_sha256':hashlib.sha256(plan.query.encode()).hexdigest(),'bindings_sha256':bindings_hash(case['bindings']),
            'declaration_ref':'SYNTHETIC CALLER DATA; no owner review',
            'annotations':[{'component_id':'r1','subtask_id':'s01','question_span':{'start':0,'end':len(plan.query)}}]}))
        path=folder/(cid+'.json');path.write_text(scope.model_dump_json())
        bundle['cases'][cid]={'path':path.name,'sha256':digest(path)}
    manifest=folder/'manifest.json';write(manifest,bundle)
    return args,cases,manifest,bundle


def test_all_twenty_cases_retain_pinned_question_scope_metadata(tmp_path):
    args,cases,manifest,_=package(tmp_path)
    output,inputs=scoped_cases(cases,manifest,digest(manifest),args['expected_pool_sha256'],args['expected_plans_sha256'])
    assert len(output)==20 and len(inputs)==21 and list(output)==list(cases)
    assert all(inputs[row['requested_scopes']]==row['requested_scopes_sha256'] for row in output.values())
    assert all('required_findings' not in row for row in output.values())
    assert not args['destination'].exists() and not args['output_directory'].exists()


@pytest.mark.parametrize('damage',['manifest_hash','pool','plans','order','missing_case','scope_identity','changed_scope','escape'])
def test_scope_roster_identity_and_paths_fail_closed(tmp_path,damage):
    args,cases,manifest,bundle=package(tmp_path);original=digest(manifest)
    cid=next(iter(cases));entry=bundle['cases'][cid];path=manifest.parent/entry['path']
    if damage=='manifest_hash':
        manifest.write_text(manifest.read_text()+' ')
    elif damage=='pool':bundle['pool_manifest_sha256']='f'*64
    elif damage=='plans':bundle['plans_sha256']='f'*64
    elif damage=='order':bundle['case_ids'].reverse()
    elif damage=='missing_case':bundle['cases'].pop(cid)
    elif damage=='scope_identity':
        scope=json.loads(path.read_text());scope['plan_id']='f'*64;write(path,scope);entry['sha256']=digest(path)
    elif damage=='changed_scope':path.write_text(path.read_text()+' ')
    else:entry['path']='../../outside.json'
    if damage!='manifest_hash':write(manifest,bundle);original=digest(manifest)
    with pytest.raises((ValueError,FileNotFoundError)):
        scoped_cases(cases,manifest,original,args['expected_pool_sha256'],args['expected_plans_sha256'])
    assert not args['destination'].exists()


def test_scoped_development_cannot_compile_without_scope_manifest(tmp_path):
    args=setup(tmp_path);dev=json.loads(args['development_path'].read_text())
    dev['composition_contract']='cq-scoped-composition-v1';dev['contract_sha256']=canonical_hash(dev)
    write(args['development_path'],dev);args['expected_identity']=dev['contract_sha256']
    with pytest.raises(ValueError,match='requires a frozen scope manifest'):
        build(**args)
    assert not args['destination'].exists()


def test_positive_scoped_compilation_retains_all_sidecars_and_new_grant_scope(tmp_path):
    args,_,manifest,_=package(tmp_path)
    dev=json.loads(args['development_path'].read_text())
    dev['composition_contract']='cq-scoped-composition-v1'
    dev['authorization_reply']='DEVELOPMENT ONLY; must not be inherited as qualification approval'
    for cid,entry in dev['cases'].items():
        plan=Plan.model_validate_json(json.dumps(entry['plan']))
        entry['bindings']={'r1':[task.subtask_id for task in plan.subtasks]}
        scope=DisclosureScopes.model_validate_json(json.dumps({'plan_id':plan.plan_id,
            'corpus_sha256':plan.corpus_sha256,'question_sha256':hashlib.sha256(plan.query.encode()).hexdigest(),
            'bindings_sha256':bindings_hash(entry['bindings']),'declaration_ref':'SYNTHETIC METADATA ONLY',
            'annotations':[{'component_id':'r1','subtask_id':task.subtask_id,
                'question_span':{'start':0,'end':len(plan.query)}} for task in plan.subtasks]}))
        path=args['development_path'].parent/(cid+'.scope.json');path.write_text(scope.model_dump_json())
        entry.update(requested_scopes=str(path),requested_scopes_sha256=digest(path))
        dev['input_sha256'][str(path)]=digest(path)
    dev['contract_sha256']=canonical_hash(dev);write(args['development_path'],dev)
    args['expected_identity']=dev['contract_sha256']
    for cid in dev['case_ids']:
        write(args['development_path'].parent/(cid+'.started.json'),{'case_id':cid,'contract_sha256':dev['contract_sha256']})
    c=build(**args,scope_manifest_path=manifest,expected_scopes_sha256=digest(manifest))
    assert len(c['cases'])==20 and c['execution_authorized'] is False
    assert c['authorization_reply']=='Authorize CQ1 scoped twenty-case qualification'
    assert all(c['input_sha256'][entry['requested_scopes']]==entry['requested_scopes_sha256'] for entry in c['cases'].values())
    assert c['requested_scope_manifest_sha256']==digest(manifest)
    assert not args['output_directory'].exists()
