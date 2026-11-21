# Capacity selection source review

Run cq1-a40 once. Require the original EIA footnote threshold span and empty mapper context. Require the raw composer to return the bound capacity unit and component identifiers. Verify the application rendered a single claim with the minimum total electricity generating capacity in both units, one megawatt and 1,000 kilowatts. Check the source URL, hash and offsets against the frozen record. Require explicit application-rendered provenance, no fallback for the selected claim, a passed final NeMo check and the persisted current draft. Keep editorial review distinct from generated evidence.

Run cq1-a39 once only after cq1-a40 passes every gate. Check the raw table selection, its exact EIA row and the rendered 2023 solar thermal figures of 3 billion kWh and 0.1% share of total utility-scale generation. Verify the final NeMo check and the stored draft.

Each case has 180 seconds including preparation and at most four local main calls and one NeMo invocation. Stop on first failure or the standing usage threshold. Zero retries or warmups. These are consumed development cases. Qualification retains the predeclared pool and requires its own grant.

For cq1-a40 verify that the safety artifact identifies the exact leading span, hash and offsets and that the context digest matches the supported standalone evidence placement case. Check the unchanged report and final NeMo acceptance. For cq1-a39 verify that the safety artifact records no leading excerpt and retains the standard full-evidence context. Record the safety and stored draft gates independently of raw selection and application rendering.
