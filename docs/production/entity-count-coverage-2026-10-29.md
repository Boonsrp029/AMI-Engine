# Entity/count evidence coverage — 29 October 2026

**Offline repair verified; actual v1.51 model quality is unassessed after a lifecycle timeout.** The subsequently authorized mapper check hit its process deadline without a retained response; the full workflow was not started. See [lifecycle findings](diagnostic-v151-findings.md). This repair follows the [v1.50 r06 source failure](diagnostic-v150-findings.md), where both counts were retrieved but omitted. Grounding alone did not establish responsiveness.

## Functional changes

The private evidence layer recognizes explicit binary requests of the form “Did A or B have more/fewer projects?”, optionally qualified by a year. It carries the literal entities and measure into mapper instructions. Unrecognized comparisons retain their existing path; no country aliases, nationality inference, generic table parser or new public schema is introduced.

Each entity needs a selected integer project count in a declared entity-before-count clause. Supported comparisons require both unambiguous roles, shared pinned document identity when using different records, and no explicitly incompatible selected reporting periods. Background, monetary values and growth percentages cannot fill a count role. A qualitative winner inconsistent with the selected counts is rejected before composition. Unknown parsing does not establish that information is absent: an invalid supported mapping fails explicitly rather than being converted into an abstention.

When eligible role candidates are disjoint, decoding selects a passage for each entity. A span containing both roles can be selected once; duplicate IDs are not manufactured. When the catalog contains competing counts, additional relevant count passages remain available so a genuine conflicting state can retain its evidence. Partial, missing and conflicting states remain explicit; the application does not invent a winner or fill missing evidence.

Both selected count passages stay together as one composition unit. Final checks require correctly attributed counts and reject swapped/omitted values or a contradictory explicit winner. Instructions request clear entity-before-count wording. Failure raises before final NeMo; successful nonempty drafts still require the existing final NeMo check and human approval for export. There is no silent re-selection, computed replacement claim, model repair loop or automatic approval.

These are literal-role and structural checks. They do not prove source truth, general entity identity, unknown date/scenario applicability or semantic entailment. Unsupported prose forms can fail conservatively and require diagnosis. The final source-quality gate and human judgments remain necessary.

## Evidence

Final suite: **826 Windows tests / 825 Linux tests plus one Windows-only skip / 15 existing warnings**; 88 targeted checks and clean `pip check`. Tests cover complete, partial, missing and conflicting evidence; shared spans; grouped integers and ties; cross-document/corpus mixing; incompatible periods within and across spans; background/instructions; omitted/swapped counts; wrong winners; model-call bounds and final guardrail failure. Earlier 820/823/825-test checkpoints are retained rather than represented as final evidence.

The frozen r06 replay rejects its original background selection with zero model calls. Controlled count assignments pass the repaired contract and remain one comparison unit; this is test evidence, not a corrected generated result. A three-case fixed-response harness uses actual engine preparation/validation, reproduces the frozen final mapper input and rejects background/wrong-winner responses without inference.

Final local image `ami-pilot:qualification-4278d28a19803272`, ID `sha256:943289b4621b5594898d79d336fb8678e2cbf8be4600275ff68cde7da7fc5d5e`, corresponds to context `4278d28a19803272520c4463a4d22810d764a27558e11e1a495c3800d494da80`. Offline Linux tests verify packaged source hashes with networking disabled. Restart/recovery preserves all four cached approved exports using a read-only backup and disposable storage. Docker Desktop was initially stopped; its retained failed build was followed by a successful CLI start/build. No real container inference or production operation is established.

Logs, contracts, replay, contexts, initial/final test results and recovery evidence are in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v10/`. Prompt `analyst-pilot-v1.51`, mapper `requested-evidence-v36`. Model/digest, 4096-context/900-completion/temperature-0 settings, four-call ceiling, public APIs/`Draft`/SQLite, source corpus, retrieval ranking, page labels, legacy graph and dependencies remain unchanged.

## Owner evidence and next gate

The [r05 owner adjudication](../pilot/owner-review-v150-2026-10-29.md) records the supplied baht comparison and additional sectors, unchanged approved claim 2, and case-specific warning disposition. The original generated draft, judgments/CSV and approved exports remain unchanged. This editorial candidate is separate from model quality and creates no stored approval/export.

The [r06-only diagnostic](diagnostic-proposal-v151.md) was authorized and stopped at its mapper deadline. The initial unexecuted prototype and authorized final `-v2` contract remain historical; neither permits a new call. No active inference grant or twenty-case authorization exists. No further scoring of r05's original output is requested, and there is no new r06 response to score. The full portfolio/production Goal remains incomplete.
