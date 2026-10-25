# Evidence mapping and safe abstention - 2026-10-24

**Implementation saved; offline tests passed; local quality gate failed.** All five local attempts failed mapping validation. No usable new brief or valid abstention was produced. This is an assistant-authored technical assessment, not a new human rating or evidence of production readiness.

## Owner judgments preserved

Your five narrative judgments in the edited [October 23 diagnostic report](draft-usefulness-2026-10-23.md) are preserved verbatim with their source hash in the [dated adjudication record](evidence/adjudication-2026-10-24.json). That sidecar records completed owner review of those earlier outputs. Historical report status fields and the completed human-review CSV remain unchanged; external reviewer usage remains pending.

## Implementation

- The opt-in pilot uses `analyst-pilot-v1.4` and `requested-evidence-v1`. Its existing three-node graph now maps evidence inside composition, with at most four workflow calls: two tool rounds, one map, one composition. Scope rejection and empty retrieval use fewer calls.
- The private mapping contract records requested anchors, supported/partial/missing/conflicting status, short answers, source quotations, measure/scenario/kind, and shared geography/period. Validation checks anchors, known source IDs and quotations with whitespace normalization. Malformed or unsupported mapping claims fail explicitly without repair calls.
- The private composition contract links claims to components and restricts citations to each component's mapped evidence. Missing supported components use mapped short answers as deterministic fallbacks, still subject to the unchanged NeMo check. Application-generated gaps identify unresolved requested components; unsupported background claims are disallowed by contract.
- A valid mapping with no supported component skips composition and returns an empty-claim draft with your exact no-information message and specific gaps. It is shown as a warning rather than an HTTP exception so the public Draft/API shape and evidence inspection remain available. Empty claims cannot be approved/exported. Invalid mapping is a separate workflow failure.
- Geography/period are added to titles when established. One `as_of` date is shared by mapping and composition; relative dates are resolved without using publication date as observation evidence.
- The UI and new Markdown exports display zero-based indexes as reader-facing PDF pages. Index 6 displays as PDF page 7. Missing/invalid values show unavailable. Raw indexes and cached approved export bytes are preserved. This presentation fix does not supply missing d04 retrieval evidence.

Public schemas, endpoint signatures, SQLite DDL, retrieval ranking, local model/settings, dependency manifests, legacy agent and existing benchmark formats are unchanged. Component tracking/quotations are structural controls, not proof that a model's answer is relevant or entailed by its quote.

## Offline and browser validation

- **140 tests passed, 3 warnings, 15.51 seconds** against the prior 100-test baseline. Targeted suite: **72 passed, 2 warnings**.
- Tests cover complete/partial/missing/conflicting maps, invalid quotes/anchors/citations, missing-component fallback, model failures without retries, historical/projection/relative-date contracts, existing injection/tool boundaries, final guardrail rejection, approval/export behavior and cached export preservation.
- The new call budget is tested with fixed responses. Mocked model tests establish wiring and structural checks, not the local model's ability to follow the mapping contract.
- Browser inspection used synthetic sources and no model calls. Both citation selection and source inspection showed PDF page 1, PDF page 7 and unavailable labels. The temporary localhost QA server and tab were closed. The [screenshot](../../reports/workflow_pilot/evidence-mapping-2026-10-24/browser-page-labels.png) is automated QA, not external usage.
- An initial quotation fixture was corrected to use exact source text. A transient Windows Application Control native PyArrow import block cleared on a direct import and rerun; no package or security settings were changed. Tests ran outside the sandbox because Windows asyncio needs internal loopback sockets.

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/evidence-mapping-full
```

## Exactly five local attempts

The selected cases used the unchanged local Ollama model, 4k context, 900-token output cap and temperature zero. Raw structured output, parsed mapping candidates, tool traces, source snapshots, usage and failures are retained. No additional judging or retry occurred.

| Case | Outcome | Blocking observation |
|---|---|---|
| d01 | Validation failure | Marked supported without answers or quotations. |
| d02 | Validation failure | Marked supported without answers or quotations. |
| d03 | Validation failure | Marked supported without answers or quotations. Also used source headings/unrequested text instead of verbatim question anchors. |
| d04 | Validation failure | Marked supported without answers or quotations. |
| d06 | Validation failure | Marked supported without answers or quotations. Did not reach the valid no-information response. |

The model omitted the optional `short_answer` and `evidence` fields from its raw JSON. Pydantic supplied empty defaults, so the response parsed structurally, then failed the required supported-answer/quotation checks. Several components were labels for geography/period or unrelated topics rather than answered request components. Rejection prevented unsupported content from reaching composition, but **rejection is not a successful answer or a valid abstention**.

All five mapping calls ended with `stop`, not a length-limit finish reason; outputs were 143-352 tokens. The retained records do not show output truncation as the cause. Model/schema interaction is the observed bottleneck; this does not establish that all open-source models fail or that a hosted model is required.

Composition calls: **0**. NeMo invocations: **0**. Fallback, final NeMo and exact-message behavior passed offline tests but were not reached with the real local model in this run.

Total: 15 workflow calls, 19,395 known input tokens, 2,052 known output tokens, 75.90 workflow seconds. Each attempt used three calls, below the four-call cap. Monetary/hardware cost is unmeasured; usage is conservatively marked incomplete.

## Next step and release status

1. **P1: simplify and strengthen the model-facing extraction contract.** Make answer/evidence fields explicit requirements rather than optional defaults, use compact extraction-focused synthetic examples, and prevent question decomposition into unrelated source headings. Preserve exact quotation and question-anchor validation; do not weaken them to accept this run.
2. Validate the revised mapping separately before expanding workflow capability. A future real-generation budget must use a new directory and retain these failures. This pass has exhausted its five-attempt allocation; no automatic further experiment was run.
3. After mapping works, address multipart retrieval and complete source spans, including regional demand and nickel, as a separate change. Prepare fresh facts before making later quality claims.
4. Hold external reviewer sessions until a usable end-to-end workflow passes its quality checks. Owner comments are already sufficient to define this pass's acceptance criteria; no new manual rating is needed to establish these technical failures.

**Verdict: Request Changes.** Saved code is reviewable but is not qualified for reviewer use or production claims. No commit, push, deployment outside localhost, Ragas run, hosted inference or reviewer contact occurred.

The [local review packet](../../reports/workflow_pilot/evidence-mapping-2026-10-24/review-packet.md) contains unchanged questions, raw mapping outputs and source locators. The [structured record](evidence/evidence-mapping-2026-10-24.json) and [integrity verification](../../reports/workflow_pilot/evidence-mapping-2026-10-24/verification.json) provide machine-readable findings.
