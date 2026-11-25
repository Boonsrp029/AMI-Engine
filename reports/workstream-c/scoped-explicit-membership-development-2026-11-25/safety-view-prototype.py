"""Unactivated C proposal for A review; no guardrails or model invocation."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from src.pilot._evidence import build_span_catalog
from src.pilot.subtasks._membership_coverage import membership_fields
from src.pilot.subtasks._request_focus import render_membership


def proposed_excerpt(query, draft, sources):
    if len(draft['claims']) != 1:
        return None
    claim = draft['claims'][0]
    if len(claim['source_ids']) != 1:
        return None
    matches = []
    for span_id, span in build_span_catalog(sources).items():
        if span['source_id'] != claim['source_ids'][0]:
            continue
        fields = membership_fields(query, span['text'])
        if fields:
            targets = dict(zip(('target_1', 'target_2'), fields['members'], strict=True))
            if claim['text'] == render_membership(targets, fields):
                matches.append({'span_id': span_id, **span})
    return matches[0] if len(matches) == 1 else None


def main():
    question = 'Does the Northbridge recovered products category include ceramic chips and reclaimed wood?'
    quote = 'Recovered products includes crushed brick, ceramic chips, reclaimed wood, and glass.'
    sources = {'manual': {'content': quote}}
    draft = {'claims': [{'text': 'The recovered products category includes ceramic chips and reclaimed wood.',
                         'source_ids': ['manual']}]}
    cases = [('complete', question, draft, sources, True)]
    for name, text in (('incomplete', 'The recovered products category includes ceramic chips.'),
        ('wrong_member', 'The recovered products category includes ceramic chips and uranium.'),
        ('wrong_polarity', 'The recovered products category excludes ceramic chips and reclaimed wood.')):
        changed = copy.deepcopy(draft)
        changed['claims'][0]['text'] = text
        cases.append((name, question, changed, sources, False))
    changed = copy.deepcopy(draft)
    changed['claims'][0]['source_ids'] = ['unretrieved']
    cases.append(('unknown_citation', question, changed, sources, False))
    cases.append(('ambiguous_duplicate_span', question, draft, {'manual': {'content': quote + ' ' + quote}}, False))
    cases.append(('empty_claims', question, {'claims': []}, sources, False))
    checks = []
    for name, query, candidate, records, expected in cases:
        excerpt = proposed_excerpt(query, candidate, records)
        assert (excerpt is not None) == expected, name
        if excerpt:
            content = records[excerpt['source_id']]['content']
            assert content[excerpt['start']:excerpt['end']] == excerpt['text']
            complete_context = '\n'.join(record['content'] for record in records.values())
            proposed_context = 'Selected source excerpt:\n' + excerpt['text'] + '\n\nComplete retrieved evidence:\n' + complete_context
            assert proposed_context.endswith(complete_context)
        checks.append({'case': name, 'recognized': excerpt is not None, 'expected': expected})
    result = {'activated': False, 'model_calls': 0, 'nemo_calls': 0, 'synthetic_checks': checks,
              'purpose': 'Exact source-leading excerpt selection; does not predict judge verdicts or bypass NO.'}
    with (ROOT / 'safety-view-prototype.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'checks_passed': len(checks), 'activated': False, 'model_calls': 0}))


if __name__ == '__main__':
    main()
