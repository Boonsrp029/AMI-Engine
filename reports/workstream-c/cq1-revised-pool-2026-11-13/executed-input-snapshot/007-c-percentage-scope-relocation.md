# Concurrent composition percentage scope

The scoped v1 development batch closed at cq-p02. The retained [offline replay](../../reports/workstream-c/scoped-development-v1-2026-11-07/cq-p02-offline-replay.json) shows that the relationship check treated a trailing country or year as part of the percentage denominator. CQ1 remains at 0 of 20 attempts.

Workstream C owns the private relationship check and its regression tests. Permit one additional equivalence when a claim and its single selected quote each contain one percentage denominator, the same literal sentence body, and the same explicit `in <location>` and `in <year>` phrases. One phrase must appear before the body and the other after it, with the positions reversed between the claim and quote. Ambiguous or more complex sentences use the existing comparison. The claim still goes through the normal unit, numeric, measure, period and observation/forecast checks.

First reproduce the failure using a different percentage, measure, location and year. Then verify that the scoped workflow retains the supported claim and shows the specific missing branch. Exercise changed denominators, numbers, units, years, countries and observation/forecast wording, plus multiple evidence quotes. Keep the saved actual failure and the original evaluation pool intact.

A fresh actual diagnostic requires a new contract and grant. If the narrow rule passes offline checks, freeze a development-only follow-up using the existing sequential two-case gate, current source identities, and the agreed call and time ceilings.
