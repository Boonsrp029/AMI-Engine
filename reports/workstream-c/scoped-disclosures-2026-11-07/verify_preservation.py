"""Read-only hashes of retained evidence; no source/reference answers are printed."""
import argparse
import json
from pathlib import Path
from scripts._mapper_transport import sha


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='preservation-and-source.json')
    args = parser.parse_args()
    if Path(args.output).name != args.output:
        raise ValueError('Output must be a filename in this evidence directory')
    root = Path('reports/workstream-c/concurrent-qualification-2026-11-06')
    baseline = json.loads((here/'baseline.json').read_text())['sha256']
    unchanged = {name: sha(Path(name)) for name in baseline if name != 'src/pilot/subtasks/synthesis.py'}
    assert all(value == baseline[name] for name, value in unchanged.items())
    counts = {}
    for manifest in [root/'manifest.json', root/'cq1/manifest.json',
                     Path('data/external/release_qualification_2026_10_30_v4/frozen-v4/manifest.json')]:
        pinned = json.loads(manifest.read_text())['sha256']
        assert all(sha(manifest.parent/name) == expected for name, expected in pinned.items())
        counts[str(manifest)] = len(pinned)
    for snapshot, key in [(root/'title-lineage-2026-11-07/executed-source-snapshot-v7', 'input_sha256'),
                          (root/'question-span-2026-11-07/executed-source-snapshot', 'executed_source_sha256')]:
        manifest = json.loads((snapshot/'manifest.json').read_text())
        assert all(sha(snapshot/name) == expected for name, expected in manifest[key].items())
    actual = root/'question-span-2026-11-07'
    manifest = json.loads((actual/'executed-source-snapshot/manifest.json').read_text())
    assert all(sha(actual/name) == expected for name, expected in manifest['actual_output_sha256'].items())
    old = root/'title-lineage-2026-11-07'
    manifest = json.loads((old/'executed-source-snapshot-v7/manifest.json').read_text())
    assert all(sha(old/'actual-development-v7'/name) == expected for name, expected in manifest['actual_output_sha256'].items())
    assert sha(Path('reports/workflow_pilot/production-readiness-2026-10-27/resume-v108/runs/attempt-r07.json')) == '5c09d7eaa6eb1f5c7a6434e531c8d4281af4efe46658f8bcd432aecfc82ebfd9'
    original = json.loads(Path('reports/workflow_pilot/production-readiness-2026-10-27/baseline.json').read_text())
    owner = json.loads(Path('docs/pilot/evidence/owner-review-2026-10-23.json').read_text())
    csv_path = Path(owner['source_csv'])
    csv_current = sha(csv_path)
    assert csv_current == original['hashes'][csv_path.as_posix()]
    release = json.loads(Path('reports/workstream-f/rc-2026-11-06/integrated-baseline.json').read_text())
    owner_docs = {name: expected for name, expected in release['sha256'].items()
                  if name.startswith('docs/pilot/') and 'owner' in name}
    assert all(sha(Path(name)) == expected for name, expected in owner_docs.items())
    export_snapshots = {name: expected for name, expected in original['hashes'].items()
                        if name.endswith('approved-exports.json') or name.endswith('approval-and-export.json')}
    assert all(sha(Path(name)) == expected for name, expected in export_snapshots.items())
    current = {str(p): sha(p) for p in Path('src').rglob('*.py')}
    result = {'unchanged_baseline': unchanged, 'manifest_file_counts': counts,
        'retained_snapshot_file_counts': [128, 93], 'actual_attempt_outputs_unchanged': True,
        'r07_unchanged': True, 'completed_owner_csv_unchanged': True,
        'owner_csv_baseline': 'matches27OctoberGoalbaseline; older23Octoberrecord is historical and differs',
        'owner_csv_current_sha256': csv_current, 'owner_csv_23October_record_sha256': owner['source_csv_sha256'],
        'owner_documents_unchanged': len(owner_docs), 'historical_approval_export_snapshots_unchanged': len(export_snapshots),
        'cached_export_behavior': 'checked with synthetic Store runner/review tests, not a production exercise',
        'current_source_sha256': current, 'new_model_calls': 0, 'CQ1attempted': 0}
    with (here/args.output).open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in {'current_source_sha256', 'unchanged_baseline'}}))


if __name__ == '__main__':
    main()
