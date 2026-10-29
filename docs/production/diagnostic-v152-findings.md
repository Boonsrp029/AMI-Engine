# r06 v1.52 diagnostic — 29 October 2026

**Mapper passed; full workflow failed before NeMo. Allowance closed.** This was one authorized mapper-only preflight and, after its technical/source checks passed, one full r06 workflow. No retry, Ragas, hosted inference, twenty-case run, approval or export occurred.

The mapper preflight returned supported answers `73%`, `Singapore` and `China`, with the correct selected passages and no false conflict. It completed in 35.735 seconds (service child 16.359 seconds; offline validation 19.234 seconds), using 2,520 input and 143 output tokens. These are one-case observations, not sustained performance or owner acceptance.

The full workflow also retrieved and mapped the correct evidence. Its composer then returned a 25% FDI growth heading for the requested 73% share and repeated the Singapore value/count passage for the China-versus-Singapore comparison, omitting China and its 810 projects. The final project-count validator rejected the incomplete comparison. No final draft was returned and NeMo was not invoked. The observed terminal failure is `ValueError` at `_entity_comparison.validate_composed_comparison`; it is not a timeout or schema-parsing failure.

## Confirmed input gap

The saved `composition_input` contains `as_of`, evidence units, component IDs and established scope. It contains neither the original question nor per-component request anchors or mapper summaries. Thus the composer is instructed to answer the requested comparison without receiving the text that identifies each unit's request. The missing request context is a confirmed implementation gap. The response also shows model omissions; adding context cannot guarantee their disappearance.

The source-only design deliberately avoided leaking unverified question dates/geography or lossy mapper answers into factual claims. The [v1.53 repair](composition-request-context-2026-10-29.md) preserves that factual boundary and forwards a separate validated request block. It does not forward mapper summaries or silently repair the failed output.

## Budget and retained evidence

The full attempt recorded four main calls and zero NeMo invocations, 4,914 input + 468 output = 5,382 known tokens, and 34.256 seconds of worker execution. Including the separate mapper preflight, the grant consumed **five main calls, zero NeMo invocations and 8,045 known tokens** (7,434 input / 611 output). All responses ended with `stop`; no output truncation or GPU error is recorded. This evidence does not establish hardware or model-family incapacity.

Local evidence remains in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v12/`: exact authorization/protocol, mapper transport/validation/source gate, `development-v152/attempt-r06.json`, raw model outputs, tool/evidence traces, process/budget records, `failure-assessment.json` and `actual-v152-result.json`. All 269 pre-run source hashes and 376 pre-run evidence hashes matched after execution. Original source snapshots, judgments and approved exports remain unchanged.

No owner scoring is requested for this failed draft attempt. A future assessable output still requires owner factual/completeness review before acceptance and exact-revision approval before export. New actual generation requires a new predeclared allowance; unused NeMo allowance cannot fund a retry. Portfolio and production qualification remain incomplete.
