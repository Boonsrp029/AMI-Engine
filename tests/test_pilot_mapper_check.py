"""Offline orchestration gates; all service processes are synthetic or mocked."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import pilot_mapper_check as check
from scripts._mapper_transport import request_body, sha, write_json


def fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path/'evidence'; root.mkdir()
    proposal = root/'proposal'; proposal.mkdir()
    package = tmp_path/'data'/'frozen'; package.mkdir(parents=True)
    (package/'corpus.json').write_text('synthetic corpus', encoding='utf-8')
    (package.parent/'source.txt').write_text('Pinned source.', encoding='utf-8')
    write_json(package/'sources.json', {'source':{'file':'source.txt','sha256':sha(package.parent/'source.txt')}})
    write_json(package/'manifest.json', {'sha256':{n:sha(package/n) for n in ('corpus.json','sources.json')}})
    (tmp_path/'application.py').write_text('# pinned application',encoding='utf-8')
    (tmp_path/'capture.py').write_text('# pinned diagnostic helper',encoding='utf-8')
    frozen={'schema':{'type':'object'}, 'messages':[
        {'type':'system','content':'Return all required fields.'}, {'type':'human','content':'Synthetic fixture.'}]}
    write_json(proposal/'input.json',frozen)
    write_json(proposal/'native.json',request_body(frozen))
    write_json(proposal/'identity.json',{'package_sha256':sha(package/'manifest.json'),
        'code_and_policy':{'application.py':sha(tmp_path/'application.py')}})
    protocol={'files':{n:sha(proposal/n) for n in ('input.json','native.json','identity.json')},
        'project_files':{'capture.py':sha(tmp_path/'capture.py')},'expected_identity':'identity.json',
        'package':'data/frozen','mapper_input':'input.json','native_body':'native.json',
        'native_body_sha256':sha(proposal/'native.json'),'capture_helper':'capture.py',
        'model':'ami-llama3.1:8b-4k','model_digest':'a'*64,'authorization_reply':'Authorize synthetic fixture',
        'service_seconds':60,'validation_seconds':30,'overall_seconds':95,'output_directory':'attempt'}
    write_json(proposal/'contract.json',protocol)
    digest=sha(proposal/'contract.json')
    write_json(proposal/'authorization.json',{'contract_sha256':digest,'human_reply':protocol['authorization_reply']})
    return proposal/'contract.json',digest,protocol


@pytest.mark.parametrize('changed', ['application.py','capture.py','data/frozen/corpus.json','data/source.txt'])
def test_protocol_rejects_changed_generator_harness_package_and_source(tmp_path,monkeypatch,changed):
    path,digest,_=fixture(tmp_path,monkeypatch)
    assert check.check_protocol(path,digest)
    (tmp_path/changed).write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError):check.check_protocol(path,digest)


def test_protocol_rejects_contract_and_native_body_changes(tmp_path,monkeypatch):
    path,digest,protocol=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='Protocol identity'):check.check_protocol(path,'0'*64)
    native=json.loads((path.parent/'native.json').read_text());native['options']['num_predict']=901
    write_json(path.parent/'native.json',native)
    protocol['files']['native.json']=sha(path.parent/'native.json')
    write_json(path,protocol)
    with pytest.raises(ValueError,match='Native request'):check.check_protocol(path,sha(path))


def test_paths_and_authorization_reject_before_spawning(tmp_path,monkeypatch):
    path,digest,protocol=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(check,'supervise',lambda *a:pytest.fail('must not spawn'))
    with pytest.raises(ValueError,match='declared root'):check._inside(path.parent,'../../outside')
    with pytest.raises(ValueError,match='authorization attached'):check.execute(path,digest,path.parent/'other.json')
    write_json(path.parent/'authorization.json',{'contract_sha256':digest,'human_reply':'Authorize OLD protocol'})
    with pytest.raises(ValueError,match='new direct human grant'):check.execute(path,digest,path.parent/'authorization.json')


@pytest.mark.parametrize('failure', ['process_timeout','failed_stream','validation_timeout','invalid_mapping',None])
def test_phase_limits_stop_and_no_workflow_or_retry(tmp_path,monkeypatch,failure):
    path,digest,_=fixture(tmp_path,monkeypatch)
    calls=[]
    def synthetic(command,output,seconds):
        calls.append((command,seconds));output.mkdir()
        assert 0<seconds<= (60 if len(calls)==1 else 30)
        process={'timed_out':False,'returncode':0}
        if len(calls)==1:
            assert 'scripts._mapper_transport' in command
            write_json(output/'service-progress.json',{'model_calls_started':1,'response_complete':False})
            if failure=='process_timeout':return {'timed_out':True,'returncode':1}
            write_json(output/'service-result.json',{'status':'failed' if failure=='failed_stream' else 'completed_transport',
                'model_calls_started':1,'usage':{'total_tokens':14},'inflight_usage_unknown':failure=='failed_stream'})
        else:
            assert 'scripts.pilot_mapper_check' in command and 'validate' in command
            if failure=='validation_timeout':return {'timed_out':True,'returncode':1}
            write_json(output/'validation-result.json',{'status':'failed' if failure=='invalid_mapping' else 'engine_validated'})
        return process
    monkeypatch.setattr(check,'supervise',synthetic)
    result=check.execute(path,digest,path.parent/'authorization.json')
    assert len(calls)==(1 if failure in ('process_timeout','failed_stream') else 2)
    assert result['model_calls_started']==1 and result['nemo_invocations']==0
    assert result['approvals_created']==result['exports_created']==0
    assert not result['conditional_workflow_authorized'] and not result['backend_cancellation_verified']
    if failure:
        assert result['status']=='failed' and result['generation_budget'].startswith('closed')
    else:
        assert result['status'].startswith('engine_validated') and 'not automatic' in result['source_assessment']
    with pytest.raises(FileExistsError):check.execute(path,digest,path.parent/'authorization.json')
    assert len(calls)==(1 if failure in ('process_timeout','failed_stream') else 2)


@pytest.mark.parametrize('changed', ['status','response_complete','identity_before','identity_after','finish'])
def test_invalid_service_never_imports_engine(tmp_path,monkeypatch,changed):
    path,digest,_=fixture(tmp_path,monkeypatch)
    service={'status':'completed_transport','response_complete':True,'identity_before':True,'identity_after':True,
             'finish':{'done_reason':'stop'}}
    service[changed]= {'done_reason':'length'} if changed=='finish' else False if changed!='status' else 'failed'
    write_json(tmp_path/'service.json',service)
    out=tmp_path/'validation';out.mkdir()
    result=check.validate_response(path,digest,tmp_path/'service.json',out)
    assert result['status']=='failed' and result['model_calls']==result['nemo_invocations']==0
    assert not result['stages']


def test_inspect_process_has_no_engine_or_framework_imports():
    result=subprocess.run([sys.executable,'-c',
        'import sys;import scripts.pilot_mapper_check;print(any(x in sys.modules for x in '
        '("src.pilot.engine","nemoguardrails","langchain_ollama")))'],capture_output=True,text=True,check=True)
    assert result.stdout.strip()=='False'


def test_offline_parser_replays_fixed_response_without_model(tmp_path,monkeypatch):
    path,digest,protocol=fixture(tmp_path,monkeypatch)
    from langchain_core.messages import SystemMessage,HumanMessage
    from pydantic import BaseModel
    class Reply(BaseModel):
        label:str
    frozen={'schema':Reply.model_json_schema(),'messages':[
        {'type':'system','content':'Return all required fields.'},{'type':'human','content':'Synthetic fixture.'}]}
    write_json(path.parent/'input.json',frozen)
    write_json(path.parent/'native.json',request_body(frozen))
    for name in ('input.json','native.json'):protocol['files'][name]=sha(path.parent/name)
    write_json(path,protocol);digest=sha(path)
    write_json(tmp_path/'service.json',{'status':'completed_transport','response_complete':True,
        'identity_before':True,'identity_after':True,'finish':{'done_reason':'stop'},'usage':None,
        'content':'```json\n{"label":"fixed"}\n```'})
    import runpy
    def helper(_):
        def run(callback):
            response=callback(Reply,[SystemMessage(content=frozen['messages'][0]['content']),
                                     HumanMessage(content=frozen['messages'][1]['content'])])
            assert response['parsed'].label=='fixed' and response['parsing_error'] is None
            return {'events':[{'kind':'synthetic validation only'}]}
        return {'run_engine_mapper':run}
    monkeypatch.setattr(runpy,'run_path',helper)
    output=tmp_path/'validation';output.mkdir()
    result=check.validate_response(path,digest,tmp_path/'service.json',output)
    assert result['status'].startswith('engine_validated') and result['parsed']=={'label':'fixed'}
    assert result['model_calls']==0 and result['reused_service_response']
