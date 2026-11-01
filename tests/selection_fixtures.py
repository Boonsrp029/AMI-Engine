"""Explicit migration of fixed test responses; never used by application code.

Older test declarations contain a now-unused scripted mapper summary. The new
wire fixtures keep their evidence/state/scope but deliberately omit that summary.
Malformed-wire tests must bypass this helper and test the schema directly.
"""
import copy

from src.pilot._source_selection import SourceSelection, WIRE_VERSION


def selection_fixture(schema, value, **kwargs):
    if issubclass(schema, SourceSelection):
        value = copy.deepcopy(value)
        value['wire_version'] = WIRE_VERSION
        for component in value['components']:
            component.pop('short_answer', None)
            component.setdefault('gap_anchor', '')
    return schema.model_validate(value, **kwargs)
