"""Bind the prepared pool and offline evidence before any authorization request."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from src.pilot.subtasks._development_lineage import canonical_hash
from src.pilot.subtasks.qualification import digest


def main():
    path = ROOT / 'development-contract.json'
    original = json.loads(path.read_text(encoding='utf-8'))
    if original.get('follow_on_pool_manifest_sha256'):
        raise ValueError('Already finalized; use a new preparation directory')
    shutil.copyfile(path, ROOT / 'development-contract-draft.json')
    paths = list((ROOT / 'pool').iterdir()) + list((ROOT / 'question-scopes').iterdir())
    paths += [ROOT / name for name in ('freeze-pool.py', 'compile-qualification.py', 'run_qualification_case.py',
        'check-offline.py', 'finalize.py', 'pool-freeze-audit.json', 'new-source-provenance.json',
        'eia-glossary-n.html', 'eia-glossary-n.txt', 'offline-validation.json')]
    original['input_sha256'].update({str(item.resolve()): digest(item) for item in paths if item.is_file()})
    original['follow_on_pool_manifest_sha256'] = digest(ROOT / 'pool/manifest.json')
    original['follow_on_qualification_requires_separate_grant'] = True
    original['contract_sha256'] = canonical_hash(original)
    path.write_text(json.dumps(original, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'final_contract_sha256': original['contract_sha256'],
                      'pins': len(original['input_sha256']), 'execution_authorized': False}))


if __name__ == '__main__':
    main()
