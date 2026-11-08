"""Seal terminal offline evidence. No inference or runtime/source modification."""
import json
from pathlib import Path
import re

from scripts._mapper_transport import sha


def main():
    here = Path(__file__).resolve().parent
    log = here/'final-full-offline-tests.txt'
    text = log.read_text(encoding='utf-8')
    match = re.search(r'(\d+) passed, (\d+) warnings in ([\d.]+)s', text)
    assert match and 'FAILED ' not in text, 'Terminal full-suite success required'
    preservation = json.loads((here/'preservation-and-source-final.json').read_text())
    assert all(sha(Path(name)) == expected for name, expected in preservation['current_source_sha256'].items())
    owned = json.loads((here/'c-owned-file-manifest.json').read_text())
    assert all(sha(Path(name)) == expected for name, expected in owned['sha256'].items())
    files = [*owned['sha256'], 'docs/concurrency/c-scoped-disclosures-handoff-a.md']
    evidence = {'milestone': 'offline C implementation complete; A activation and actual quality pending',
        'full_windows': {'passed': int(match[1]), 'warnings': int(match[2]), 'seconds': float(match[3]),
            'log_sha256': sha(log)},
        'focused_scoped': {'passed': 39, 'seconds': 15.58, 'log_sha256': sha(here/'final-scoped-tests.txt')},
        'regression': 'Conflict plus missing branch failed before the final repair; retained test/log. Final suite includes repair.',
        'owned_files_sha256': {name: sha(Path(name)) for name in files},
        'source_manifest_sha256': sha(here/'preservation-and-source-final.json'),
        'input_context_comparison': json.loads((here/'offline-context-comparison.json').read_text()),
        'token_optimizer': {'version': '5.13.66', 'mode': 'Codex read-only audit; no config or hook edits',
            'automatic_compression': 'not configured; no verified Codex context savings'},
        'generation_calls': 0, 'actual_nemo_invocations': 0, 'Ragas_runs': 0, 'CQ1attempted': 0,
        'historical_judgments_and_actual_failures': 'preserved; not regraded',
        'model_quality': 'unverified for new scoped callback', 'owner_acceptance': 'not inferred',
        'independent_usage': 'pending', 'production_qualification': 'not established',
        'A_activation': 'handoff prepared; no current caller changed',
        'no_commit_push_deploy_or_reviewer_contact': True}
    with (here/'completion-evidence.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n')
    old_root = Path('reports/workstream-c/concurrent-qualification-2026-11-06')
    handoff = old_root/'handoff.json'
    current = json.loads(handoff.read_text())
    current['status'] = evidence['milestone'] + '; all inference grants closed'
    current['offline_scoped_disclosures'].update(full_suite=evidence['full_windows'], active_full_session=None,
        completion_evidence=str(here/'completion-evidence.json'), source_integrity='final source manifest matches current files')
    current['next'] = ['A applies explicit scoped-callback activation handoff and freezes per-case scope sidecars; default path stays unchanged until then.',
        'Prepare the next scoped diagnostic/controller contract with exact combined source and input hashes; no current generation grant exists.',
        'Obtain separate actual-generation budget, retain failures and source-adjudicate before advancing; unchanged quality/CQ1/owner/production gates remain unmet.']
    handoff.write_text(json.dumps(current, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'full_windows': evidence['full_windows'], 'source_identity': 'matched',
        'new_model_calls': 0, 'model_quality': evidence['model_quality'], 'A_activation': evidence['A_activation']}))


if __name__ == '__main__':
    main()
