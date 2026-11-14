"""C-owned activation adapter; A must opt in explicitly at the runner call site."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .contracts import Plan
from ._disclosures import DisclosureScopes, validate_scopes
from ._scoped_generation import ScopedConcurrentComposer
from .generation import ConcurrentComposer


CONTRACT_VERSION = 'cq-scoped-composition-v1'


@dataclass(frozen=True)
class DeadlineBoundScopedComposer:
    declared_plan: Plan
    runtime_plan: Plan
    bindings: dict
    as_of: str
    transport: object
    declared_scopes: DisclosureScopes
    scope_file_sha256: str
    capture: object = None
    complete_required_branches: dict | None = None

    def __call__(self, report, access):
        declared = Plan.model_validate_json(self.declared_plan.model_dump_json())
        runtime = Plan.model_validate_json(self.runtime_plan.model_dump_json())
        scopes = validate_scopes(declared, self.bindings, self.declared_scopes)
        original, actual = declared.model_dump(mode='json'), runtime.model_dump(mode='json')
        declared_seconds = original.pop('deadline_seconds')
        runtime_seconds = actual.pop('deadline_seconds')
        if original != actual or not 0 < runtime_seconds <= declared_seconds:
            raise ValueError('Only an owned-runner deadline reduction may rebind scopes')
        # This is explicit application binding, not acceptance of a stale scope
        # contract. Preserve the original and executed identities in provenance.
        executed = scopes.model_copy(update={'plan_id': runtime.plan_id})
        validate_scopes(runtime, self.bindings, executed)
        result = ScopedConcurrentComposer(runtime, self.bindings, self.as_of, self.transport,
            executed, self.capture, self.complete_required_branches)(report, access)
        result.diagnostics['scope_deadline_binding'] = {
            'declared_scope_contract': scopes.model_dump(mode='json'),
            'declared_scope_file_sha256': self.scope_file_sha256,
            'declared_plan_id': declared.plan_id, 'runtime_plan_id': runtime.plan_id,
            'declared_deadline_seconds': declared_seconds, 'runtime_deadline_seconds': runtime_seconds,
            'allowed_change': 'deadline reduction only; all other plan fields equal',
            'semantic_support_proven': False}
        return result


def prepare_composer(contract, frozen, runtime_plan, transport, capture):
    """Prepare a callback only; performs no model call and issues no authorization.

    The outer ledger remains responsible for real grants, complete integrity,
    budgets and once-only execution. This helper pins its own extra sidecar.
    """
    kind = contract.get('composition_contract')
    if kind is None:
        if 'requested_scopes' in frozen or 'requested_scopes_sha256' in frozen:
            raise ValueError('Scoped metadata needs an explicit composition contract')
        return ConcurrentComposer(runtime_plan, frozen['bindings'], contract['as_of'], transport,
            capture, complete_required_branches=frozen.get('complete_required_branches'))
    if kind != CONTRACT_VERSION:
        raise ValueError('Unknown composition contract; no silent fallback')
    path = Path(frozen['requested_scopes']).resolve()
    expected = frozen['requested_scopes_sha256']
    pinned = contract.get('input_sha256', {})
    if (not isinstance(expected, str) or len(expected) != 64
            or pinned.get(str(path)) != expected
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
        raise ValueError('Requested-scope sidecar must be an exact frozen input')
    scopes = DisclosureScopes.model_validate_json(path.read_text(encoding='utf-8'))
    declared = Plan.model_validate_json(json.dumps(frozen['plan']))
    validate_scopes(declared, frozen['bindings'], scopes)
    # Validate the runtime cap before constructing any model/client boundary.
    left, right = declared.model_dump(mode='json'), runtime_plan.model_dump(mode='json')
    limit, seconds = left.pop('deadline_seconds'), right.pop('deadline_seconds')
    if left != right or not 0 < seconds <= limit:
        raise ValueError('Runtime plan differs beyond its allowed deadline reduction')
    return DeadlineBoundScopedComposer(declared, runtime_plan, frozen['bindings'], contract['as_of'],
        transport, scopes, expected, capture, frozen.get('complete_required_branches'))
