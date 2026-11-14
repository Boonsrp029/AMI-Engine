# Opposing publication-status development gate

Run cq-status01 once. Run cq-status02 once only after technical, exact-source, completeness and safety checks pass for the first case. Each case has 180 seconds including preparation and allows at most four local main calls and one NeMo wrapper invocation. The total ceiling is eight main calls and two NeMo wrapper invocations, with zero retries and warmups. Stop at the first failure.

| Case | Required output |
|---|---|
| cq-status01 | The raw composer and final draft state the 2019 Peru passenger rail amount and provisional status with their respective citations. Both components remain supported. No conflict, substitution, fallback or editorial repair supplies either required fact. |
| cq-status02 | The final draft identifies a conflict for the 2021 Cambodia ferry counts, names both exact source IDs and retains their opposed statements. It makes no status claim and incurs no composer or NeMo call. Record whether the raw mapper selected both statements or the application found the missing opposition among bound sources. Any application decision must retain the raw mapper response, exact added span and separate explanation. |

Compare exact retrieved and cited sources, raw selections, composition when present, final draft, runtime lineage and stored revision. Record raw model completeness independently from the application conflict disclosure. Bind the assistant assessments to the exact results using lists of source findings. Keep owner adjudication pending until an explicit decision. The source-gate verdicts of the preceding batch remain preserved.

Both fixtures are consumed development evidence. A successful pair may unlock compilation of the revised CQ1 contract. Qualification requires its own authorization.
