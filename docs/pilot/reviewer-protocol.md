# Guided reviewer protocol (invitations not sent)

Invite one to three research, product or operations peers using your own account.
Suggested message:

> Would you try a supervised local prototype that helps prepare and review a
> short market-research brief? The session takes about 20–30 minutes. It uses
> public sources and does not need customer data. I would like candid feedback
> on missing facts, source support, usability and total task time, including
> checking and corrections. May I record anonymized notes under a reviewer alias?

Participation and observations must be real and consensual. Do not claim that
these invitations have been sent or that a session has occurred until it has.

## Two tasks per reviewer

Use tasks of comparable complexity drawn from the frozen cases. For reviewer 1,
do the first task manually with the supplied PDFs, then the second with AMI.
Reverse the order for reviewer 2 where possible. Supply the same source access.
Avoid having a reviewer memorize the answer before testing it with assistance.
This is a small usability comparison, not a controlled causal experiment.

Start the clock at the question and stop after the checked final brief. Include
reading, source verification and editing. Record raw seconds, assisted/manual
mode, corpus revision, run/revision IDs, missing facts, unsupported claims,
corrections, usefulness (1–5), and whether the output was approved. The UI stores
these measurements with the review; leave unknown fields blank rather than zero.

For the five-case technical comparison, open `human_review.csv` in the generated
comparison directory. Check correctness, completeness, and source support against
the references and original pages. Fill reviewer alias and review status only
after reading the evidence. Distinguish human findings from automated checks.

## Follow-up and release gate

Summarize actual participant and task counts. Choose one observed problem,
document the feedback, make a narrow improvement, and rerun the affected checks.
If no feedback arrives, report external review and feedback-driven iteration as
pending. Never manufacture time savings, ROI, production scale or testimonials.

The pilot may be demonstrated before feedback arrives, with that limitation
visible. Describe it as a supervised local portfolio pilot, not fintech
employment or enterprise production operation.
