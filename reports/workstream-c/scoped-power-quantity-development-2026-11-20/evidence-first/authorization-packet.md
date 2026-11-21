# Power conversion fact-check diagnostic

The integrated development run correctly said one gigawatt equals one billion watts, yet NeMo blocked it. The archived verdict is unavailable. The diagnostic reconstructs the exact original full evidence from its recorded digest, puts the complete cited EIA conversion ahead of that evidence, and captures the raw judge verdict. Both prompts retain all prior evidence. The report text and existing NeMo policy are unmodified in the supported case. [Retained failure](../findings.md)

1. Run power-supported once. Require a single YES or YES. and acceptance of the exact supported report.
2. Only after the first passes and usage remains below the threshold, run power-wrong-scale once. It changes only “one billion watts” to “one million watts.” Require a single NO or NO. and rejection by self check facts.

Maximum two local NeMo wrapper invocations, 60 seconds per case including model verification, zero workflow calls, retries or warmups. Stop on first failure or the standing 90% threshold. Output goes to actual. Record wrapper timing and raw verdict. Internal judge usage and cost remain unmeasured. This development experiment cannot change past CQ1 results or prove integrated qualification.

The real Colang flow exercised both prompts with fixed judges. It rendered the complete context and returned the expected allow and block decisions. No local model ran in preflight. [Offline preflight](offline-preflight.json)

Contract SHA-256 16e0347972546ee51cf55387139800179bb3ee48a5241b45ffeadb9985db9b10. [Frozen contract](contract.json)

Reply **Authorize power conversion evidence-first fact-check diagnostics** to execute.
