# Actual v5 diagnostic — coverage gate correctly stopped incomplete mapping

**Quality gate failed; allowance closed.** cq-p01 was attempted once; cq-p02 and all20CQ1cases remain unattempted. No retry, tuning or case substitution occurred within the batch.

The mapper returned valid constrained-state JSON but selected only Canada's observation. Offline replay of the exact saved response against the unchanged source catalog and coverage policy raises: Supported request leaves required branch coverage unselected: s02. Japan's available projection was again omitted. This was a request-completeness failure, not schema extraction/truncation or GPU capacity evidence. The application rejected it before composition, NeMo or draft persistence. The guard worked; the model did not satisfy the coverage instruction.

Observed: one main request,602input+127outputtokens, normal stop,23.078seconds end-to-end. No NeMo invocation or saved draft. Worker failure telemetry records ValueError/composition phase (the callback phase contains mapping), not an inference-backend crash. Monetary/hardware cost remains unmeasured. The prior v4 publication failure remains independently unverified because this run never reached that boundary.

## Next offline contract design

Move necessary branch coverage into supported-state decoding where tractable, preserving the application guard. For disjoint support-span sets, supported evidence may use a tuple prefix with one selectable span from each declared required branch; all eligible spans remain choices and no fact/value is preselected. Partial/missing alternatives must remain available so irrelevant evidence is never forced into a claim. Shared/overlapping-source cases need explicit handling and cannot simply require duplicate citations; retain strict application coverage and shared-origin semantics.

This is an explicit private decoder-contract change, not proof of semantic support. Use different synthetic facts and test schema literals/selection, partial/missing, irrelevant/distractor evidence and shared provenance. Recount message and grammar resources after any repair. No model change, request substitution, answer injection, evidence-validation relaxation or further inference is authorized.

Raw response/result/SQLite history/stopped marker and exact source snapshot are preserved. No manual semantic scoring is requested for this hard technical/coverage rejection. Overall quality Goal remains unachieved.
