"""Bounded, read-only stored-telemetry summary. No model calls or alert delivery.

Queries, sources, reviewer identities, raw errors and arbitrary event labels are
never selected for output. Stored timings may include synthetic/replayed runs;
this report does not establish warm latency, service liveness or model quality.
"""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import sqlite3
import time


STATUSES = {'queued','running','needs_review','approved','rejected','failed','interrupted'}
EVENTS = ('model_request_started','model_call','model_failure','guard_invocation_started')


def _object(value):
    try:
        if not isinstance(value,str) or len(value)>65_536:return None
        result=json.loads(value)
        return result if isinstance(result,dict) else None
    except (TypeError,ValueError,RecursionError):
        return None


def _seconds(value):
    try:
        return value if type(value) in (int,float) and math.isfinite(value) and value>=0 else None
    except OverflowError:
        return None


def _latencies(values):
    values=sorted(values)
    return {'samples':len(values),'p50_seconds':values[math.ceil(len(values)*.5)-1] if values else None,
        'p95_seconds':values[math.ceil(len(values)*.95)-1] if values else None,
        'definition':'nearest-rank recorded run elapsed time; not qualified warm end-to-end latency'}


def build_report(database,run_limit=10_000,event_limit=100_000):
    if type(run_limit) is not int or not 1<=run_limit<=10_000:
        raise ValueError('Run limit must be between1and10000')
    if type(event_limit) is not int or not 1<=event_limit<=100_000:
        raise ValueError('Event limit must be between1and100000')
    path=Path(database).resolve()
    if not path.is_file():
        raise FileNotFoundError('Workflow database is unavailable')
    started=time.monotonic()
    # mode=ro prevents missing-file creation and storage writes. BEGIN keeps all
    # aggregate queries in one consistent read snapshot without Store migrations.
    statuses=Counter({s:0 for s in sorted(STATUSES)});statuses['unknown']=0
    elapsed=[];invalid_metrics=0;missing_elapsed=0;selected_runs=selected_events=0
    counts=Counter({kind:0 for kind in EVENTS});usage={'input_tokens':0,'output_tokens':0,'total_tokens':0}
    known_usage=missing_usage=invalid_payloads=0
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
        db.set_progress_handler(lambda: int(time.monotonic()-started>5),10_000)
        db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
        total_runs=db.execute('SELECT count(*) FROM runs').fetchone()[0]
        runs=db.execute('SELECT status,CASE WHEN length(metrics)<=65536 THEN metrics ELSE NULL END '
            'FROM runs ORDER BY created DESC,id LIMIT ?',(run_limit,))
        for status,encoded in runs:
            if time.monotonic()-started>5:raise TimeoutError('Report deadline exceeded')
            selected_runs+=1;statuses[status if status in STATUSES else 'unknown']+=1
            metrics=_object(encoded)
            if metrics is None:invalid_metrics+=1
            duration=_seconds(metrics.get('elapsed_seconds')) if metrics else None
            if duration is None:missing_elapsed+=1
            else:elapsed.append(duration)
        marks=','.join('?' for _ in EVENTS)
        selected='SELECT id FROM runs ORDER BY created DESC,id LIMIT ?'
        where=f'FROM events WHERE run_id IN ({selected}) AND kind IN ({marks})'
        params=(run_limit,*EVENTS)
        total_events=db.execute('SELECT count(*) '+where,params).fetchone()[0]
        events=db.execute('SELECT kind,CASE WHEN length(payload)<=65536 THEN payload ELSE NULL END '
            +where+' ORDER BY seq DESC LIMIT ?',(*params,event_limit))
        for kind,encoded in events:
            if time.monotonic()-started>5:raise TimeoutError('Report deadline exceeded')
            selected_events+=1;counts[kind]+=1;payload=_object(encoded)
            if payload is None:invalid_payloads+=1
            if kind!='model_call':continue
            value=payload.get('usage') if payload else None
            if (isinstance(value,dict) and all(type(value.get(k)) is int and value[k]>=0 for k in ('input_tokens','output_tokens'))
                    and ('total_tokens' not in value or type(value['total_tokens']) is int
                         and value['total_tokens']==value['input_tokens']+value['output_tokens'])):
                known_usage+=1;usage['input_tokens']+=value['input_tokens'];usage['output_tokens']+=value['output_tokens']
            else:missing_usage+=1
    usage['total_tokens']=usage['input_tokens']+usage['output_tokens']
    truncated=total_runs>selected_runs or total_events>selected_events
    conditions=[]
    if statuses['failed']:conditions.append('failed_runs_present')
    if statuses['interrupted']:conditions.append('interrupted_runs_present')
    if statuses['unknown']:conditions.append('unknown_run_status_present')
    if truncated:conditions.append('report_truncated')
    if not elapsed:conditions.append('latency_unavailable')
    if missing_usage or not known_usage:conditions.append('model_token_usage_partial_or_unavailable')
    return {'format':'ami-stored-telemetry-v1','generated_utc':datetime.now(timezone.utc).isoformat(),
        'scope':{'selection':'latest runs by creation time; current stored statuses',
            'total_stored_runs':total_runs,'selected_runs':selected_runs,'run_limit':run_limit,
            'matching_marker_events':total_events,'selected_marker_events':selected_events,'event_limit':event_limit,'truncated':truncated},
        'run_status_counts':dict(statuses),'recorded_latency':_latencies(elapsed),
        'runs_without_valid_elapsed_time':missing_elapsed,'invalid_metric_objects':invalid_metrics,
        'event_marker_counts':dict(counts),'invalid_event_payloads':invalid_payloads,
        'known_model_token_totals':usage if known_usage else None,
        'model_call_events_with_valid_usage':known_usage,'model_call_events_without_valid_usage':missing_usage,
        'overall_token_accounting_complete':False,'nemo_internal_token_usage':None,'monetary_cost':None,'hardware_energy_cost':None,
        'conditions':conditions,'alert_delivery_performed':False,
        'qualification':'Stored events may be synthetic/replayed/edited. Markers do not prove inference, backend cancellation, user usefulness or production SLOs.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--run-limit',type=int,default=10_000)
    parser.add_argument('--event-limit',type=int,default=100_000)
    args=parser.parse_args(argv)
    try:
        if args.output.exists():raise FileExistsError('Use a new report path')
        report=build_report(args.database,args.run_limit,args.event_limit)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as target:
            json.dump(report,target,ensure_ascii=False,indent=2,allow_nan=False);target.write('\n')
    except (OSError,ValueError,sqlite3.Error) as error:
        # No database paths, SQL, query data or exception details are disclosed.
        print(json.dumps({'status':'unavailable','error_type':type(error).__name__}))
        return 1
    print(json.dumps({'status':'written','selected_runs':report['scope']['selected_runs'],
        'alert_delivery_performed':False}))
    return 0


if __name__=='__main__':raise SystemExit(main())
