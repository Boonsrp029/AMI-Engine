"""Offline retained-response diagnosis; sockets blocked, no safety or persistence."""
import json
from pathlib import Path
import socket
import time
import traceback

ROOT = Path(__file__).resolve().parent

def blocked(*args, **kwargs):
    raise AssertionError('Network forbidden in retained-response replay')

socket.socket.connect = blocked
socket.create_connection = blocked

from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks._scoped_activation import prepare_composer

contract = json.loads((ROOT / 'development-contract.json').read_text())
frozen = contract['cases']['cq-p02']
result = json.loads((ROOT / 'actual-development-v1/cq-p02.result.json').read_text())
runtime = next(e['payload']['plan'] for e in result['stored_run']['events'] if e['kind'] == 'subtask_plan')
plan = Plan.model_validate_json(json.dumps(runtime))
report = run_plan(plan, result['stored_run']['id'], result['stored_run']['metrics']['attempt_id'],
                  LocalBM25Adapter(frozen['corpus_path']))
calls = []

def fixed(stage, schema, instruction, inputs):
    calls.append(stage)
    record = json.loads((ROOT / f'actual-development-v1/cq-p02.{stage}.raw.json').read_text())
    return {'parsed': json.loads(record['raw']), 'raw': record['raw'], 'usage': record.get('usage')}

callback = prepare_composer(contract, frozen, plan, fixed, None)
try:
    projection = callback(report, ModelAccess(time.monotonic() + 30))
    outcome = {'reproduced_failure': False, 'draft': projection.draft}
except Exception as error:
    outcome = {'reproduced_failure': True, 'type': type(error).__name__, 'message': str(error),
               'traceback': traceback.format_exc()}
outcome.update(offline=True, sockets_blocked=True, actual_model_calls=0,
               replayed_stages=calls, nemo_invocations=0)
output = ROOT / 'cq-p02-offline-replay.json'
if output.exists():
    raise FileExistsError(output)
output.write_text(json.dumps(outcome, indent=2) + '\n', encoding='utf-8')
print(json.dumps(outcome, indent=2))
