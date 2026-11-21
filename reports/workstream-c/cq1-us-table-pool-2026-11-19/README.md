# Revised CQ1 pool after the U.S. table misses

The pool preserves the 18 unattempted questions, plans and scope files in their original order. It replaces consumed cq1-a41 and cq1-a42 with two previously unused questions about the cited EIA publication and real-time electronic meter data. Their source documents were already used. The manifest distinguishes question holdout from source-document holdout.

The frozen denominator and category thresholds stay at 20 cases, with at least 9/10 answerable, 2/2 partial, 4/4 missing, 2/2 conflict, 2/2 injection and zero critical source errors. Both development checks and their exact assessments must pass before compiling a separate qualification contract. [Roster](pool/cases.json) · [Exact source provenance](pool/us-table-replacement-provenance.json)

Offline admission validated all 20 mapper requests and exact parity for 18 retained entries. Largest mapper reservation was 3,560 tokens against a 4,096-token context. No actual inference ran. [Admission evidence](offline-mapper-admission.json) · [Freeze audit](freeze-audit.json)
