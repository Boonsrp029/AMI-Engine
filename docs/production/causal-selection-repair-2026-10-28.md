> Subsequent actual v1.46 diagnostics stopped at r04: [findings](diagnostic-v146-findings.md). The record below describes engineering verification; it does not override that failed quality gate.

# Causal evidence and comparison repair — 28 October 2026

Prompt `analyst-pilot-v1.46`, mapper `requested-evidence-v31`, unprofiled retrieval policy `pilot-component-lexical-v3`. This is an offline engineering repair after the [failed v1.43 diagnostic](diagnostic-v143-findings.md). **No new model generation or owner acceptance is established.** Historical outputs, failed attempts, owner judgments and cached approved exports remain unchanged.

## Evidence eligibility

Hyphenated financial qualifiers now retain their specific measure, including headline versus core inflation. Stronger synthetic tests use a causal core-inflation distractor; the earlier weak test, whose distractor had no causal marker, remains historical evidence rather than being promoted as proof.

For a causal question, a recognized literal subject and its immediately following demonstrative causal continuation can become one contiguous quotation. The application preserves the source text, content hash, character offsets and original member-span IDs. It never joins source records, crosses paragraph or intervening-subject boundaries, synthesizes text, or exceeds the existing 600-character quotation limit. Long or unrecognized continuations stay separate. Command-shaped source content is not promoted into these reading windows. This is a traceable reading window, not a general pronoun resolver or proof of entailment.

When a complete recognized causal window exists, the subject view requires one such window before optional evidence. Unknown spans remain eligible as extras; known incompatible subjects and instruction-shaped spans remain excluded. Existing profile-specific view contracts keep their priority. The extra-choice enum is shared in the private JSON schema rather than repeated in every tuple alternative. For the consumed r03 source set, static schema size is **5,002 characters**, versus 5,395 previously and 8,975 in the first repair prototype. This is not a measured token count, latency or model-quality result.

## Composition and provenance

After every origin passes scope, measure, number and quotation checks, identical public assertions with identical selected quote text, the same requested component and equal established scope may merge. All citations and unit coverage are retained. A union exceeding the public five-citation limit remains separate; no source is silently dropped. Distinct quotations, different components/scopes and paraphrases do not gain this new merge rule. Existing exact-text/exact-citation sharing is retained. Multiple citations do not establish independent corroboration.

The selected-evidence fallback also recognizes a standalone result-of explanation. A fixed-response workflow test demonstrates retained causal detail, four main calls and one final guardrail invocation; guardrail rejection still fails closed. These scripted responses are not actual model-quality evidence.

## Bounded period proof

A monthly summary before the detailed section may bind to a report month only when every selected summary quotation has its own previous-month or month-on-month cue. The record must lie between the pinned report header and the first explicit section boundary. Detailed records retain the existing bound before the next quarterly/section boundary. Both context records, source/corpus identities and factual content hashes are checked. The two-context/five-citation budgets remain unchanged.

A binding fingerprint detects internal metadata mutation; it does not authenticate an external source. Publication-only, wrong-month, forecast, quarterly, altered-content or ambiguous contexts remain rejected or unresolved. This does not restore the removed unbounded same-document heading fallback. Quarterly request components cannot receive a monthly binding solely because the source contains monthly material.

## Comparison integration

The former comparison path used one component for both periods and another for “which categories explain those directions.” The source-period gate interpreted that second component as monthly-only, conflicting with its required quarterly evidence. The recognized literal comparison grammar now creates two verbatim anchors: one monthly and one quarterly. The subject is copied from the original question into each instruction, which covers direction and categories when requested. No separate anaphoric category slot remains.

Retrieval, source-context validation and coverage checks share those component identities. A quarterly component does not inherit another component's monthly date or an erroneous missing-month warning. Missing quarterly evidence preserves the supported monthly answer and an explicit quarterly gap. Unsupported grammar keeps the prior ordinary request handling. The raw `Corpus.search()` method and Databricks adapters are unchanged; no graph, public schema or framework migration is included.

## Validation boundaries and next gate

Synthetic contracts are in `tests/fixtures/causal_eligibility_v1.json`, `monthly_summary_v1.json` and `comparison_requests_v1.json`, with tests for eligibility, exact provenance, unknown extras, conflicts, partial answers, fallback, date separation, guardrails and citation limits. Initial failing checks are preserved in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v4/`.

A controlled reprojection replaces old selection IDs with the new required source spans and reuses saved composer text. It retains the previously omitted causes, combines duplicate assertions with their citations and establishes December for the applicable claims. It makes zero model or guardrail calls and is **not a fresh generation, quality pass, approval or export**. A separate consumed-source comparison fixture shows agreement between the period and coverage gates; it does not establish complete actual answers.

The v1.44 intermediate suite passed 645 Windows tests; the v1.45 intermediate suite passed 659 Windows tests and its Linux/recovery checks. Final v1.46 checks pass **668 Windows tests /667 Linux tests plus one Windows-only skip**, with 15 existing warnings. Image `ami-pilot:qualification-31eaf5d21672bf11`, ID `sha256:a8edac04886405d4546d544fc12f15ed696c6c21404ee4d36919e8f0f59474fd`, matches sanitized context `31eaf5d21672bf11af67905d8c3204e0df5e26d4d335630e532ed38b07dd2530`. Recovery preserves all four approved exports byte-for-byte and blocks empty d06. Both dependency checks pass unchanged. All model settings, dependencies, public APIs, SQLite schema, four-call ceiling, final NeMo and exact-revision approval controls remain unchanged. No commits, pushes, deployments or reviewer contact occurred.

Actual selection, interpretation, relevance and completeness remain unverified. Geographic scope, source-extraction defects and ambiguous formats retain explicit limits; no country alias is invented. The previous four-case budget stopped at r03 and cannot be reused after changing the generator. A new [bounded development diagnostic](diagnostic-proposal-v146.md) is proposed separately; no twenty-case run is included.

No repeated human scoring is required for engineering failures. New assessable generated outputs need source-grounded owner adjudication before owner acceptance, and export needs approval of the exact revision. Independent usefulness still requires an owner-arranged reviewer session. Portfolio completion and production qualification remain open.

The owner subsequently authorized the four consumed-case diagnostic. Execution outcomes will be retained separately; the engineering results above do not establish that diagnostic passed.
