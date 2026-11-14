"""Explicit production adapter from the browser API to A's owned runner."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OwnedSubtaskExecutor:
    """Callbacks for the opt-in runner; branch/composition callbacks must pickle."""

    operation: object
    compose: object
    safety: object

    @property
    def execution_mode(self):
        return "owned_runner"

    def execute(self, store, run_id, plan, corpus_path, *, lease=None):
        from .runner import run_stored_plan

        return run_stored_plan(store, run_id, plan, corpus_path,
                               self.operation, self.compose, self.safety,
                               lease=lease)
