# AMI release and qualification contract — 2026-10-27

## Owner-confirmed scope

The owner selected **“Local portfolio release first, then existing Databricks staging”** and accepted these proposed operating targets in chat. External deployment, paid infrastructure, commits/pushes and reviewer contact remain separately authorized actions.

| Item | Agreed target and qualification boundary |
|---|---|
| Users/data | 1–3 human reviewers; public documents and clearly labelled synthetic fixtures; no customer/identity/payment data |
| Initial delivery | Local RTX 4060 workflow, then the existing Databricks staging environment |
| Concurrency | One active workflow; at most two queued requests |
| Latency | Warm execution p95 at most 120 seconds; cold start and queue wait reported separately |
| Deadline | 180-second total execution target, including policy checks; owned-process implementation and offline fault tests exist; backend cancellation and target-deployment qualification remain pending |
| Backup | Daily backup; proposed derived recovery-point target at most 24 hours of history |
| Restore | Restore usable task/revision/review/export history within 30 minutes |
| Review/export | Actual human identity/decision for the exact revision; edits invalidate approval; empty claims cannot be approved/exported |
| Source freshness | A pinned snapshot is historical evidence, not a real-time feed. Preserve publication, observation and requested dates separately |
| Operations | Supervised pilot initially; service hours, incident ownership and external rollout acceptance require confirmation before production qualification |
| Spend | No authorized paid infrastructure/hosted inference. Local hardware/energy cost remains unknown, not zero |

These are acceptance targets, not achieved measurements. Queue expiry, load/soak duration, production identity/access design and a reachable staging model route must be specified before live qualification. Do not describe a metadata health response as proof of policy correctness or inference quality.

## Owner-confirmed quality contract

The owner accepted the frozen 20-case gates and bounded budgets: 9/10 complete supported answers, 2/2 correct partial answers, 4/4 appropriate abstentions, 2/2 explicit conflicts, 2/2 safe injection outcomes, and zero critical unsupported or wrong-scope/date/unit/scenario claims. Two separate synthetic development preflights must pass before held-out generation. See [evaluation protocol](evaluation-protocol.md) for source identities, invocation/deadline limits and stop conditions. Owner adjudication is required for semantic support and usefulness; passing schema/citation checks is insufficient.

Unedited generation must be scored separately from corrected/approved drafts. Four historical approved exports are preserved as owner evidence, not four fresh generator successes. External reviewer evidence requires real sessions arranged by the owner.

## Budget and change control

At most four main workflow model calls are retained. NeMo internal work is separate and must be measured/bounded where possible; unknown counts are reported explicitly. The first diagnostic batch only investigates process lifecycle using frozen text, not new analyst answers. Further live diagnostics need a frozen purpose, attempt budget and output directory; do not automatically retry technical failures.

Keep library versions unchanged. The activated objective additionally authorizes evaluating/removing proven unused or duplicate dependencies **after deployability is verified**, provided deployment is unaffected. That conditional gate has not passed: inventory candidates now, remove none. Framework migrations, API changes, production-hosting changes and dependency-version changes remain separately proposed decisions.

Check five-hour usage before major passes/long validation. At 90% used / 10% remaining, save a precise handoff and pause under the standing instruction. Never consume usage simply to reach that threshold. Neither milestone nor a green test suite completes the full production goal.
