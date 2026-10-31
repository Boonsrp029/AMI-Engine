"""Read-only telemetry, bounded inputs and honest unknowns; no inference."""
import hashlib,json,sqlite3
from pathlib import Path

import pytest

from scripts import pilot_operational_report as report
from src.pilot.store import Store
from src.pilot.schemas import ResearchRequest


PRIVATE='private-query-person@example.invalid'


def fixture(tmp_path,entries):
    path=tmp_path/'workflow.sqlite3';store=Store(path)
    ids=[]
    for index,(status,metrics) in enumerate(entries):
        run_id,_=store.create(ResearchRequest(query='Synthetic analyst request',request_key='request-'+str(index)),'a'*64)
        with store.connection() as db:
            # Simulate a legacy/tampered row; do not weaken the input PII guard.
            db.execute('UPDATE runs SET query=?,status=?,metrics=?,error=?,created=? WHERE id=?',
                (PRIVATE,status,json.dumps(metrics),'private-error-secret',f'2026-01-01T00:00:{index:02d}+00:00',run_id))
        ids.append(run_id)
    return path,store,ids


def test_report_readonly_counts_latencies_partial_usage_and_no_sensitive_data(tmp_path):
    path,store,ids=fixture(tmp_path,[('approved',{'elapsed_seconds':10}),('failed',{'elapsed_seconds':20}),('interrupted',{})])
    store.event(ids[0],'model_request_started',{'query':PRIVATE})
    store.event(ids[0],'model_call',{'usage':{'input_tokens':40,'output_tokens':5,'total_tokens':45},'source':'private-source-secret'})
    store.event(ids[1],'model_call',{'usage':None})
    store.event(ids[1],'model_failure',{'error':'private-error-secret'})
    store.event(ids[0],'guard_invocation_started',{})
    store.event(ids[0],'private-event-label',{'reviewer':'private-reviewer'})
    before=hashlib.sha256(path.read_bytes()).hexdigest();value=report.build_report(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    assert value['run_status_counts']['approved']==value['run_status_counts']['failed']==value['run_status_counts']['interrupted']==1
    assert value['recorded_latency']['samples']==2 and value['recorded_latency']['p95_seconds']==20
    assert value['known_model_token_totals']=={'input_tokens':40,'output_tokens':5,'total_tokens':45}
    assert value['model_call_events_without_valid_usage']==1
    assert value['nemo_internal_token_usage'] is value['monetary_cost'] is value['hardware_energy_cost'] is None
    assert not value['overall_token_accounting_complete'] and not value['alert_delivery_performed']
    encoded=json.dumps(value)
    assert all(word not in encoded for word in (PRIVATE,'private-source-secret','private-error-secret','private-reviewer','private-event-label'))


def test_unknowns_are_null_not_zero_and_bad_status_does_not_leak(tmp_path):
    path,store,ids=fixture(tmp_path,[('private-status-secret',{'elapsed_seconds':float('nan')})])
    with store.connection() as db:db.execute('UPDATE runs SET metrics=?',('not-json',))
    store.event(ids[0],'model_call',{'usage':{'input_tokens':True,'output_tokens':3}})
    value=report.build_report(path)
    assert value['known_model_token_totals'] is None and value['recorded_latency']['p95_seconds'] is None
    assert value['invalid_metric_objects']==1 and value['run_status_counts']['unknown']==1
    assert 'private-status-secret' not in json.dumps(value)


def test_event_and_run_limits_disclose_truncation_and_select_recent_runs(tmp_path):
    path,store,ids=fixture(tmp_path,[('failed',{}),('approved',{})])
    for _ in range(3):store.event(ids[-1],'model_call',{'usage':None})
    value=report.build_report(path,run_limit=1,event_limit=1)
    assert value['scope']['total_stored_runs']==2 and value['scope']['selected_runs']==1
    assert value['scope']['matching_marker_events']==3 and value['scope']['selected_marker_events']==1
    assert value['scope']['truncated'] and 'report_truncated' in value['conditions']


def test_malformed_large_or_inconsistent_usage_is_not_invented(tmp_path):
    path,store,ids=fixture(tmp_path,[('needs_review',{'elapsed_seconds':True})])
    for usage in ({'input_tokens':2,'output_tokens':3,'total_tokens':99},
        {'input_tokens':-1,'output_tokens':3},None):store.event(ids[0],'model_call',{'usage':usage})
    with store.connection() as db:
        db.execute('INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)',(ids[0],'model_call','x'*70_000,'now'))
    value=report.build_report(path)
    assert value['known_model_token_totals'] is None and value['model_call_events_without_valid_usage']==4
    assert value['invalid_event_payloads']==1 and value['recorded_latency']['samples']==0


def test_missing_database_is_not_created_and_cli_error_is_sanitized(tmp_path,capsys):
    missing=tmp_path/'private-source-secret.sqlite3';output=tmp_path/'report.json'
    assert report.main(['--database',str(missing),'--output',str(output)])==1
    assert not missing.exists() and not output.exists()
    text=capsys.readouterr().out
    assert 'FileNotFoundError' in text and 'private-source-secret' not in text


def test_cli_writes_new_report_only_and_preserves_existing_artifact(tmp_path):
    path,_,_=fixture(tmp_path,[('queued',{})]);output=tmp_path/'report.json'
    assert report.main(['--database',str(path),'--output',str(output)])==0
    before=output.read_bytes();assert report.main(['--database',str(path),'--output',str(output)])==1
    assert output.read_bytes()==before


def test_empty_history_and_explicit_zero_usage_are_distinct(tmp_path):
    path=tmp_path/'empty.sqlite3';store=Store(path)
    empty=report.build_report(path)
    assert empty['scope']['selected_runs']==0 and empty['known_model_token_totals'] is None
    run_id,_=store.create(ResearchRequest(query='Synthetic request',request_key='request-one'),'a'*64)
    store.event(run_id,'model_call',{'usage':{'input_tokens':0,'output_tokens':0,'total_tokens':0}})
    zero=report.build_report(path)
    assert zero['model_call_events_with_valid_usage']==1
    assert zero['known_model_token_totals']=={'input_tokens':0,'output_tokens':0,'total_tokens':0}
    assert zero['monetary_cost'] is None and not zero['overall_token_accounting_complete']


@pytest.mark.parametrize('limit',[0,-1,True,10_001])
def test_invalid_run_limit_fails_without_reading_database(tmp_path,limit):
    with pytest.raises(ValueError):report.build_report(tmp_path/'missing',run_limit=limit)


def test_no_framework_import_needed_to_read_or_inspect_cli():
    import subprocess,sys
    completed=subprocess.run([sys.executable,'-c',
        'import sys;import scripts.pilot_operational_report;print(any(x in sys.modules for x in ("src.pilot.engine","nemoguardrails","langchain_ollama")))'],
        capture_output=True,text=True,check=True)
    assert completed.stdout.strip()=='False'
