"""Predeclare unused glossary facts and preserve seventeen unattempted cases."""
from collections import Counter
from copy import deepcopy
import html
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash, validate_scopes
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.quality_review import COUNTS, THRESHOLDS

PRIOR = ROOT.parent / 'cq1-power-quantity-pool-2026-11-20'
ACTUAL = ROOT.parent / 'scoped-power-attribution-development-2026-11-20'
REPLACEMENTS = (
    ('cq1-a49', 'Net generation',
     'In the EIA definition of net generation, what is subtracted from gross generation?',
     ['Electrical energy consumed at the generating stations for station service or auxiliaries.']),
    ('cq1-a50', 'Net electricity consumption',
     'How does the EIA compute net electricity consumption from generation, trade and losses?',
     ['Generation plus imports, minus exports, minus transmission and distribution losses.']),
    ('cq1-a51', 'Net interstate flow of electricity',
     'In the EIA definition of net interstate flow of electricity, what does a positive number indicate?',
     ['More electricity including associated losses came into the state than went out during the year.']),
)


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    source = ROOT / 'eia-glossary-n.html'
    raw = source.read_text(encoding='utf-8')
    text = ' '.join(html.unescape(re.sub('<[^>]+>', ' ', raw)).split())
    text_path = ROOT / 'eia-glossary-n.txt'
    text_path.write_text(text + '\n', encoding='utf-8')
    corpus, provenance = [], []
    for cid, term, query, findings in REPLACEMENTS:
        paragraph = next(part for part in re.findall(r'<p\b[^>]*>(.*?)</p>', raw, flags=re.S)
                         if f'>{term}:</strong>' in part)
        excerpt = ' '.join(html.unescape(re.sub('<[^>]+>', ' ', paragraph)).split())
        assert excerpt in text
        record = {'feed_id': f'eia-glossary-{cid}', 'clean_content': excerpt,
                  'title': f'EIA glossary — {term}', 'published': None,
                  'url': 'https://www.eia.gov/tools/glossary/index.php?id=N',
                  'doc_name': text_path.name, 'page_num': None}
        corpus.append(record)
        start = text.index(excerpt)
        provenance.append({'case_id': cid, 'source_id': record['feed_id'], 'url': record['url'],
            'captured_date': '2026-11-25', 'publication_date': None,
            'html_sha256': digest(source), 'text_sha256': digest(text_path),
            'start': start, 'end': start + len(excerpt), 'exact_excerpt': excerpt})
    existing_questions = set()
    for path in ROOT.parent.rglob('cases.json'):
        if 'executed-input-snapshot' in path.parts or 'executed-source-snapshot' in path.parts:
            continue
        rows = read(path)
        if isinstance(rows, list):
            existing_questions.update(row['query'].casefold() for row in rows if isinstance(row, dict) and 'query' in row)
    assert all(query.casefold() not in existing_questions for _, _, query, _ in REPLACEMENTS)
    stop = read(ACTUAL / 'cq1-stop-analysis.json')
    retained = stop['unattempted']
    assert len(retained) == 17 and set(stop['attempted']) == {'cq1-a46', 'cq1-a47', 'cq1-a48'}
    pool = ROOT / 'pool'
    shutil.copytree(PRIOR / 'pool', pool)
    old_cases = {row['case_id']: row for row in read(pool / 'cases.json')}
    old_plans = read(pool / 'plans-v3-explicit-coverage.json')
    # Only new cases use the new corpus. Retained retrieval inputs remain exact.
    new_corpus = pool / 'glossary-corpus.json'
    write(new_corpus, corpus)
    scope_folder = ROOT / 'question-scopes'
    scope_folder.mkdir()
    cases, plans, scope_rows = [], {}, {}
    for cid, term, query, findings in REPLACEMENTS:
        row = {**old_cases['cq1-a48'], 'case_id': cid, 'query': query, 'required_findings': findings,
               'corpus': new_corpus.name}
        entry = deepcopy(old_plans['cq1-a48'])
        entry['plan']['query'] = entry['plan']['subtasks'][0]['query'] = query
        entry['plan']['corpus_sha256'] = digest(new_corpus)
        entry['corpus_path'] = new_corpus.name
        plan = Plan.model_validate_json(json.dumps(entry['plan']))
        scope = {'version': 'cq-scoped-disclosures-v1', 'plan_id': plan.plan_id,
            'corpus_sha256': plan.corpus_sha256, 'question_sha256': hashlib.sha256(query.encode()).hexdigest(),
            'bindings_sha256': bindings_hash(entry['bindings']),
            'declaration_ref': 'Unused glossary question on newly captured source facts; preparer has seen references.',
            'annotations': [{'component_id': 'r1', 'subtask_id': 's01', 'question_span': {'start': 0, 'end': len(query)}}]}
        validate_scopes(plan, entry['bindings'], DisclosureScopes.model_validate_json(json.dumps(scope)))
        write(scope_folder / f'{cid}.json', scope)
        scope_rows[cid] = {'path': f'{cid}.json', 'sha256': digest(scope_folder / f'{cid}.json')}
        cases.append(row)
        plans[cid] = entry
    prior_scopes = read(PRIOR / 'question-scopes/manifest.json')
    retained_audit = {}
    for cid in retained:
        cases.append(old_cases[cid])
        entry = deepcopy(old_plans[cid])
        entry['corpus_path'] = Path(entry['corpus_path']).name
        assert digest(pool / entry['corpus_path']) == entry['plan']['corpus_sha256']
        plans[cid] = entry
        original = PRIOR / 'question-scopes' / prior_scopes['cases'][cid]['path']
        shutil.copyfile(original, scope_folder / f'{cid}.json')
        scope_rows[cid] = {'path': f'{cid}.json', 'sha256': digest(original)}
        retained_audit[cid] = {'case_unchanged': True, 'plan_unchanged': entry['plan'] == old_plans[cid]['plan'],
            'corpus_sha256': entry['plan']['corpus_sha256'], 'scope_sha256': digest(original)}
    assert dict(Counter(row['category'] for row in cases)) == COUNTS
    # New copies supersede these three generated metadata files only.
    for name, value in (('cases.json', cases), ('plans-v3-explicit-coverage.json', plans)):
        (pool / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest = read(PRIOR / 'pool/manifest.json')
    manifest.update(revision='membership-coverage-2026-11-25',
        freshness='17 exact unattempted cases plus 3 unused questions on newly captured glossary definitions; references inspected by preparer.',
        retained_unattempted_cases=retained, replacement_case=[item[0] for item in REPLACEMENTS],
        excluded_consumed_case=stop['attempted'], supersedes_manifest_sha256=digest(PRIOR / 'pool/manifest.json'),
        categories=COUNTS, thresholds={**THRESHOLDS, 'critical_errors': 0})
    manifest['sha256'].update({'cases.json': digest(pool / 'cases.json'), 'glossary-corpus.json': digest(new_corpus)})
    (pool / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (pool / 'plans-v3-coverage-manifest.json').write_text(json.dumps({
        'plans_file': 'plans-v3-explicit-coverage.json', 'sha256': digest(pool / 'plans-v3-explicit-coverage.json'),
        'original_content_manifest_sha256': digest(pool / 'manifest.json')}, indent=2) + '\n', encoding='utf-8')
    write(scope_folder / 'manifest.json', {'version': 'cq1-requested-scopes-v1',
        'pool_manifest_sha256': digest(pool / 'manifest.json'),
        'plans_sha256': digest(pool / 'plans-v3-explicit-coverage.json'),
        'case_ids': [row['case_id'] for row in cases], 'cases': scope_rows})
    write(ROOT / 'new-source-provenance.json', provenance)
    write(ROOT / 'pool-freeze-audit.json', {'generation_performed': False, 'retained_cases': retained_audit,
        'new_cases': [item[0] for item in REPLACEMENTS], 'manifest_sha256': digest(pool / 'manifest.json'),
        'source_provenance_sha256': digest(ROOT / 'new-source-provenance.json'),
        'subsequent_qualification_contract': 'must compile only after two passing current development attempts',
        'execution_authorized': False})
    print(json.dumps({'retained': len(retained), 'new': len(REPLACEMENTS), 'total': len(cases),
                      'manifest_sha256': digest(pool / 'manifest.json')}))


if __name__ == '__main__':
    main()
