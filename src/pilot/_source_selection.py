"""Explicit selection-only wire and provenance-checked application extracts.

This is a new private contract, never a repair path for a malformed legacy wire.
Exact quotation retention proves provenance, not relevance or completeness.
"""
from typing import Annotated, Literal
import re

from pydantic import Field, model_validator

from src.pilot.schemas import StrictModel
from src.pilot._evidence import (
    EvidenceSelection, GeographySelection, MAPPING_INSTRUCTION,
    _resolve_span, resolve_selection,
)
from src.utils._periods import _COMMAND
from src.pilot._requests import requested_components
from src.pilot._quantities import quantity_pairs
from src.pilot._financial_coverage import financial_views, validate_financial_selection


SOURCE_MAPPING_VERSION = 'requested-evidence-v42'
WIRE_VERSION = 'source-selection-v1'


def _instruction():
    # Keep the legacy instruction/schema available unchanged. This explicit
    # migration alters only answer authorship and its corresponding examples.
    text = MAPPING_INSTRUCTION.split('Examples show format only,')[0]
    changes = {
        'exactly one answer per supplied request': 'exactly one classification per supplied request',
        ('requires status, short_answer, evidence. Include all requested causes/activities; '
         'preserve supported partial answers. short_answer must ANSWER the request in complete sentences '
         'with the change, measure and all supported causes/activities, not a copied topic label. '):
        ('Return status, evidence and gap_anchor for every component. Select evidence covering all '
         'requested causes/activities; preserve supported partial evidence. Do not write an answer or '
         'copy quotations: the application constructs extracts from your selected span IDs. '),
        'answer each period\'s direction and requested categories':
            'select evidence for each period\'s direction and requested categories',
        'answer that one measure\'s level or change': 'select evidence for that one measure\'s level or change',
        "For missing use short_answer='', evidence=[] and mark missing without unrelated background.":
            'For missing use evidence=[] and mark missing without unrelated background.',
        'For conflicting use empty answer and two differing spans':
            'For conflicting select at least two differing spans',
        'select both counts and answer which is larger or smaller': 'select both counts for the requested comparison',
        'A supported answer is not a gap.': 'A supported selection is not a gap.',
    }
    for old, new in changes.items():
        if old not in text:
            raise ValueError('Legacy mapping instruction changed; review the private migration')
        text = text.replace(old, new)
    return (f'Return wire_version="{WIRE_VERSION}". No short_answer field is permitted. '
        + text + 'For unordered financial views, select each available coverage role at least once; '
        'one span may cover several roles and must not be repeated. Role labels are not proof of semantic support. '
        'Return actual values in the new selection-only format. Examples are synthetic.\n'
        '{"wire_version":"source-selection-v1","components":[{"component_id":"r1",'
        '"status":"supported","evidence":["example-output"],"gap_anchor":""}],'
        '"geography":{"status":"unresolved","value":"","evidence":[],"reason":"No place stated."},"period":""}\n'
        '{"wire_version":"source-selection-v1","components":[{"component_id":"r1",'
        '"status":"missing","evidence":[],"gap_anchor":"requested dated observation"}],'
        '"geography":{"status":"unresolved","value":"","evidence":[],"reason":"No place stated."},"period":""}')


SOURCE_SELECTION_INSTRUCTION = _instruction()


class SourceSelectionComponent(StrictModel):
    component_id: str = Field(min_length=1, max_length=30)
    status: Literal['supported', 'partial', 'missing', 'conflicting']
    evidence: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        max_length=5, json_schema_extra={'uniqueItems': True})
    gap_anchor: str = Field(max_length=1200)
    measure: str = Field(default='', max_length=100)
    scenario: str = Field(default='', max_length=100)
    kind: Literal['actual', 'projection', 'unknown'] = 'unknown'

    @model_validator(mode='after')
    def valid_selection_state(self):
        if len(set(self.evidence)) != len(self.evidence):
            raise ValueError('Selected evidence span IDs must be distinct within each component')
        if self.status in {'supported', 'partial'} and not self.evidence:
            raise ValueError('Supported selection requires evidence')
        if self.status == 'supported' and self.gap_anchor:
            raise ValueError('Supported evidence cannot contain a gap anchor')
        if self.status == 'missing' and self.evidence:
            raise ValueError('Missing selection cannot contain background evidence')
        if self.status == 'conflicting' and len(self.evidence) < 2:
            raise ValueError('Conflicting selection requires at least two spans')
        return self


class SourceSelection(EvidenceSelection):
    # Inheritance preserves schema-family detection for adapters, not old-wire
    # acceptance. The explicit version and strict component type separate them.
    wire_version: Literal['source-selection-v1']
    components: list[SourceSelectionComponent] = Field(min_length=1, max_length=5)


def resolve_source_selection(value, catalog, question, sources, as_of):
    selection = SourceSelection.model_validate(value)
    views = financial_views(catalog, sources, requested_components(question), question)
    legacy_shape = selection.model_dump(exclude={'wire_version'})
    extracts = []
    for component in legacy_shape['components']:
        ids = component['evidence']
        # Resolve identity, source hash and exact character offsets BEFORE using
        # any catalog text as an application-authored answer.
        resolved = [_resolve_span(sid, catalog, sources) for sid in ids]
        coverage = validate_financial_selection(component, views.get(component['component_id']))
        if any(_COMMAND.search(e['quote']) for e in resolved):
            raise ValueError('Selected extract contains instruction-like source content')
        supported = component['status'] in {'supported', 'partial'}
        answer = ' '.join(e['quote'] for e in resolved) if supported else ''
        if len(answer) > 800:
            raise ValueError('Selected extracts exceed the 800-character answer limit')
        component['short_answer'] = answer
        extracts.append({'component_id': component['component_id'],
            'financial_comparison_coverage': coverage,
            'origin': 'application-selected-source-extract', 'text': answer,
            'span_ids': ids, 'evidence': [{**e, 'span_id': sid,
                **{k: catalog[sid][k] for k in ('content_sha256', 'start', 'end')}}
                for sid, e in zip(ids, resolved, strict=True)]})
    # Preserve all legacy anchor, quotation, geographic, state and citation
    # validation. Invalid input never becomes an abstention or repair call.
    mapping = resolve_selection(legacy_shape, catalog, question, sources, as_of)
    requests = {r['component_id']: r for r in requested_components(question)}
    for component, extract in zip(mapping.components, extracts, strict=True):
        request = requests[component.component_id]
        measure = request.get('quantity_measure')
        check = 'not_applicable'
        if measure and component.status in {'supported', 'partial'}:
            quoted = ' '.join(e.quote for e in component.evidence)
            units = {unit for unit, _ in quantity_pairs(quoted)}
            has_value = bool(units & {'usd', 'baht'})
            has_count = 'project' in units or bool(re.search(
                r'\b(?:project count|number of projects)\b', quoted, re.I))
            wrong = ((measure == 'value' and has_count and not has_value)
                or (measure == 'count' and has_value and not has_count))
            if wrong:
                raise ValueError('Selected extracts have incompatible requested quantity measure')
            # This does not prove subject, period, level/change or percentage
            # denominator support. Unrecognized units remain unknown.
            check = 'passed_necessary_measure_check' if has_value or has_count else 'unknown'
        extract['quantity_measure_check'] = check
    return mapping, extracts
