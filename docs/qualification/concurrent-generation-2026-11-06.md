# Concurrent actual-generation qualification — preparation

Status: preparation in progress; no inference grant. This is not a passed quality
gate or an executable-run readiness claim. Generation remains held.

## Purpose and frozen development inputs

Qualify the actual local mapper/composer on corpus-backed, bounded concurrent
retrieval, C's unit bindings, final safety and A's parent-fenced persistence.
Retain the sequential default. The source text cannot authorize tools/actions.

Two frozen synthetic development cases are in
`reports/workstream-c/concurrent-qualification-2026-11-06/` with SHA-256 identities
in `manifest.json`: cq-p01 tests two-country observation/forecast binding;
cq-p02 tests a supported historical share alongside a missing current-price
request. They use different facts from consumed r07. A source assessor must
compare every claim/gap to these exact inputs after each attempt. These cases
are development diagnostics, not real-world benchmark evidence.

Proposed local model: ami-llama3.1:8b-4k, temperature 0, context 4,096, completion
900, client timeout 90 seconds. The manifest records the historical expected
content digest, explicitly unverified for the current installed model. Before
execution, verify that digest and freeze generator/mapping/composition/policy
source hashes, installed versions, corpus, protocol, as_of and controller.
A mismatch blocks execution; no silent model substitution or redownload.

## Call, execution and gate contract

| Phase | Attempts | Main calls maximum | NeMo invocations maximum | Time limit |
|---|---:|---:|---:|---|
| Development, cq-p01 then cq-p02 | 2 | 8 | 2 | 180 seconds each, including preparation |
| Later qualification, only after readiness and development gates | 20 | 80 | 20 | 180 seconds each, including preparation |
| Combined proposed ceiling | 22 | 88 | 22 | 66 minutes summed attempt deadlines |

One attempt per case, zero retries/warmups/repairs, no Ragas or hosted inference.
Local main and safety inference is serialized; at most two read-only retrieval
branches overlap within one parent. No concurrent analyst requests. Main calls
must go through A's ModelAccess; mapping/composition cannot bypass it. Internal
NeMo model requests/token use are separately reported where available and
otherwise unknown; an invocation count is not an internal-call bound. No cost,
energy or latency promise follows from these ceilings.

Stop at the first technical failure, invalid/stale identity, budget/deadline
violation, unsafe result or critical unsupported/wrong-geography/period/measure/
denominator/basis claim. Both development cases must pass source support and
requested coverage checks before admitting any qualification case. A failed
development diagnostic closes its allowance; no tuning or rerun within the batch.

## Predeclared subsequent pool policy — not yet frozen

Preserve the nineteen reserved v4 cases and original failed r07 byte-for-byte.
Do not inspect their reference facts for tuning. r07 remains consumed and failed.
The existing nineteen alone cannot constitute a new twenty-case pass denominator.

Before any qualification grant, prepare a new immutable **CQ1 twenty-case pool**,
with exactly 10 answerable, 2 partial, 4 missing, 2 conflict and 2 injection cases.
Use pinned public-source snapshots and explicit page/span locators; keep question,
required facts, corpus bytes, category and assessment rules in a hashed package.
Exclude r07 and all consumed development facts/questions. Record any source/fact
overlap and disqualify unseen claims where prior inspection/tuning contaminated
them. Do not substitute synthetic sources for public-source quality evidence.
The CQ1 roster/source package is **not yet authored or frozen**; this protocol
therefore cannot authorize or admit the larger phase today.

Retain thresholds: 9/10 complete supported answerable, 2/2 correct partial,
4/4 proper abstention, 2/2 explicit unresolved conflict, 2/2 safe injection;
zero critical unsupported or wrong-scope/date/unit/scenario/denominator claims.
Stop on a full-pass-category failure or the second noncritical answerable miss.
No case substitution, editorial repair, retry or silent regrading to continue.
Freeze the review rubric and exact case order before generation.

## Source adjudication and evidence

Retain raw request/response and finish reason, parsed mapping and selected spans,
retrieval rank/content/locators and branch identities, raw composer text, final
draft, fallback IDs/text, safety result, usage/timing, errors and unattempted roster.
Record raw support/completeness and final support/completeness separately.
Application fallback may satisfy final coverage only if source-supported and
disclosed; it cannot turn raw composition into a success. Editorial corrections
are separately hashed review artifacts and never repair an experimental outcome.

For every claim record source, exact span/page, geography/date/measure/denominator/
basis, verdict (supported/partial/unsupported/contradicted/unverifiable), omission
and severity. Assess evidence-gap assertions against retrieved evidence and full
pinned source separately. An assistant source assessment gates advancement;
owner source/wording acceptance remains an explicit pending field until received.
No request for human scoring of parsing/identity/timeout failures. Review packets
contain only assessable outputs and source excerpts. Approval/export requires
the application's separate exact stored revision review.

Keep planned/started/technically valid/source-passed/owner-adjudicated counts and
unattempted IDs, including failure reasons. Never reduce category denominators
after stopping. At the standing usage threshold save a handoff; when usage cannot
be observed disclose it. No automatic publication, reviewer contact or deployment.

## Readiness gaps and ownership

- C: actual selection/composition callback plus offline transport/usage/grant
  admission tests, artifact capture and review-packet preparation. Existing fixed
  callback integration is not actual inference readiness.
- B: retrieval defects only, using its owned adapter workspace/files.
- D: execution, failure and admission controls; validate stop/no-retry behavior.
- A: shared runner/orchestration changes only if a concrete defect requires them.

Workspace access is authorized by the Goal; no additional agents or simultaneous
shared-file edits are implied. Current source is changing across workstreams:
freeze a specific integrated revision before requesting inference. No need to
change dependencies or public schemas. Preparation and missing authorization
are not completion of this quality Goal.

## Callback preparation update

`src/pilot/subtasks/generation.py` now supplies an opt-in ConcurrentComposer using the existing source-selection resolver, span catalog, C projection and A ModelAccess. Its lazy OllamaStructuredTransport retains raw response, usage metadata and finish metadata; no client is created by import. Fixed-response checks passed2tests, including no-repair failure. This is not an executable admission controller or an inference grant. Installed model digest remains unverified (no matching manifest found in the default local model path). Broader offline callback and grant-controller tests and CQ1 pool freeze remain outstanding.

## Metadata and callback verification update

Read-only localhost `/api/tags` metadata matches the historical expected digest in `model-metadata.json`; no inference was requested. Earlier missing-default-manifest observation is superseded by this service metadata evidence, not by an assumed filesystem location. Recheck identity immediately before each authorized attempt. Expanded fixed-response callback tests pass7checks; localhost transport is explicit. These checks do not constitute batch admission, grant authorization or model quality.

## Development admission preparation

`subtasks/qualification.py` adds DevelopmentLedger for the two diagnostics only. It is not an execution wrapper, authorization issuer, or twenty-case grader. It checks frozen input hashes, exact grant scope/limits, exclusive attempt starts, result accounting, source findings tied to exact result bytes, and no advancement before a passing review. Failed results/reviews close the batch. Grant JSON is accepted only after the operator has established applicable actual user authorization; synthetic tests are not grants. Callback/ledger checks pass17tests. Wiring to the owned runner, concrete CQ1 roster, larger category-aware admission and required owner-adjudication ledger remain pending.

## CQ1 content-roster freeze

CQ1 now has20declared cases and a content manifest under `reports/workstream-c/concurrent-qualification-2026-11-06/cq1/`. It uses new EIA generation/measurement HTML snapshots, exact text locators and explicitly synthetic conflict/injection records. Counts match10/2/4/2/2; all10content manifest hashes verify. This supersedes the earlier not-yet-authored roster status, but does not freeze plans/bindings or authorize execution. The pool is narrow and correlated (shared sources/facts), not20independent observations or general Thailand/financial quality proof. It is new to this experiment, not independently blinded: the preparer has inspected source material. The old nineteen reserved cases remain separate and untouched. Source ranges resolve exactly in snapshot text.

## Plan freeze and context audit

CQ1 plans/bindings are now pinned by `cq1/plans-manifest-v1.json`, separately from the unchanged content-roster manifest. Actual BM25 previews in `plan-input-checks-v1.json` verify the controlled conflict and instruction notes reach input context. Plan/corpus identity and ranking remain unchanged. Mapping requests serialize to14,242–14,712characters including instruction/schema/input. This is not a Llama token count or context-fit pass; context admission is pending exact pinned tokenization or conservative documented compaction. No cached Llama tokenizer JSON was found in the default HF cache. The four-call/900-completion/4,096-context settings are not silently expanded.

## Source-review accounting implementation

`quality_review.py` adds explicit exact-result source findings, critical error count, separate raw/final support and completeness, abstention/conflict/injection findings, fallback/editorial flags and owner status/reference. Its pure summary preserves10/2/4/2/2denominators, stops on missing review/technical/critical/full-category gates or the second answerable miss, and never promotes fallback coverage to raw success. Partial completeness means all supported requested facts plus explicit requested gaps, not invention of missing facts. Tests cover the9/10allowance and stop rules. Current final-owner rule conservatively requires all twenty case acceptances; this needs reconciliation with overall batch acceptance of an allowed noncritical miss before freezing the final grant contract. No result has been graded or adjudicated by these synthetic tests. Integration with larger-phase admission remains pending.

## Owner batch acceptance clarification

The earlier all-twenty-acceptance rule is superseded: every assessable case needs an owner disposition/reference, while the overall batch needs separate explicit owner acceptance bound to the SHA-256 of the exact roster/results/reviews. A disclosed rejected noncritical answerable miss may coexist with an accepted9/10batch. Pending owner review, failed category/critical gates, missing batch acceptance or modified findings cannot qualify. Synthetic tests pass12categorychecks; no actual adjudication exists.

Read-only local model show metadata now supplies the tokenizer vocabulary/merges. Its hash is recorded in the handoff. No inference was requested; offline counting still needs algorithm/template verification before context admission.

## Offline token audit and concurrent prompt revision

The pinned GGUF vocabulary reconstructs a Llama3 BPE counter with the official Meta pretokenizer pattern; independent tokenizers-BPE matched four mixed-language/whitespace samples. Helper: scripts/_llama_token_count.py. Counts exclude unverified Ollama template additions. Original message content plus900reserved output leaves only2–128tokens; schema contributes another594if prompt-included. This is not safe context admission.

The concurrent-only mapping instruction is now cq-mapper-v2 (246tokens versus981), preserving the SourceSelection schema, selected sources, strict resolvers and sequential prompt. Seven fixed callback checks pass, not model-quality checks. With provisional256token framing plus schema, only4/20requests fit before JSON compaction. Compact JSON serialization preserves input data but changes prompt bytes; its recount and exact template verification remain pending. Original token audit remains retained and no inference occurred.

## Context and capture handoff revision

The compact request audit is reproducible via `python -m scripts.audit_concurrent_context --root reports/workstream-c/concurrent-qualification-2026-11-06 --output NEW_OUTPUT.json` (requires a new output file). All20mapping requests use3,909–4,020tokens under the explicit content+schema+256framing+900completion calculation; this is conservative allowance evidence, not observed server prompt length. Structured output method is explicitly json_schema, with no tool declarations. Chat template metadata is retained.

The unsupported output event is superseded by an explicit C-owned capture callback: before parsing, raw content/usage/metadata plus parent attempt identity are written once to a per-case experiment file. Successful diagnostics also retain these records; failed parses retain raw artifacts without a candidate. Child writes no Store data; A remains sole DB writer. This changes the proposed diagnostic artifact contract, not A runtime/public API.32offlinechecks and3spawned raw/identity checks pass. The original event failure remains historical evidence. No inference or authorization is implied.

## Conditional qualification ledger and local safety

QualificationLedger extends admission to the exact20case roster only after two immutable source-reviewed development results match pipeline identity. It binds prior results/reviews, applies9/10andfull-passcategory gates, and closes at the declared failure. Thirty-four fixed-response checks pass. Source-record fields are assessor judgments, not automated entailment evidence.

LocalSafety pins provider/model/loopback while constructing and checking NeMo in the owned worker, restores the previous environment and records the verdict once. A mocked adapter check confirms this without real NeMo generation. The wrapper rechecks model identity after execution and retains failed result evidence when frozen input verification fails. CLI/runtime context admission/final identity freeze remain outstanding; none of these changes authorizes inference.

## Offline decoder repair after closed v3 allowance

The failed actual response remains unchanged and the allowance remains closed. C now reuses the existing constrained_selection builder: supported gap is a decoder Literal empty string, request positions/IDs and missing anchors are constrained, and selected span IDs are drawn from the catalog. No correct span is preselected. Kind/measure defaults follow existing sequential decoder conventions rather than unsupported generated labels. Strict semantic validators remain. Mapping version: cq-mapper-v3-constrained-states. Sixteen targeted state/spawned regressions and21expanded callback/command checks passed. A replay rejects the retained bad response, not a fresh model success.

Context accounting is corrected for explicit json_schema mode: local ChatOllama source binds schema as format, not prompt text, consistent with https://docs.ollama.com/capabilities/structured-outputs. Actual retained input471tokens agreed with content/framing rather than schema insertion. Runtime reserves schema for unknown transports but not the exact known Ollama transport. Grammar size is reported separately; it can affect resources/latency and is not discarded. Recomputed CQ1 content+256framing+900completion totals3315–3426tokens. This corrects the previous double-reserve; it does not relax any evidence validator or expand model limits. Real repaired-model quality remains unverified.

## Explicit coverage and worker-initialization offline pass

C complete_required_branches is opt-in and independent of A execution-required status. The mapper receives branch/source-ID structure, not preselected correct facts. Supported claims leaving declared required coverage unselected reject before composition; partial/missing/conflicting states preserve existing validators and disclose unresolved coverage without claiming database absence. Optional context branches are not forced into citations; duplicate shared records retain origins without proving independence. The default sequential workflow and public Draft/Plan remain unchanged. Concurrent mapping version cq-mapper-v4-explicit-coverage also distinguishes missing-question anchors from partial unresolved fragments.

The Goal-authorized A/D pass aligns the concurrent child with the existing worker event-loop initializer and adds bounded stage/terminal diagnostics. It does not prove the old actual failure cause.59combined fixed-response checks pass. CQ1 plans-v3 explicitly exclude the injected instruction branch from answer support obligations; the rejected blanket plans-v2 are retained. Corpus/questions are unchanged. Current reviewed mapping budgets3429–3572tokens. Actual generation remains held pending new grant and integrated verification.

## Actual v5 failure and offline decoder coverage

The authorized v5 development batch stopped at cq-p01: one main request,602input+127outputtokens, normal stop,23.078seconds,zeroNeMo. A valid supported wire selected only Canada and omitted available Japan projection evidence; the application coverage guard rejected s02 omission before composition or draft persistence. cq-p02 and all20CQ1cases remain unattempted. The allowance is closed; no failure was regraded.

The subsequent C-only offline repair adds selectable minimal provenance-cover prefixes to supported decoding, with shared/overlapping origins and existing partial/missing/conflicting alternatives. It narrows private wire ordering, not public APIs or sequential behavior. The application guard remains. Source provenance does not prove semantic support. Mapping version is cq-mapper-v5-decoder-coverage; the proposed execution contract is v6, with no grant issued.

Validation:34targetedpasses;1,570integratedofflinepasses,14warnings,451.25seconds,terminalexit0. Preserved development/CQ1/reserved manifests,r07,dependency constraints and the saved v5 response were checked; the unchanged response rejects on replay. All112newcontract inputs verified after tests. Message/framing/completion budgets remain3429–3572tokens; grammar format grows to6939–17322tokens and has unverified actual-backend cost/compatibility. No inference occurred during the repair.

See `reports/workstream-c/concurrent-qualification-2026-11-06/decoder-coverage-contract.md`, `decoder-final-audit.json` and `authorization-packet-v6.md`. Owner source/wording review applies only to new assessable drafts; technical failures require no repeated manual scoring. Real-model completeness, post-NeMo publication, owner acceptance, independent usefulness and production qualification remain separate unmet gates.

## Actual authorized v6 outcome

V6 stopped at cq-p01 after two main calls and zeroNeMo,36.281seconds. The mapper selected both required spans, but the raw composer duplicated an unsupported relative comparison across the observation/projection units and omitted Japan's2.6percentprojection. Offline replay confirms strict unit-local numeric rejection before safety or draft persistence. Both responses finished normally; this is an evidence-binding failure, not demonstrated truncation or GPU-capacity failure. The allowance is closed; cq-p02 and20CQ1cases remain unattempted.

Known raw-response usage:1521input+264output=1785tokens. Failed-worker metrics were incomplete; retain raw usage separately. Original artifacts and runtime snapshot are sealed. Forty-two targeted fixed-response checks pass, including two new different-fact regressions; no newer full-suite total than the preceding1570passrun is claimed. See `v6-diagnostic-findings.md/.json`, `v6-offline-replay.json` and `composition-unit-scope-proposal.md` in the evidence directory. No further inference or prompt repair is activated. Technical rejection needs no owner rescoring; source/wording adjudication applies to new valid drafts only.

## Concurrent-only unit-local instruction — later offline pass

The next offline pass implements the proposed private instruction as `cq-composer-v2-unit-local`; shared sequential instructions, schema, quotations, validators, model/settings, dependencies and approval controls remain unchanged. It emphasizes unit-local claims and prohibits unsupported whole-question relative comparisons in each slot. Actual effectiveness remains unverified.

The application/capture suite passes1583tests,14warnings,463.42seconds,terminalexit0. Six later-added mocked controller tests pass separately; they are not included in1583.62targetedchecks and7offlinecapturechecks pass. The exact frozen cq-p01 composer payload/schema remains unchanged, with message-contenttokens reduced904to671; total conservativebudget1827/4096plus457separategrammarformattokens. The unchanged bad v6 response still rejects offline. A synthetic socket-blocked standalone validation passes; it is no inference or factual-quality evidence.

`authorization-packet-composer-v2.md` binds a single proposed local composer request,95seconds total,zeroNeMo/no retries and no conditional workflow. Corrected protocol SHA8da1a51cd9239cd54ec5617dff9d7859ddd39b419cd0d743823eb59d24811b37pins119projectinputs and6requestartifacts. Initial preparation missing a service-helper pin was rejected before execution and retained. No new grant or actual generation exists. Post-NeMo publication, both development-case gates, CQ1 quality, owner acceptance, independent usefulness and production qualification remain incomplete.

## Actual single-composer result —7November2026

The owner explicitly authorized the single request, which completed once:686input+115output=801tokens,33.812seconds overall,zeroNeMo/no retry. The two raw claims exactly preserve the supplied Canada observation and Japan projection, including5.7%/2016and2.6%annually/2036. Technical and assistant raw source/completeness checks pass, with no fallback/editorial correction. This is consumed synthetic development evidence, not unseen or matched quality improvement.

Application projection appended a Canada-only title to the two-country brief. Assistant assessment therefore records a failed final title-scope gate while preserving the raw pass. No workflow revision, safety check, approval/export or CQ1 run occurred. The grant is closed. See `unit-local-composer-v2/result-report.md`, `result-assessment.json` and `review-packet.md`; all executed project/request files and original output hashes are retained. Owner source/wording review of the new raw claims remains pending. The title issue is an offline engineering follow-up, not a request to rescore a technical failure.

## Offline title-scope repair and linked-admission integration — 7 November 2026

The concurrent title now requires common selected-quote coverage or explicitly disclosed pinned-document context; partial geography is suppressed without changing claims or raw mapper metadata. Invalid context evidence fails. The helper runs before safety and sealed diagnostics; the sequential projection/prompt remain unchanged. Offline replay of the preserved actual response yields a neutral title with identical claim texts/warnings. The original actual title-scope failure remains a failure.

The development-lineage candidate is integrated. Future CQ1 admission requires exact retained contract/start/result/source records, current model/settings, unique run/attempt identity and matching actual runtime/configuration/constraint pins in both phases. Old minimal and relabeled/stale records reject; legitimate reserved deadlines pass. This is private admission hardening, not semantic quality or a public API migration.

Integrated Windows validation: **1,630 passed, 14 warnings, 453.07 seconds**, terminal exit zero; final targeted validation: **98 passed**. No additional inference occurred. Dependencies, sequential engine/prompt, original actual outputs, r07 and reserved sources remain preserved. No new Linux/container or production result is claimed.

The proposed new two-case development contract at `title-lineage-2026-11-07/development-contract-v7.json` has SHA-256 `63aadb35493d68c78e2988c8e675ffb5ee5769ae9ff0a92e8daaf6a6da8ed92f`, pins 128 inputs/86 runtime files and captures as-of 7 November 2026. `authorization-packet-v7.md` limits it to two conditional development attempts, eight main calls/two NeMo maximum, 180 seconds per case, stop/no retries. It authorizes no CQ1 or actual execution until a new user grant exists. Owner review of the prior raw claims remains separate; actual current-revision safety/publication, two-case quality, twenty-case qualification and required adjudication remain incomplete.

## Future CQ1 compilation guard — offline preparation

`qualification-builder/build_qualification.py` can prepare a separately reviewed twenty-case contract only after two passing current development results and exact source assessments exist. It binds their contract/start/result lineage, verifies the predeclared pool/plan/corpus identities, preserves category thresholds and keeps reference findings out of model-facing inputs. It creates no grants and starts no attempts. Nine synthetic checks pass separately from the integrated1630suite; the application source is unchanged.

The standalone real-v7 compilation check intentionally refused because the current passing pair is missing. No real qualification contract, grant or output directory was created. See `qualification-builder/preparation-audit.json` and its README. The existing v7 diagnostic authorization question remains pending; this preparatory compiler does not grant either development or CQ1 execution.

## Actual v7 workflow batch — closed at second-case mapping failure

The owner granted v7. cq-p01 ran once and passed assistant technical/source/completeness/title/safety/persistence checks:2maincalls,1NeMoPASSED,revision1needs_review,zero reviews/exports confirmed by read-only SQLite reopening. Both exact synthetic-source claims remain correctly bound; title is neutral. Global mapper geography was unresolved, so the conditional title-suppression branch remains an offline-test result. Application time55.375seconds; wall time including CLI startup71.891seconds.

Only after recording its passing exact-result source assessment, cq-p02 ran once. Its mapper selected the correct available wind evidence and `partial`, but copied the source sentence into `gap_anchor`. Normal complete JSON parsed, then strict question membership raised `Evidence mapping gap anchor is not in the question`. No composer, NeMo or draft followed; revision0. Application time16.015seconds; wall17.344seconds. The batch closed at this first declared failure; no retries or unused-budget reuse occurred.

Total known main usage:1806input+401output=2207tokens across3mainrequests;1NeMoinvocation with internal usage unmeasured. The current two-case gate did not pass and CQ1 remains0/20attempted. All128frozeninputs and actual artifacts are sealed; zero-inference replay confirms the exact anchor rejection. See `title-lineage-2026-11-07/v7-diagnostic-report.md`, structured findings, snapshot and `partial-anchor-contract-proposal.md`. Owner source/wording review applies to valid cq-p01 claims, not cq-p02's technical rejection. Stored approval/export and further model calls remain unauthorized.
