# Progress-comprehension task cards — synthetic only

These cards are invented task-state examples, not screenshots, application runs, market facts or evidence that the current UI supports these views. No LLM call is needed. The facilitator assigns an alias, records actual consent, chooses the visible/hidden order and withholds the facilitator rubric until answers are recorded. Unknown answers are acceptable.

## Matched card A — fictional document set Alder

One research request has three branches. S1 retrieves required source A. S2 retrieves required source B. S3 optionally inspects extra context and depends on S1. All work is read-only.

Visible-progress condition, checkpoint1: S1 completed; S2 running; S3 waiting_on_dependency (completion event not yet processed). No draft exists and no review decision exists.

Visible-progress condition, checkpoint2: S1 completed; S2 completed; S3 failed. Required evidence gathering is complete; aggregation is permitted with an explicit optional-branch gap. Composition/safety have not finished. No saved reviewable draft exists.

Hidden-progress condition: show only “Research task in progress; no draft available.” Do not provide branch statuses or let the facilitator hint which branch failed.

Ask at each checkpoint: What do you know is running or waiting? What information is unavailable? Can the system prepare a partial draft? Is there already a checked/approved brief? What would you do next, and what additional information would help? Record the participant's answer and uncertainty before explanation.

## Matched card B — fictional document set Birch

A different research request has three branches. S1 retrieves required source X. S2 retrieves required source Y. S3 optionally inspects extra context after S1.

Visible checkpoint1: S1 completed; S2 running; S3 waiting_on_dependency (coordinator has not processed the completed dependency yet). No draft or human decision exists.

Visible checkpoint2: S1 completed; S2 completed; S3 failed. Aggregation may proceed with an optional gap; composition/safety and saved draft remain pending. No approval exists.

Hidden condition and questions are identical to A. Assign A-visible/B-hidden for one reviewer and reverse where feasible. Equivalent structure helps compare comprehension; repeated exposure, learning and this small sample prevent a causal speedup claim. Do not give both versions of the same card to a reviewer as independent tasks.

## Boundary card C — required failure

S1 failed while retrieving required evidence. S2 was cancelled and S3 is blocked by S1. Parent drafting is blocked and no draft or approval exists. Ask whether a brief may be presented as complete and whether retry would resume old attempts or create a fresh attempt. This is a separate failure-comprehension probe, not part of the matched visibility timing comparison.

## Boundary card D — cancelled request

The user cancelled the parent request. A worker later returns a result, but it is rejected by the cancellation fence. Previously retained events remain visible. Ask whether that late result should become an approvable draft. This is an explanation of intended contract behavior, not a measured backend cancellation result.

Record mode progress_synthetic, card/checkpoint, condition/order, exact answers, comprehension time if actually timed, uncertainty, state-identification errors, usefulness feedback and deviations. Do not invent progress percentages or classify uncertainty under a hidden condition as an error. This exercise cannot establish live model quality, inference latency, external-service cancellation or full end-to-end reviewer usage.
