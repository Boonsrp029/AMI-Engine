# Concurrent-workflow qualification — Workstream G

Prepared 5 November 2026. Status: preparation only; full qualification incomplete.

Start with [protocol](concurrent-qualification-protocol.md), [evidence matrix](concurrent-evidence-register.md), [reviewer protocol](concurrent-reviewer-protocol.md) and [operational decisions](concurrent-operational-decisions.md).

G owns this directory. A owns shared runtime/API integration, B retrieval, C composition, D integration tests, E UI and F packaging/CI. G records their evidence without modifying those implementations. No new public API, database or dependency change is proposed.

Use the JSON files in templates/ as field guides, never as completed observations. Copy into a new private session directory outside version control, change template_only to false only for an actual record, and leave unknown values null. Do not overwrite owner human_review.csv, approved exports or historical reports. Store detailed excerpts, participant notes and credentials outside repository documentation; summaries use aliases and source locators.

No invitation, consent, live generation, review decision, alert or deployment is implied by this package. Generation remains held. Check shared usage before major passes; pause at 90% used under the standing owner instruction.

Reviewer status update (5 November 2026): owner confirms no sessions arranged. [Synthetic progress cards](progress-task-cards.md) can support separately labelled usability sessions; keep the [facilitator rubric](progress-facilitator-rubric.md) separate from participant material. No generation grant is needed for reading these static cards; actual participation/consent must still be arranged by the owner.
