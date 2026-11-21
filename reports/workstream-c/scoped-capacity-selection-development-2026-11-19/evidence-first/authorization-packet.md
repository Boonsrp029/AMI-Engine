# Capacity evidence placement diagnostic

The retained full-evidence fact check returned NO on a supported report. This experiment prepends the exact selected EIA footnote to the same complete retrieved evidence. It keeps the pinned model, NeMo policy and strict verdict parser. The negative case changes only the report's equivalent quantity from 1,000 to 1,500 kilowatts. This isolates the proposed evidence presentation while checking whether an unsupported quantity is still rejected. [Baseline result](../actual-fact-check/result.json)

Run capacity-supported once. Advance to capacity-wrong-kilowatts once only if the former returns an exact affirmative verdict and NeMo accepts the unchanged report. The latter must return an exact negative verdict and block. Stop on the first failed or timed-out case or the standing five-hour threshold. Maximum two local NeMo wrapper invocations, 60 seconds per case, zero analyst model calls, retries or warmups. Retain both raw verdicts, prompt, timing and decisions where available. Internal provider usage and cost are unmeasured.

Offline preflight confirmed that both rendered prompts carry the full evidence and that fixed YES and NO drive the expected outcomes. Model behavior remains to be tested. Any observed success applies only to this development pair. Application integration and actual workflow qualification remain separate.

Contract SHA-256 ad1b9ca97d897e53626f25be56bd32ad187af363c5f3e6051302463dc4daeafe. [Frozen inputs](contract.json) · [Offline preflight](offline-preflight.json)

Reply **Authorize capacity evidence-first fact-check diagnostics** to execute.
