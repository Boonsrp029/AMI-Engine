# Decision on verified table-row composition

The 13 November table case failed when the composer omitted the share after selecting the correct row. The [offline prototype](offline-table-projection-prototype.json) takes the actual retained mapper selection, resolves its exact span, renders both fields, and passes the existing scoped projection checks. It produced a safety-pending claim with 1,802 billion kWh and 43.1% of total utility-scale generation in 2023. The claim keeps the same source, unit and retrieval branch. The previous run remains failed.

| Option | Behavior | Model budget and evidence |
|---|---|---|
| Application renders the verified row (recommended) | A supported, single-span table focus produces a source-bound claim from the parsed row. Remaining units still use the composer. | One fewer main call when the brief contains only the verified table row. The raw composer field is absent for that unit. The application-rendered text has separate provenance. |
| Composer selects a verified row ID | The composer emits the exact row unit ID, and the application resolves it to the same fixed text. | Retains the second call for a table-only brief. It demonstrates model selection of the row ID. Completeness of the rendered claim comes from application code. |

The proposed contract applies to the scoped concurrent workflow. The mapper must select the exact verified span in its bound retrieval branch, with supported status. If the layout, requested scope, row or year is ambiguous, use the existing composition path. A partial or conflicting status cannot authorize automatic rendering. The composer receives only the remaining units, and its schema excludes application-owned unit IDs. Merge claims in original unit order. Revalidate the combined draft with the existing relationship, numeric, source and final safety checks before persistence.

Record raw mapper selection, raw composer output when present, application-rendered claims, and fallback separately. The development source gate still checks the complete cited brief and requires raw composer completeness for model-owned units. Application-owned claims receive their own source-completeness judgment. This changes what the current diagnostic requires from raw composition, while keeping the CQ1 category thresholds and owner adjudication.

Before activation, cover table-only and mixed output, duplicate or forged unit IDs, changed source bytes, unsupported scope, and the final safety and exact-revision review paths. Treat the prototype as projection evidence. Safety, persistence and the revised contract's actual model behavior still need validation.
