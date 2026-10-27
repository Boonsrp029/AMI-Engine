# Scope and coverage repair after failed qualification

The v1.36 qualification remains failed. This work is offline engineering; no new generated output, score, owner acceptance or export is implied. The full Goal remains incomplete.

## Freeze before tuning

The proposed v3 final pool was frozen before the new scope edits. It retains the sixteen unattempted v2 cases unchanged and replaces consumed r03–r06 with r23–r26. Counts remain ten answerable, two partial, four missing, two conflicts and two injection cases. The replacements ask different facts and retain multipart, causal, historical/forecast, geographic and quantity/baseline distinctions. Comparable difficulty is not established. All four replacements use IEA, changing the answerable topic mix to seven IEA and three BOT cases; this requires review before final qualification and cannot support a matched before/after improvement claim.

Specification: `data/pilot/release-2026-10-27-v3/spec.json`. Frozen manifest SHA-256: `c8ee93dd983022549bd43d7cb3dadcf2d223dc36606d7bc5dc1e296ff6782fe0`. The pinned sources and public retrieval corpus are byte-identical to v2. This shared source exposure limits independence; no pretraining novelty or statistical assurance is claimed. References are assistant-authored and await human adjudication. v1/v2 failures remain unchanged.

The new pool has **zero generated attempts and no authorized generation budget**. A stopped batch's unused ceiling cannot unlock a new generator or package.

## Pass 1: constrain scope choices

Previously, capitalized words following “in” could become geographic candidates even when the question requested another place. The mapper could also choose any date anywhere in the offered spans. A dateline that lacked the word “published” could then become an observation label.

The runtime now restricts geographic choices to labels also occurring in the question, preserving word boundaries and case-insensitive matching. It does not shorten a multiword source name to match another requested name. Unrequested industry and market labels cannot enter the known-geography decoder. The unrestricted private helper mode remains compatible for existing callers. This is a conservative restriction, not a geographic ontology: a matching question phrase still does not prove geographic meaning. A location omitted from the question may remain unresolved.

Period choices are restricted to explicitly requested month/date values or, for year-only requests, the requested years. A narrow release-number/dateline prefix is excluded from measurement dates in both choice generation and scope propagation. Other factual dates later in the same span remain available. Unknown dateline forms and date-to-measurement attribution remain unresolved problems; this is not a general publication-date classifier.

Prompt identity for this pass is `analyst-pilot-v1.37`, mapping `requested-evidence-v24`. Four-call limits, public `Draft`, library versions, final NeMo and exact-revision review/export controls are unchanged. The retained r05 raw scope candidate now fails the revised schema in offline replay. That is rejection evidence, not a freshly improved answer. Initial targeted-test expectation failures were retained; corrected targeted checks pass 73 tests.

The complete v1.37 Windows suite passed **517 tests**, retaining 15 dependency warnings. The earlier v1.36 container remains a separate artifact; no Linux or container result is attributed to the new source yet.

## Pass 2: explicit multipart request boundaries

The parser now recognizes comma-separated interrogative clauses and auxiliary-led questions such as “did”, “does” and “was”. Introductory scope before the first question remains attached to it. Compound subjects, quoted text and simple parenthetical material are preserved. When requests exceed the five-slot limit, the original whole-question fallback remains explicit rather than silently discarding a task. This is bounded grammatical segmentation, not complete natural-language intent parsing.

The retained r06 question now has three request slots. Its saved one-slot candidate is rejected before evidence resolution; no model generated a replacement mapping. The 51 targeted checks passed, including the scope-choice and approval/export instruction contracts. Current prompt/mapping identities are `analyst-pilot-v1.38` / `requested-evidence-v25`; the expanded full Windows suite passed **528 tests**, retaining the same 15 dependency warnings.

Per-slot semantic relevance, monthly/quarterly coverage, measurement denominators and wrong-report provenance remain unresolved. These parser changes do not prove that a model will populate the slots correctly. No new inference budget is requested until the remaining offline repair gate is concrete and verified.

## Remaining passes and gates

| Pass | Current failure | Intended improvement | Required validation |
|---|---|---|---|
| Requested component/report context | An unresolved-period warning still permits a wrong-report monthly answer; a quarterly paragraph can answer a monthly request | Reject established source/report incompatibility before composition, retaining explicit provenance and ambiguity limits | Synthetic wrong-month/quarter fixtures and saved r03 replay; valid dated historical comparisons must remain possible |
| Request and evidence coverage | A multipart question can remain one slot; populated slots can contain unrelated background | Track each requested measure, comparison and denominator; verify available source coverage before composing | Synthetic multipart/partial/conflict cases, retained r04/r06 analysis and complete-source-span checks; no case-ID patches |
| Actual validation | Fixed responses only establish engineering contracts | Propose a new bounded diagnostic gate only after offline repairs pass | New explicit budget, pinned model/generator, one attempt per case, source inspection before final-pool execution |

Do not relax r06's valid scope rejection, convert malformed output to abstention, hardcode reference answers, or claim that exact quotation identity establishes semantic relevance. Preserve useful supported partial answers and distinct missing/conflicting states. Failed outputs do not need repeated human scoring. Future owner-acceptance still requires source-grounded human review; export requires approval of the exact revision.
