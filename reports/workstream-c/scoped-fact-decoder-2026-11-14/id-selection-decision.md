# ID-only fact selection proposal

In the failed mapper-only diagnostic, the mapper put prose into context ID fields and gave character offsets that ended before either requested fact. The [offline prototype](check-id-selection.py) uses the application's existing span IDs and source offsets for the full selected passage. A response groups direct IDs and context IDs by source record and keeps the existing supported, missing and conflicting decisions.

Nine checks passed. The schema rejected the captured free-text context and a synthetic cross-record context choice. The checks retained valid same-record context, explicit missing and separate conflict alternatives. Application validation still rejected a direct span reused as context. [Check results](id-selection-results.json)

The prototype uses complete source spans. It drops the narrower, model-selected phrase offsets from the proposed response. This is a private contract change. For a historical-capability sentence, the retained passage can carry the subject, the capability, its cadence and the recipient together. For long spans containing several independent facts or an unrelated statement, ID selection alone cannot prove relevance or completeness. The generic metering passage in the saved failure would still be a structurally valid ID. Any revised workflow must keep exact-source assessment and verify that direct evidence, context, and other retrieved material remain distinct.

Before runtime integration, measure schema size with all 20 frozen cases and preserve the current geographical and branch-coverage requirements. Keep the previous result and allowance closed. This prototype made no runtime changes and used no model calls.

## Frozen-roster estimate

The [offline roster check](check-id-roster.py) constructed each proposal from the original requests and bound evidence. It preserved the current geography schema. A separate two-branch fixture exercised the existing coverage check: direct evidence from one branch did not satisfy a second required branch. The largest estimated message reservation was 3,462 of 4,096 tokens, and the largest separately measured format schema was 1,913 tokens. [Per-case results](id-roster-results.json)

The estimate uses a provisional instruction and schema. It does not validate the final runtime wiring, actual decoder or full composition budget. Before activation, choose whether the model should select complete source spans or application-generated phrase excerpts. The first removes offset arithmetic and retains qualifiers, but may carry adjacent facts. The second could provide more precise retention checks but requires a general method to generate useful excerpts without supplying reference answers.

## Composition boundary

The [socket-blocked projection check](check-whole-span-projection.py) emulated an ID-only selection by selecting the entire source span through the existing offset fields. The ordinary projection produced both fixed claims. The current literal-retention gate then rejected both, including the supported paraphrase that retained “could,” the reported information, cadence and recipient. Treating a full passage as the selected answer literal would force verbatim repetition. Removing the gate altogether would let the present-tense control through. [Replay results](whole-span-projection-results.json)

**Recommended offline integration:** use complete source span IDs and keep existing exact-source citations, numeric and scope validation. Give the ID-only branch its own retention check. Preserve claim-to-fact lineage and fail if the projected claim drops an explicit capability qualifier such as “could.” Require exact-source review of direct relevance and requested details because a span-level binding cannot establish that every fact survived. Keep the existing offset contract available for historical replay. Test a supported paraphrase, the present-tense control, numeric substitution, missing details and a long span carrying adjacent facts before freezing any generation.

This changes the private mapper response and the associated composition check. It does not authorize actual generation. No runtime change has been applied in this check.
