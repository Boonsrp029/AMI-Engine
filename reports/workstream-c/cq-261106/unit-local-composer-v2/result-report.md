# Actual single composer diagnostic — raw pass, application title issue

Executed once on 7 November 2026 under the explicit single-request user grant. Protocol SHA-256 `8da1a51cd9239cd54ec5617dff9d7859ddd39b419cd0d743823eb59d24811b37` was verified. The request reused the retained synthetic mapper evidence; no fresh mapper/model retrieval or workflow was generated.

## Observed execution

One actual local composer request, zero NeMo invocations, no retries or warmups. Normal `stop`, model identity checked before and after. Reported usage **686 input + 115 output = 801 tokens**. Overall elapsed **33.812 seconds** within the 95-second limit; service phase 14.640 seconds, socket-blocked offline validation 18.984 seconds. These are one-attempt timings including startup, not a sustained latency result or matched quality/cost improvement. Hardware/monetary cost remains unmeasured.

Technical validation passed. The raw output reports both supplied facts in their correct units, with no fallback/editorial correction or unsupported relative comparison:

1. “In Canada, observed electricity demand grew 5.7% in 2016.”
2. “In Japan, electricity demand is projected to grow 2.6% annually through 2036.”

The exact whitespace-preserved model text is in `review-packet.md` and `actual/service/service-result.json`. These are synthetic development facts, not verified official energy statistics. Assistant source support/completeness passes for the raw claims; owner wording/source acceptance remains pending.

## Application-generated scope failure

The raw generic title is `Analyst research brief`. Application projection changes it to **`Analyst research brief (Canada)`**, despite the explicitly two-country question and Japan claim. The retained mapper's global geography is Canada with evidence only from `cq-observed`. That single-source resolution is insufficient to label this complete two-country brief.

Accordingly, `result-assessment.json` records **raw supported/complete:true**, **application claims supported/complete:true**, **application title scope:false**, and **overall final-output gate:false**. The application-scope issue must not be hidden behind technical parsing success or the raw improvement. No new workflow is authorized, no NeMo was run, no Store revision was created, and no approval/export is possible from this diagnostic.

## Preservation and next engineering action

The executed 119 project files, 6 request artifacts and protocol are copied into `executed-source-snapshot/`; 13 original output files are hashed. Original model/service/validation artifacts and their pending statuses remain unchanged. The source assessment is separate and assistant-authored. Generated validation child IDs belong to offline replay provenance, not a newly served analyst workflow.

The once-only grant is closed after its single request. Stop further inference. Repair concurrent application title scope offline: a common global geography label must apply to all selected units/sources, including legitimately pinned same-document context; otherwise retain a neutral title. Preserve explicit per-claim geography, strict numeric/relationship checks, raw mapping and diagnostics. Do not alter the original generated output or silently count a corrected title as a fresh success.

The previously tested lineage candidate remains separate/unapplied. Its integration window can now be considered because this frozen actual attempt is closed, but future execution identities must be re-frozen after any source changes. CQ1 remains 0/20 attempted; the passing two-case workflow gate, actual safety/publication, required adjudication and production qualification are not established.

Human review is useful for source support and wording of these two raw claims before owner acceptance. The known title bug is an engineering correction and needs no repeated numerical scoring. Review does not approve/export a stored revision or authorize more model calls.
