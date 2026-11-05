from pathlib import Path
import json,hashlib,socket
from types import SimpleNamespace

def deny(*a,**k):raise AssertionError('No network during frozen replay')
socket.socket.connect=deny;socket.socket.connect_ex=deny
from src.pilot.subtasks.contracts import Plan,Subtask,Identity,Source,Result,digest
from src.pilot.subtasks.scheduler import Report,aggregate
from src.pilot.subtasks.synthesis import compose_report
path=Path('reports/workflow_pilot/production-readiness-2026-10-27/resume-v108/runs/attempt-r07.json')
sha=hashlib.sha256(path.read_bytes()).hexdigest();assert sha=='5c09d7eaa6eb1f5c7a6434e531c8d4281af4efe46658f8bcd432aecfc82ebfd9'
d=json.loads(path.read_text());records=d['retrieved_sources'];corpus=next(iter(records.values()))['corpus_sha256']
p=Plan(query=d['query'],corpus_sha256=corpus,subtasks=(Subtask(subtask_id='s01',operation='retrieve',query='consumed r07 source replay'),))
i=Identity(run_id='a'*32,attempt_id='b'*32,plan_id=p.plan_id,corpus_sha256=corpus)
sources=tuple(Source(source_id=sid,content=s['content'],content_sha256=digest(s['content']),corpus_sha256=corpus,role='support',title=s['title'],url=s['url'],published=s['published'],doc_name=s['doc_name'],page_num=s['page_num']) for sid,s in records.items())
result=Result(identity=i,subtask_id='s01',child_attempt_id='c'*32,outcome='evidence',sources=sources,elapsed_seconds=0.)
report=Report(i,'completed',(('s01','completed'),),(result,),aggregate((result,)),(),True)
mapping=next(e['payload'] for e in d['events'] if e['kind']=='evidence_mapping');mapping={k:v for k,v in mapping.items() if k!='geography_resolution'}
raw=json.loads(d['captured_model_outputs'][-1]['content'])
def forbidden(**kwargs):raise AssertionError('Bad composition must not reach safety')
try:
 compose_report(p,report,mapping,raw,{c['component_id']:('s01',) for c in mapping['components']},as_of='2026-11-03',guard=SimpleNamespace(validate_output=forbidden),is_current=lambda:True)
 raise AssertionError('Saved bad response accepted')
except ValueError as error:
 assert str(error)=='Draft introduces a numeric value absent from its selected evidence',str(error)
 output={'outcome':'rejected unchanged original raw response','message':str(error),'r07_sha256':sha,'wrapper':'synthetic aggregate reconstructed from frozen sources; not new retrieval/generation','network':'blocked','actual_model_calls':0,'actual_safety_calls':0,'source_artifact_unchanged':hashlib.sha256(path.read_bytes()).hexdigest()==sha}
 Path('reports/workstream-c/r07-aggregate-replay.json').write_text(json.dumps(output,indent=2),encoding='utf-8');print(json.dumps(output))
