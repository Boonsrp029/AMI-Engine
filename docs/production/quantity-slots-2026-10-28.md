# Currency parsing and explicit quantity slots — 28 October 2026

**Offline repair verified; subsequent actual diagnostic failed at r06.** The mapper and r05 passed; the requested r06 country/count comparison was omitted despite retrieved evidence and NeMo YES. See [actual findings](diagnostic-v150-findings.md). The offline checkpoint below predates that run. This follows the [failed v1.49 diagnostic](diagnostic-v149-findings.md). Prompt `analyst-pilot-v1.50`, mapper `requested-evidence-v35`; model, context/completion limits, temperature, library versions and final NeMo policy are unchanged.

## Demonstrated defects and changes

The first r05 failure incorrectly rejected a supported currency amount: the source heading contains `USD33 Billion`, while the short answer says `33 billion USD`. Numeric extraction now recognizes the existing declared `USD`/`THB` currency codes directly beside numbers. It does not generally split letters from digits. Tests reject identifier fragments and malformed decimal suffixes, retain rejection of absent numbers, and preserve the separate final value/unit checks. This is literal numeric compatibility, not exchange-rate conversion or proof of relevance.

The same response independently assigned count/FDI passages to 35% application-value growth and omitted 3,137 projects. The original canonical request combined value and count into one broad slot. The private request planner now recognizes explicit coordinated **value and project count / number of projects**, optionally followed by **how did each/both change**. It assigns two level slots or four level/change slots. Each has a verbatim question anchor, its measure/task and an instruction to supply its own answer/evidence or an explicit unresolved state. Decoder constraints require each slot exactly once; missing fields, old two-slot responses, duplicate/unknown slots and unsupported numeric answers still fail rather than being filled or repaired.

The recognition grammar is deliberately explicit. Other subject pairs, quoted/parenthesized examples and additional/unrecognized clauses keep their existing request behavior. No BOI figures, dates, source IDs or answer text are hardcoded into generation. The original question remains the authority for subject and scope. An explicit missing/partial/conflicting state is still permitted; requiring four classifications does not prove that a model correctly recognized available evidence.

Retrieval uses the same original clauses in the same order. The facet trace now links them to the finer mapping slots, but the lexical ranking algorithm, source records and selected IDs are unchanged. A frozen r05 replay verifies identical query text, ranked previews and top-three sources. Composer units retain their existing exact-evidence deduplication and independent origin validation; four fact classifications can yield two cited claims when level and growth share the same passage.

Shared each-change anchors could otherwise produce indistinguishable warnings. Gaps now name the requested measure while preserving the original clause. That identity is retained through internal composition units, including partial states. No new public `Draft` fields or SQLite columns were added.

## Validation and limits

- Targeted contracts: 92 passed. Full suite: **783 Windows tests / 782 Linux tests plus one Windows-only skip / 15 existing warnings**. The earlier 745/744 baseline is retained.
- Frozen r05 replay: the value component now passes the necessary numeric check; the incorrectly assigned 35% component still fails. The unchanged historical two-slot response also fails the new four-slot canonical contract. No corrected draft or new model response is created.
- Fixed-response harness: a correctly assigned four-fact mapping passes the actual engine's mapper preparation/validation path; an FDI-span substitution fails. These are synthetic plumbing checks with zero inference and zero NeMo invocations.
- Local image `ami-pilot:qualification-8b9d2b87bec170a6`, ID `sha256:46717c8b7f3047861cf5daab42ccc7bc50b6a62f54b3a32e9aa771789e333603`, corresponds to build context `8b9d2b87bec170a6299c4b1751b98d3e49388e3bb70b6ce50152f08667c965d2`. Actual offline Linux tests check packaged source hashes. No-inference restart/recovery preserves the four approved cached exports with a read-only backup and disposable storage.

Evidence lives in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v9/`: the pre-edit contract/snapshot, test logs, replay, fixed harness, build/image/context records and recovery checks. Initial Docker cache/engine access failures and the network-disabled system-package-step failure are retained; the normal-network build reused existing dependency layers successfully. No dependency-version change was made. Local Linux/image checks do not establish remote CI, actual container inference or production operation.

Public entry points, `Draft`, approval/export lifecycle, stored zero-based pages, reader-facing page labels, legacy graph and source corpus remain unchanged. Existing judgments, frozen attempts and approved exports are protected. New private slot behavior and numeric parsing are functional repairs, not a behavior-preserving refactor. The four-call workflow ceiling and mandatory final NeMo check remain; no repair loop or automatic approval was added.

## Next gate and human review

The [reduced v1.50 diagnostic](diagnostic-proposal-v150.md) is proposed separately: one mapper call using the actual retained r05 question and input prepared by the current engine; only if it passes technical and source/completeness checks may r05/r06 run once each. No generation is authorized by the existence of that protocol. The closed v1.49 allowance cannot be reused.

No repeated human scoring is requested for technical failures or unchanged r03/r04 content. Their country-clarified editorial candidates still need exact-wording acceptance. Any new assessable final drafts require source/completeness review before being called owner-accepted, and export requires approval of the exact saved revision. Independent reviewer usage and the full portfolio/production Goal remain incomplete.
