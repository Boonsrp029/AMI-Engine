# Facilitator rubric — keep separate from participant cards

Preparation only. No reviewer has completed these probes. Obtain actual consent, record assignment/familiarity and ask neutral questions before explanations. Use [participant cards](progress-task-cards.md) and the existing session template in mode progress_synthetic. Do not copy these expected answers into an observation record as if a participant supplied them.

| Probe | Expected contract interpretation | Recording rule |
|---|---|---|
| A/B checkpoint1 | S2 running; S3 waiting for the coordinator to process dependency completion. No reviewable draft yet | Note comprehension, uncertainty and whether the temporary waiting state confuses the reviewer |
| A/B checkpoint2 | Optional S3 failure permits aggregation with a declared gap after required branches complete. Composition/safety/save still pending | Do not equate retrieval completion with a complete or approved brief |
| A/B hidden view | Branch-specific facts cannot be inferred from the display | Record unavailable information and confidence; do not score honest uncertainty as incorrect |
| C required failure | Required failure prevents drafting; failed dependency blocks descendants. Explicit retry creates fresh attempt identities | Record misunderstanding rather than supplying a desired answer |
| D parent cancellation | Late worker output cannot publish a new candidate. Actual server-side cancellation is not established | Distinguish UI/process expectations from backend measurements |

Progress observations should contain card_id, checkpoint, display_condition, order, prompt, answer_verbatim, expected_information_available, assessment (correct/incorrect/uncertain/not_assessable), assessor_reason, comprehension_seconds if measured and deviations. Store these as objects in session-record.json's progress_questions list. For unmatched or not-assessable responses leave error totals unknown; report denominators only for assessed questions. Perceived helpfulness and correctness are different outcomes.

Keep the comparison exploratory: show participant counts, question counts, raw responses/times, missing data, task order and learning effects. Do not turn synthetic-card time into production latency or business savings. Real independent users can provide interface feedback here, but synthetic-card review alone does not satisfy the live analyst-task qualification gate.
