# Historical reporting focus prototype

The direct-evidence diagnostic selected both the requested historical reporting sentence and a general background span. This offline prototype checks whether one already-retrieved sentence can bind the report subject, cadence, content and recipient using literal matches. It keeps the full source sentence with its modality and does not assemble facts across sentences.

Seven synthetic checks passed. The prototype declined split evidence, conflicting complete matches, different subjects or cadences, current-tense assertions and unrelated questions. The untouched cq1-a20 question did not match because the question says “automated electricity meters” and the source says “automated meters.” A counterfactual using the literal source subject resolved the exact source span at offsets 1417–1503. [Executable prototype](check-historical-reporting-focus.py) · [Recorded results](historical-reporting-focus-results.json)

This prototype does not qualify the original question. A runtime design would need to establish subject equivalence from the same retrieved record, then require one unique complete match across the relevant bound branches. Low-confidence and split matches should retain the existing mapping path. Composition would need to preserve the matched source’s scope and modality. This would be a change to the opt-in composition contract and should be evaluated with more than one source before activation.

The owner's requested consolidated sentence is preserved as an editorial judgment. It is distinct from the historical source capability used in this engineering check. [Owner wording](cq1-a20-owner-adjudication-2026-11-14.md)

This work used no model calls and changed no runtime behavior. The next offline test should examine whether same-record context can establish subject equivalence without conflating related devices. Preserve the original question and recorded failures.

## Same-record check on 14 November

The pinned EIA text moves from manually read electricity meters to automated meters, then introduces electronic smart meters in a later sentence. An assistant-reviewed binding resolved the original question to the automated-meter sentence at offsets 1417–1503 and retained “could periodically report.” It binds the exact source identity, hash, context and fact offsets. Nine synthetic checks passed, including rejection of a newer-device substitution, source changes and multiple complete matches. [Binding results](reporting-subject-binding-results.json)

The source context supports this case-specific interpretation. The prototype still relies on an externally supplied subject declaration, so it provides no automatic evidence that another source uses the same terminology. Do not promote the declaration into the qualification pipeline or score the replay as a generated answer. A reusable design needs independently reviewed subject relationships or a general evidence selection contract tested on different sources before activation.
