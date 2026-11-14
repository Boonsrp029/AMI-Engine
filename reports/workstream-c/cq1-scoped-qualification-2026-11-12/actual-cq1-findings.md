# CQ1 scoped qualification stopped at cq1-a01

12 November 2026. The authorized CQ1 contract attempted one of twenty cases. The first case failed during evidence mapping. Nineteen cases remain unattempted. The ledger closed the allowance at the first failure. There are zero source-adjudicated CQ1 results.

The mapper call completed normally and used 2,319 input and 204 output tokens. The operator ended after 33.671 seconds within the 180-second bound. The stored run has status failed, revision 0 and no draft. No composer request or NeMo invocation occurred. The exact result SHA-256 is `f17be32537b7983e86bd7aa6897b19d978c210140ade6c1d2808ca412b8bc0df`. All 161 pinned inputs matched the contract and have a retained execution snapshot.

## Reproduced failure

The scoped mapper schema accepted `Watthours` as a geography value because the general source-choice heuristic admitted a capitalized term following `in` in a measurement definition. The mapper chose the unrelated measurement document for this value. Its component selections came from the generation document and included the total, a preliminary-data note and an unrelated table fragment. The selected measurement span lacked a supported source or pinned-document binding. The existing resolver raised `Geography evidence must come from a supported component's retrieved source or its pinned document`.

The [socket-blocked replay](cq1-a01-offline-replay-with-evidence.json) reproduced the binding error from the saved response and exact runtime plan. The first replay saved its result and then exited with a display error because the schema-error key was absent. The corrected replay records the span evidence and completes successfully. The source-binding validator prevented an invalid geography from reaching composition. No claim-level quality score or manual adjudication applies to the failed attempt.

## Proposed offline follow-up

Prototype request-bound geography choices for a new concurrent mapper contract using the existing requested-label filter. In a separate synthetic example, the current filter offered Chile, Passenger, Passenger Kilometres and Pesos as places. The request-bound filter offered only Chile for the Chile passenger-rail query. The filter is a necessary check. A requested word can still denote a unit, and a valid alias such as US versus United States may lack a literal match. Keep those cases unresolved unless the application can establish a supported location with explicit evidence and verified document lineage.

Test unrelated capitalized units, geography aliases, supported-source membership and multi-country title behavior using different source facts. Preserve the evidence and document-binding checks. The next development gate should cover a representative multi-document case, including irrelevant returned spans and correctly selected required facts. cq1-a01 is now consumed. Before a future qualification attempt, predeclare the treatment of the nineteen unattempted CQ1 cases and any replacement case.
