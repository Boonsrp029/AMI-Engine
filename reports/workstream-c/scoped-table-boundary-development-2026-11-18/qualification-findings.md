# CQ1 stopped at the Other sources composition

The 18 November qualification ran two of twenty ordered cases once. cq1-a37 passed technical, assistant source, completeness, safety and storage checks. cq1-a38 failed composition validation. Eighteen cases remain unattempted. The allowance is closed. [Exact accounting](qualification-batch-summary.json)

The batch used four local main-model calls and one NeMo wrapper invocation. Captures report 6,839 main-model tokens. Internal NeMo usage and monetary cost are unmeasured. Owned wall times were 62.81 seconds and 29.55 seconds. No retries or warmups ran.

cq1-a37 correctly answered Other gases at 11 billion kWh and 0.3% of total U.S. utility-scale generation in 2023. Marker 3 in the source is a footnote. Raw composition selected the verified table unit and the application rendered the supported values. Generated prose leaves U.S. implicit. Its exact-result owner review is pending. [Source assessment](actual-cq1/cq1-a37.assessment.json)

cq1-a38 selected the right-hand table fragment without the year or headings. The raw composer then answered a different row, saying pumped storage generation was 4 and its share 0.4% in 2023. In the source, 4 is a footnote marker for pumped storage, whose actual values are -6 billion kWh and -0.1%. The 0.4% occurs in the preceding geothermal row. The requested Other sources row is 10 billion kWh and 0.2%, preceded by footnote marker 5.

Both raw responses parsed. Fixed-response replay with sockets blocked reproduced the exact rejection, “Draft introduces a numeric value absent from its selected evidence.” The selected fragment has no 2023 year. No final draft, fallback, approved revision, export or NeMo call was produced for cq1-a38. [Offline replay](cq1-a38-offline-replay.json)

Source inspection identifies an implementation gap before composition. The table recognizer accepts only unsigned amounts and shares. It stops at the preceding negative pumped-storage row and never offers a verified Other sources focus. The exact source window from the year/headings through the requested row is 591 characters and fits the existing 600-character limit. A larger context window is unnecessary for this failure.

Next offline engineering should support signed table amounts and shares independently of unsigned conversion parsing. Preserve footnote handling, exact source offsets, ambiguous-row rejection and strict composition validation. Use different facts for regressions, including a requested row after a negative row and a requested negative net-generation row. Preserve this failed outcome and freeze new development evidence before any new applicable generation grant.

The owner has accepted source support and the U.S.-explicit editorial copies for the two earlier development results. That acceptance is recorded in owner-acceptance-development.json and applies to those copies. It does not approve/export stored revisions or regrade this failed qualification. Human review can assess the new cq1-a37 draft; cq1-a38 has no final draft to review.
