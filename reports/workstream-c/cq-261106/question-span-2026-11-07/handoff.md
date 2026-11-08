# Question-span repair handoff — 7 November 2026

## Actual qualification status

**Latest:** the separately granted mapper-only attempt executed once and closed at
a semantic quality failure. See [actual report](actual-report.md). It parsed the
new wire, kept the wind fact and selected a valid question range, but that range
was `and`, not the missing dated price request. One actual main call, zero
composer/NeMo calls, 871 known tokens, 28.468 seconds outer wall time. No draft,
approval/export, retry or conditional workflow followed. The current snapshot has
93 executed source/helper/test files. Older results below remain historical.

The v7 grant is closed. cq-p01 passed assistant technical/source/completeness,
final NeMo and persistence checks. cq-p02 failed the question-anchor validator
after one mapper response. It produced no draft. Actual batch consumption was
three main calls and one NeMo invocation, with 2,207 known main tokens; internal
safety usage and cost remain unmeasured. CQ1 remains 0/20 attempted.

Original v7 outputs, all 128 executed snapshot inputs and the original r07 failure
are preserved. The historical replay reproduces the original error using the
original code with sockets blocked. It is not a current-model success.

## Offline repair

Private mapper `cq-mapper-v6-question-spans` now uses required question offsets
instead of a free-text partial gap. Full-question Unicode code-point positions
preserve shared scope/dates and arbitrary requested fragments. At most 32 hints
are provided; all positions remain legal. Existing source/citation/coverage and
final safety/review controls remain in place. The sequential workflow, public
APIs, model/settings and all dependency constraints are unchanged.

See [contract](../../../../docs/concurrency/c-question-span-contract.md) for state
semantics, private-wire compatibility boundaries and remaining semantic risks.

- Expanded targeted checks: **94 passed in 14.99 seconds**.
- Full integrated offline suite: **1,657 passed, 14 warnings in 498.41 seconds**;
  session 29370 terminated with exit 0. Log: `../question-span-integrated-tests.txt`.
- Follow-up question-span checks: **27 passed in 3.77 seconds**, exit 0. These
  cover the error-message readability edit made during collection; it changes no
  state/schema/selection behavior. No integrated suite was repeated for that edit.
- Offline request inspection confirms the unchanged local model, 4,096 context,
  900 completion and temperature 0 settings; zero model calls.
- Conservative CQ1 message budgets: 20/20 within allowance, 3,590–3,827 including
  framing and completion reservations. Grammar processing latency is unverified.
- Preservation report verifies 128 snapshot inputs, 15 actual-output files, all
  three dependency constraints, r07, CQ1 manifest/plans and 87 current runtime pins.

## Exact next step

1. No further generation under the closed mapper-only allowance. Do not repeat
   the full offline suite without a new change or unresolved engineering concern.
2. Review [gap-contract decision](gap-contract-decision.md). The next safe work is
   an offline deterministic branch-disclosure prototype with different facts,
   preserving supported partial answers and honest unresolved-coverage labels.
3. Explicitly propose any change to model-selected gap semantics before adopting
   it. A owns new plan/request-scope fields; C owns private projection. Do not
   patch only `and`, weaken source checks or silently change sequential parsing.
4. A later actual diagnostic needs a new frozen purpose/budget/grant. Any current
   passing two-case workflow pair, CQ1 qualification and adjudication remain
   unmet. Old cq-p01 cannot qualify a changed mapper by itself.

## Human review

The valid cq-p01 claims are assessable; owner source/wording acceptance is still
pending. The existing pending raw-composer review has the same two claim texts.
Do not ask for repeated manual scoring of cq-p02's technical failure. Semantic
acceptance is distinct from stored exact-revision approval/export. Independent
reviewer usage and production qualification remain pending.

No new generation, Ragas, hosted inference, Databricks operation, commit, push,
deployment, reviewer contact or approval/export is authorized by this handoff.
