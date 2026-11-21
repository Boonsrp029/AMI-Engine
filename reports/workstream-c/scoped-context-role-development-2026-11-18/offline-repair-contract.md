# Direct/context schema alignment

The retained cq1-a40 mapper chose the correct capacity-definition span and also put that identifier in its context list. The generated generic same-record schema accepted it. The existing resolver rejected the duplicate role before composition. The original failure and all 201 frozen inputs are archived.

This private schema change creates one branch per allowed direct span. Each branch fixes span_id to that identifier and restricts context to other spans in the same source record. The existing focused case already excludes its fixed direct span. Required fields, wire keys, source bindings, context limit of two, group bounds and resolver rejection remain active. No invalid response is deduplicated or repaired.

Prompt instructions will explicitly require distinct contextual identifiers and empty context when unnecessary. This increments the private mapping version. Repeated context IDs and duplicate direct selections across groups remain subject to the existing semantic checks. Do not claim the JSON schema expresses every cross-selection invariant.

Ownership is limited to C's _fact_selection.py and focused tests. There is no public API, dependency, framework or orchestration change. Sequential entry points, model/settings, safety and exact-revision approval/export contracts remain intact.

Validate unrelated synthetic sources with multiple spans, no contextual spans, multiple source records, unfocused and focused decisions, wrong-record context, self-context and valid context order. Exercise fixed-response mapping/composition, retained-invalid-response rejection and request/schema sizes. Full offline validation follows targeted checks. Actual decoder feasibility and model quality need a fresh bounded generation grant.
