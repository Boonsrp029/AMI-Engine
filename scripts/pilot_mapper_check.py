"""Hash-pinned diagnostic orchestration; execution requires a new human grant.

The application model adapter is unchanged. The service child uses only stdlib;
a separate offline child replays its response through actual engine validation.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from scripts._mapper_transport import read_json, request_body, sha, supervise, write_json


def _inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Protocol path leaves its declared root')
    return path


def check_protocol(path, digest):
    path = Path(path).resolve()
    if sha(path) != digest:
        raise ValueError('Protocol identity changed')
    protocol = read_json(path)
    for name, expected in protocol['files'].items():
        if sha(_inside(path.parent, name)) != expected:
            raise ValueError('Frozen diagnostic artifact changed')
    project = Path.cwd().resolve()
    for name, expected in protocol['project_files'].items():
        if sha(_inside(project, name)) != expected:
            raise ValueError('Application or diagnostic code changed')
    identity = read_json(_inside(path.parent, protocol['expected_identity']))
    for name, expected in identity['code_and_policy'].items():
        if sha(_inside(project, name)) != expected:
            raise ValueError('Generator identity changed')
    package = _inside(project, protocol['package'])
    if sha(package/'manifest.json') != identity['package_sha256']:
        raise ValueError('Package identity changed')
    manifest = read_json(package/'manifest.json')
    for name, expected in manifest['sha256'].items():
        if sha(_inside(package, name)) != expected:
            raise ValueError('Frozen package content changed')
    for source in read_json(package/'sources.json').values():
        if sha(_inside(package.parent, source['file'])) != source['sha256']:
            raise ValueError('Pinned source content changed')
    frozen = read_json(_inside(path.parent, protocol['mapper_input']))
    native = read_json(_inside(path.parent, protocol['native_body']))
    if request_body(frozen) != native:
        raise ValueError('Native request differs from frozen mapper messages/schema/options')
    return protocol


def validate_response(protocol_path, digest, service_path, output):
    """One offline validation, with no service/client/model invocation."""
    started = time.monotonic()
    output = Path(output)
    write_json(output/'validation-progress.json', {'stage':'bootstrap', 'monotonic':started, 'model_calls':0})
    result = {'status':'started', 'model_calls':0, 'nemo_invocations':0, 'stages':[]}
    try:
        protocol = check_protocol(protocol_path, digest)
        service = read_json(service_path)
        if (not service['status'].startswith('completed_transport') or not service['response_complete']
                or not service['identity_before'] or not service['identity_after']
                or service['finish'].get('done_reason') != 'stop'):
            raise ValueError('Transport did not complete its technical contract')
        result['stages'].append({'stage':'engine_import_started', 'elapsed_seconds':time.monotonic()-started})
        write_json(output/'validation-progress.json', result)
        import runpy
        from langchain_core.messages import AIMessage
        from langchain_core.output_parsers import PydanticOutputParser
        helper = runpy.run_path(_inside(Path.cwd(), protocol['capture_helper']).as_posix())
        result['stages'].append({'stage':'engine_import_complete', 'elapsed_seconds':time.monotonic()-started})
        frozen = read_json(_inside(Path(protocol_path).resolve().parent, protocol['mapper_input']))
        def fixed_response(schema, messages):
            observed = {'schema':schema.model_json_schema(),
                        'messages':[{'type':m.type,'content':m.content} for m in messages]}
            if observed != frozen:
                raise ValueError('Actual engine input no longer matches frozen transport input')
            raw = AIMessage(content=service['content'], usage_metadata=service['usage'],
                response_metadata={**service['finish'], 'model_provider':'ollama', 'model_name':protocol['model']})
            # Reuse the installed SDK's parser behavior; do not add a second
            # parser/repair model or fill missing mapper fields.
            try:
                parsed = PydanticOutputParser(pydantic_object=schema).invoke(raw)
                result['parsed'] = parsed.model_dump()
                error = None
            except Exception as exc:
                parsed, error = None, exc
                result['parsing_error_type'] = type(exc).__name__
            return {'raw':raw, 'parsed':parsed, 'parsing_error':error}
        checked = helper['run_engine_mapper'](fixed_response)
        result.update(status='engine_validated; assistant source assessment pending',
                      events=checked['events'], reused_service_response=True)
        check_protocol(protocol_path, digest)
    except Exception as error:
        result.update(status='failed', error_type=type(error).__name__)
    result['elapsed_seconds'] = time.monotonic()-started
    write_json(output/'validation-result.json', result)
    return result


def execute(protocol_path, digest, authorization):
    started = time.monotonic()
    protocol_path = Path(protocol_path).resolve()
    protocol = check_protocol(protocol_path, digest)
    if Path(authorization).resolve() != protocol_path.parent/'authorization.json':
        raise ValueError('Use the authorization attached to this exact protocol')
    auth = read_json(authorization)
    if auth.get('contract_sha256') != digest or auth.get('human_reply') != protocol['authorization_reply']:
        raise ValueError('A new direct human grant is required')
    if protocol['service_seconds'] != 60 or protocol['validation_seconds'] != 30 or protocol['overall_seconds'] != 95:
        raise ValueError('Diagnostic phase budgets changed')
    output = _inside(protocol_path.parent.parent, protocol['output_directory'])
    output.mkdir(exist_ok=False)
    deadline = started + 95
    summary = {'status':'started', 'model_calls_started':0, 'nemo_invocations':0,
        'source_assessment':'pending', 'conditional_workflow_authorized':False,
        'backend_cancellation_verified':False, 'phase_results':{}}
    try:
        seconds = min(60, deadline-time.monotonic()-32)
        if seconds <= 0:
            raise TimeoutError('Preparation exhausted the declared overall budget')
        service_out = output/'service'
        service = supervise([sys.executable,'-m','scripts._mapper_transport','service',
            '--input',str(_inside(protocol_path.parent, protocol['native_body'])),
            '--output',str(service_out),'--contract',str(protocol_path),'--contract-sha256',digest,
            '--authorization',str(authorization),'--deadline',str(time.monotonic()+seconds)], service_out, seconds)
        summary['phase_results']['service'] = service
        progress_path = service_out/'service-progress.json'
        progress = read_json(progress_path) if progress_path.is_file() else {}
        summary['model_calls_started'] = progress.get('model_calls_started',0)
        summary['inflight_usage_unknown'] = bool(summary['model_calls_started'] and not progress.get('response_complete'))
        if service['timed_out'] or service['returncode'] != 0:
            raise RuntimeError('Service process failed; do not retry')
        service_path = service_out/'service-result.json'
        received = read_json(service_path)
        summary.update(model_calls_started=received['model_calls_started'], usage=received['usage'],
                       inflight_usage_unknown=received['inflight_usage_unknown'])
        if not received['status'].startswith('completed_transport'):
            raise RuntimeError('Service technical gate failed')
        seconds = min(30, deadline-time.monotonic()-2)
        if seconds <= 0:
            raise TimeoutError('No offline validation budget remains')
        validation_out = output/'validation'
        validation = supervise([sys.executable,'-m','scripts.pilot_mapper_check','validate',
            '--protocol',str(protocol_path),'--sha256',digest,'--service',str(service_path),
            '--output',str(validation_out)], validation_out, seconds)
        summary['phase_results']['validation'] = validation
        if validation['timed_out'] or validation['returncode'] != 0:
            raise RuntimeError('Offline validation failed; do not retry')
        checked = read_json(validation_out/'validation-result.json')
        if not checked['status'].startswith('engine_validated'):
            raise RuntimeError('Engine validation gate failed')
        check_protocol(protocol_path,digest)
        summary['status'] = 'engine_validated; assistant source assessment pending'
        summary['source_assessment'] = 'required before conditional workflow; not automatic'
    except Exception as error:
        summary.update(status='failed',error_type=type(error).__name__,generation_budget='closed after technical failure')
    summary.update(elapsed_seconds=time.monotonic()-started, overall_seconds=95,
                   elapsed_budget_exceeded=time.monotonic()>deadline, approvals_created=0,exports_created=0)
    write_json(output/'summary.json',summary)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['inspect','execute','validate'])
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--service',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    if args.mode=='inspect':
        p=check_protocol(args.protocol,args.sha256)
        print(json.dumps({'protocol_valid':True,'model_calls':0,'overall_seconds':p['overall_seconds']}))
        return 0
    if args.mode=='validate':
        if not args.service or not args.output:parser.error('validation needs a completed service record and owned output')
        result=validate_response(args.protocol,args.sha256,args.service,args.output)
        return 0 if result['status'].startswith('engine_validated') else 1
    if not args.authorization:parser.error('execution needs a new protocol-specific human grant')
    result=execute(args.protocol,args.sha256,args.authorization)
    print(json.dumps({k:result[k] for k in ('status','model_calls_started','nemo_invocations','elapsed_seconds')}))
    return 0 if result['status'].startswith('engine_validated') else 1


if __name__=='__main__':
    raise SystemExit(main())
