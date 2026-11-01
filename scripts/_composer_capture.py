"""Offline composer capture/replay over pinned inputs. Never creates a model client.

Logical engine events include frozen tool/mapper replays; they are not new model
requests. Only an explicitly supplied callback can produce a target response.
"""
import json
from contextlib import ExitStack
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts._mapper_transport import sha


class CapturedComposer(Exception):
    pass


class ValidatedComposition(Exception):
    pass


def capture_composer(attempt_path, corpus_path, as_of, callback=None, *, expected_attempt_sha256):
    """Replay fixed tools/mapper; stop before safety after actual draft validation.

    The callback receives the current schema and messages exactly once. It is
    used for frozen-response parsing during offline validation; it is not a
    second inference or judge. No guard verdict is fabricated.
    """
    if sha(attempt_path) != expected_attempt_sha256:
        raise ValueError('Retained attempt identity changed')
    frozen_date = date.fromisoformat(as_of)
    attempt = json.loads(Path(attempt_path).read_text(encoding='utf-8'))
    outputs = attempt['captured_model_outputs']
    if [item['stage'] for item in outputs] != ['tool', 'tool', 'structured', 'structured']:
        raise ValueError('Composer replay requires exactly two tool turns, mapper and composer')
    # Heavy imports occur only inside the separately bounded offline child.
    from langchain_core.messages import AIMessage
    from langchain_core.output_parsers import PydanticOutputParser
    from langgraph.graph import StateGraph
    from src.pilot._evidence import (EvidenceSelection, EvidenceSelectionComponent,
        MAPPING_INSTRUCTION, MAPPING_VERSION, resolve_selection)
    from src.pilot._source_selection import SourceSelection, WIRE_VERSION
    from src.pilot.engine import Corpus, PilotEngine

    # This offline harness can replay a valid historical wire under its original
    # contract. It never adapts it into a new-wire model response. Production
    # engine calls have no such legacy acceptance path.
    retained_mapping = json.loads(outputs[2]['content'])
    legacy = 'wire_version' not in retained_mapping
    (EvidenceSelection if legacy else SourceSelection).model_validate(retained_mapping)
    mapper_contract = 'legacy-model-written-answer-replay' if legacy else WIRE_VERSION

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return cls(frozen_date.year, frozen_date.month, frozen_date.day)

    turns = iter(outputs[:2])
    captured, final_state, events = {}, {}, []
    counts = {'frozen_tool_replays': 0, 'frozen_mapper_replays': 0, 'target_callback_invocations': 0}

    def tool_invoke(_):
        item = next(turns)
        counts['frozen_tool_replays'] += 1
        return AIMessage(content=item['content'], tool_calls=item.get('tool_calls', []))

    def structured(schema, **_):
        if issubclass(schema, EvidenceSelection):
            def mapper_invoke(_):
                counts['frozen_mapper_replays'] += 1
                if counts['frozen_mapper_replays'] != 1:
                    raise ValueError('Unexpected extra mapper replay')
                raw = AIMessage(content=outputs[2]['content'])
                return {'raw': raw, 'parsed': PydanticOutputParser(pydantic_object=schema).invoke(raw), 'parsing_error': None}
            return SimpleNamespace(invoke=mapper_invoke)
        def compose_invoke(messages):
            captured.update(schema=schema.model_json_schema(), messages=[{'type':m.type,'content':m.content} for m in messages])
            if callback is None:
                raise CapturedComposer('Composer input captured without inference')
            counts['target_callback_invocations'] += 1
            if counts['target_callback_invocations'] != 1:
                raise ValueError('Unexpected extra composer callback')
            return callback(schema, messages)
        return SimpleNamespace(invoke=compose_invoke)

    model = SimpleNamespace(bind_tools=lambda _: SimpleNamespace(invoke=tool_invoke), with_structured_output=structured)
    def forbidden_guard(**_):
        raise AssertionError('Composer-only diagnostic must not invoke NeMo')
    original_add = StateGraph.add_node
    def add_node(graph, node, action=None, **kwargs):
        if node == 'safety':
            def before_safety(state):
                final_state.update(draft=state['draft'], sources=state['sources'])
                raise ValidatedComposition('Draft validation completed; safety intentionally not executed')
            action = before_safety
        return original_add(graph, node, action, **kwargs)
    try:
        with ExitStack() as replay_scope:
            replay_scope.enter_context(patch('src.pilot.engine.date', FrozenDate))
            replay_scope.enter_context(patch.object(StateGraph, 'add_node', add_node))
            if legacy:
                def legacy_resolve(value, catalog, question, sources, as_of):
                    return resolve_selection(value, catalog, question, sources, as_of), None
                for name, value in {
                    'SourceSelection': EvidenceSelection,
                    'SourceSelectionComponent': EvidenceSelectionComponent,
                    'SOURCE_SELECTION_INSTRUCTION': MAPPING_INSTRUCTION,
                    'SOURCE_MAPPING_VERSION': MAPPING_VERSION,
                    'resolve_source_selection': legacy_resolve,
                }.items():
                    replay_scope.enter_context(patch('src.pilot.engine.' + name, value))
            PilotEngine(Corpus(corpus_path), model, SimpleNamespace(validate_output=forbidden_guard)).run(
                attempt['query'], lambda kind,payload: events.append({'kind':kind,'payload':payload}))
    except CapturedComposer:
        status = 'captured without inference'
    except ValidatedComposition:
        status = 'passed actual composition validation; source assessment pending; NeMo not run'
    else:
        raise AssertionError('Composer-only replay must stop before safety')
    if any(e['kind'] in {'guard_invocation_started','guardrails'} for e in events):
        raise AssertionError('Unexpected guard event in composer-only replay')
    return {'status':status,'captured':captured,'events':events,**final_state,**counts,
        'mapper_contract':mapper_contract,
        'actual_model_calls':0,'nemo_invocations':0,
        'event_attribution':'logical engine events include fixed tool/mapper replays; not new inference counts'}
