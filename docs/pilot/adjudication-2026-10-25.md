# Owner wording addendum — 2026-10-25

This addendum records the owner's new revisions and explicit choices in the conversation. The [structured record](evidence/adjudication-2026-10-25.json) preserves the original wording verbatim, the approved revision, source locators and hashes. It supplements earlier judgments without rewriting them or assigning new numerical scores. Future model outputs still require their own assessment.

## d03: approved development example

> Private investment in Thailand in August 2026 was higher than July, particularly in machinery and equipment, supported by the global technology cycle and investment in data centers. Private consumption increased slightly from the previous month, driven by spending on services, particularly hotels and restaurants, consistent with increased foreign tourist arrivals. Spending on semi-durable and durable goods also increased.

The owner selected **Correct the explanation** after the source distinction was presented. This example is reviewed development guidance, not a hardcoded application answer or a replacement for a frozen output.

The pinned BOT snapshot supports the monthly comparison and investment explanation on PDF page 1 (index 0, chunks `BOT_AUG_2026:0:3` and `:0:4`), and investment/consumption detail on PDF page 2 (index 1, chunks `BOT_AUG_2026:1:0` and `:1:1`). “Previous month” in this August release is July; detailed indicators are seasonally adjusted. The original chunk ending with “investment in data” needs its continuation to establish “data centers.” This pass does not change retrieval to supply adjacent chunks automatically.

The owner's original consumption sentence referred to domestic expenditure including foreign tourists. Chunk `BOT_AUG_2026:1:4` describes PCI measurement coverage and distinguishes category from aggregate treatment of tourist spending. It does not establish the main driver of consumption. The explanatory passage in `:1:0` supplies the supported activities used above. These findings concern the pinned local source, not independent verification of economic outcomes.

## d06: approved retrieved-evidence scope

The owner selected **Retrieved evidence** rather than database-wide absence. The new no-information message is:

> I'm sorry, but the documents retrieved from our current document database do not provide enough evidence to answer this question. Please rephrase your question or try another topic.

The gap template retains the complete original question:

> The retrieved documents do not establish an answer to: [original question]

For d06, this retains Thailand, exact retail electricity prices and yesterday. Selected passages cannot establish absence from every document in the database. Conflicting evidence receives a distinct conflict warning; supported partial answers remain available.

## Manual review

No further wording decision is required before implementation. After technical checks pass, the owner reviews new assessable outputs for source support, completeness and usefulness, especially d03's causal explanation. Approval of a saved brief remains tied to its exact revision. Independent reviewer usage is still pending; this addendum establishes no external-use evidence.
