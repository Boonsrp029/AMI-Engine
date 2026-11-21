"""Reconstruct the retained fact-check prompt using a fixed local test double."""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from src.pilot.launch import configure_event_loop
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan


def main():
    configure_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    spec = importlib.util.spec_from_file_location("grounding_fixture", "tests/test_guardrail_grounding.py")
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    folder = Path("reports/workstream-c/scoped-capacity-selection-development-2026-11-19")
    contract = json.loads((folder / "development-contract.json").read_bytes())
    case = contract["cases"]["cq1-a40"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    sources = [result.source for result in report.sources]
    retained = json.loads((folder / "source-check.json").read_bytes())
    claim = retained["safety"]["raw_output"]
    context = "\n".join(source.content for source in sources)
    assert retained["span"] in context
    results = {}
    for answer in ("YES", "NO", "YES, the source supports it."):
        with pytest.MonkeyPatch.context() as patch:
            guard, judge = fixtures.runner(patch, answer)
            result = guard.validate_output(claim, context, plan.query)
            prompt, = judge.prompts
            assert claim in prompt and context in prompt and "{{" not in prompt
            assert result["passed_guardrails"] is (answer == "YES")
            results[answer] = {"passed": result["passed_guardrails"], "rail": result["blocking_rail"]}
    result = {"contract_sha256": contract["contract_sha256"], "fixed_judge": True,
              "model_calls": 0, "question": plan.query, "claim": claim, "span": retained["span"],
              "source_ids": [source.source_id for source in sources], "evidence_chars": len(context),
              "prompt_chars": len(prompt), "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
              "reconstructed_prompt": prompt, "fixed_verdict_results": results}
    with (folder / "safety-prompt-replay.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
    print(json.dumps({key: result[key] for key in ("source_ids", "evidence_chars", "prompt_chars", "fixed_verdict_results")}))


if __name__ == "__main__":
    main()


