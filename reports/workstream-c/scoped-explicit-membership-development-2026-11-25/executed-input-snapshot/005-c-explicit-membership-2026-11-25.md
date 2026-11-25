# Verified phrases for explicit membership questions

The owner selected “Extend the existing verified-phrase renderer (Recommended)” after the actual v19 development failure. This authorizes offline implementation. The failed response and its source snapshot remain preserved separately. There is no new inference allowance.

## Behavior and change

v19 used one free-text claim for the entire “does category C include A and B?” request. The mapper selected a source list containing both names, but the composer omitted the second. The new lexical guard detected the omission before safety; it did not make generation complete.

The recognized, unambiguous affirmative source list now enters the existing category-membership route. The private composer response requires target_1 and target_2. Each must match its complete source phrase in order. The application renders one cited sentence through the existing membership renderer. Raw target fields and application rendering retain separate diagnostic records.

Only a single support branch and one exact matching source span can establish this focus. Different categories, missing members, duplicates, unbound/context-only sources and conflicting branches do not establish it. Oversized phrases retain the general prose path instead of creating an impossible constrained field. Source phrase case and qualifiers are retained. Phrase identity establishes a structural relation to the selected source; semantic applicability still requires safety and source review.

When canonical evidence merging combines requests for different member pairs, a single two-field rendering cannot express all requested names. Those requests retain general model prose with a combined coverage checklist from every origin. A regression rejects omission of a member requested only by the second component and accepts a complete cited response without fallback. The existing canonical aggregation contract is preserved.

## Ownership, passes and checks

C owns _membership_coverage.py, _request_focus.py, _scoped_generation.py, the private mapping version and synthetic tests. A's execution controls and B's retrieval remain unchanged. There is no dependency upgrade, public API migration or architecture move.

1. Preserve every pinned v19 execution input in a separate hash-verified snapshot before editing. Snapshot historical attempts, owner records and the existing source.
2. Reuse the existing source-phrase recognizer for focus selection. Route recognized membership units to the existing two-field schema and renderer, preserving the general free-prose coverage guard for other cases.
3. Validate missing fields, duplicates, changed qualifiers, wrong units, raw-response retention, source isolation and the missing-evidence path through the normal entry point. Retain the existing renderer, guardrail, approval/export and sequential tests.
4. Run the integrated offline suite. Prepare a separate version-bound development packet and preserve the predeclared twenty-case pool. Real outputs need a new applicable grant.

Composition advances to cq-composer-v20-explicit-membership-fields; whole-span mapping advances to cq-fact-span-selection-v1-explicit-membership. The four-main-call ceiling, model/context/completion settings and dependency constraints remain fixed.

The new evidence directory is reports/workstream-c/scoped-explicit-membership-development-2026-11-25. Actual model quality, owner acceptance and qualification remain pending. New technically assessable outputs require owner review. Failed technical attempts do not require repeated human scoring.
