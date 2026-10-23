# Source audit for human adjudication

**Assistant-authored; awaiting human adjudication.** No human ratings or review decisions are supplied.

## Method and provenance

Five paired cases (h01-h05), ten frozen outputs, were checked against the pinned BOT/IEA PDFs and captured retrieval contexts. References were checked against source pages rather than treated as unquestionable truth. All findings distinguish source fidelity, retrieved coverage and task completeness. This is not independent verification of the PDFs’ authenticity or current real-world facts.

No application, prompt, dependency, benchmark answer, human-review record or Ragas metric was changed. No model inference, reviewer contact, commit, push or deployment was performed. Detailed excerpts and rendered pages remain in the ignored local review directory.

The initial integrity snapshot covers **157 files**. Machine-readable input hashes, exact output spans, component findings and locators are in [source-audit.json](evidence/source-audit.json). The local [review packet](../../reports/workflow_pilot/source_review/review-packet.md) includes unchanged outputs, source excerpts and blank reviewer prompts. Ragas scores are kept separate in the existing evaluation report.

### Status meanings

- **Supported:** The asserted proposition is supported within its stated scope; this does not establish full task completeness.
- **Partially Supported:** Some components or a limited local absence are supported, with material qualification or missing scope.
- **Unsupported:** A needed evidentiary basis or justification is absent; source differences do not themselves establish a conflict.
- **Contradicted:** The assertion disagrees with explicit source or captured-evidence content.
- **Unverifiable:** The available source, layout or scope does not permit a reliable conclusion.

A supported statement can still be incomplete or irrelevant. A true “not in provided evidence” statement can coexist with a retrieval failure when the full corpus contains the fact. A dated projection can correctly answer a historical source-summary question.

### Pinned sources

| Document | PDF pages | SHA-256 |
|---|---:|---|
| [BOT_AUG_2026](https://www.bot.or.th/content/dam/bot/documents/en/thai-economy/state-of-thai-economy/monthly-report/macro-2026-08-press.pdf) | 7 | `182962527071430875386c1200cfbdfa3aa4d90616dce00f240cb525e5596012` |
| [IEA_SEA_2024](https://iea.blob.core.windows.net/assets/ac357b64-0020-421c-98d7-f5c468dadb0f/SoutheastAsiaEnergyOutlook2024.pdf) | 200 | `15d45df68f8df43a499ad9ef07910f4f0ba19c6244af107bf7a50e8fa9ecf521` |

Reader-facing PDF pages are one-based; indexes are zero-based. IEA printed page numbers match the PDF page numbers on inspected pages. BOT locators use PDF pages because printed numbering is not established.

### Visual checks

Inspected rendered BOT PDF pages 1-2 and IEA PDF pages 7-9, 35, 86, 161-162 and 172. This confirmed category labels, units, dates, table scope and the cross-page nickel sentence. The visual export graphic shows -0.1% month-on-month; its association is not reliable from flattened header numbers alone.

## Findings at a glance

| Case | Existing agent | New workflow |
|---|---|---|
| h01 | Identifies categories and moderation, but omits the requested technology/AI-cycle driver. | Its three cited claims are supported and cover the two main requested facts; the product/date gap messages are false and the figures warning is not established from flattened input. |
| h02 | Source-supported concise answer, but omits weather/production-cost and crude-oil causal links. | Unsupported abstention: all required causal evidence was retrieved. |
| h03 | Investment fact is supported, while consumption activities and investment drivers are not explained. | Mixed failure: retrieval misses consumption and full investment-driver evidence; synthesis also discards available specific investment activities. |
| h04 | Valid demand growth and generation context, missing requested demand TWh level; added renewables percentages misattribute solar-only shares. | Unsupported abstention despite complete demand evidence; gap messages confuse precision, metric and scenario distinctions. |
| h05 | Ambiguous stock/additions wording and missing 16 GWh baseline; absence of nickel share is accurately scoped to its provided contexts. | All three cited claims are supported, but the required nickel share is not retrieved or answered. Several country-specific gaps are unrequested. |

**All six workflow claim-to-citation links are source-supported in this audit.** This does not validate the three abstentions, the fifteen warning messages or complete question coverage. Findings below include every original response sentence, workflow claim, warning and abstention.

## Case-by-case source checks

### h01: What supported exports excluding gold in the BOT August 2026 release, and did technology-related exports keep accelerating?

Required facts and observed coverage:

| Fact | Source | Retrieved: legacy / workflow | Answer: legacy / workflow |
|---|---|---|---|
| High exports excluding gold were supported by the global technology/AI cycle. | BOT_AUG_2026 PDF 1 (indexes 0) | complete / complete | partial / complete |
| Technology-related exports moderated after prior growth; continued acceleration is not the reported outcome. | BOT_AUG_2026 PDF 1 (indexes 0); BOT_AUG_2026 PDF 3 (indexes 2) | complete / complete | complete / complete |

Statement and gap assessments (the structured record retains exact field/span locators and text hashes; unchanged output text is in the local packet):

| ID | Assessment | Reason and source |
|---|---|---|
| `h01-legacy-s1` | **partially supported** | Electronics/electrical appliances are supported categories, but listing them does not identify the causal support asked for: the global technology/AI cycle. The wording is not wholly fabricated. Sources: BOT_AUG_2026 PDF 1 (indexes 0); BOT_AUG_2026 PDF 3 (indexes 2). |
| `h01-legacy-s2` | **supported** | The release explicitly describes moderation after prior strong growth; no continuing acceleration is asserted. Sources: BOT_AUG_2026 PDF 1 (indexes 0). |
| `h01-workflow-c1` | **supported** | High exports excluding gold and the technology/AI-cycle driver are directly supported by its cited chunk. Sources: BOT_AUG_2026 PDF 1 (indexes 0). |
| `h01-workflow-c2` | **supported** | Declining but still high electronics/electrical-appliance exports and their technology-cycle support are directly supported; this addresses the no-further-acceleration part. Sources: BOT_AUG_2026 PDF 3 (indexes 2). |
| `h01-workflow-c3` | **supported** | Agricultural/agro-manufacturing exports and sugar-to-Indonesia explanation occur in the cited chunk. This is extra context, not an answer error. Sources: BOT_AUG_2026 PDF 3 (indexes 2). |
| `h01-workflow-w1` | **contradicted** | Specific products are named in the returned evidence and even in the draft’s own claims. This gap assertion is false for the captured inputs. Sources: BOT_AUG_2026 PDF 3 (indexes 2); BOT_AUG_2026 PDF 3 (indexes 2). |
| `h01-workflow-w2` | **unverifiable** | The captured header contains numbers without reliable layout associations; the cited export prose lacks a clearly labelled exact export-change figure. The PDF graphic shows -0.1% month-on-month, but source layout cannot be silently attributed to the flattened model input. Exact figures were not requested, so this is not a valid reason to withhold the qualitative answer. Sources: BOT_AUG_2026 PDF 1 (indexes 0). |
| `h01-workflow-w3` | **contradicted** | August 2026 is explicit in the query and retrieved release heading. No more exact daily date is needed for this monthly question. Sources: BOT_AUG_2026 PDF 1 (indexes 0). |

Reference check: **supported**. The other-products increase is supported contextual information; the question does not require every extra reference fact.

Questions for the human reviewer:
- Would you keep the electronics decline as the answer to the acceleration question?
- Which gap messages would you remove or qualify?

### h02: How does the BOT explain the increase in headline inflation and core inflation in August 2026?

Required facts and observed coverage:

| Fact | Source | Retrieved: legacy / workflow | Answer: legacy / workflow |
|---|---|---|---|
| Headline inflation rose with food and energy prices. | BOT_AUG_2026 PDF 1 (indexes 0) | complete / complete | complete / missing |
| Fresh-food increases involved adverse weather/lower output and rising production costs. | BOT_AUG_2026 PDF 1 (indexes 0) | complete / complete | missing / missing |
| Domestic energy/fuel increases followed higher global crude-oil prices. | BOT_AUG_2026 PDF 1 (indexes 0) | complete / complete | missing / missing |
| Core inflation rose through gradual cost pass-through to consumer prices. | BOT_AUG_2026 PDF 1 (indexes 0) | complete / complete | complete / missing |

Statement and gap assessments (the structured record retains exact field/span locators and text hashes; unchanged output text is in the local packet):

| ID | Assessment | Reason and source |
|---|---|---|
| `h02-legacy-s1` | **supported** | Food/energy increases and core cost pass-through are supported. Weather/production-cost and crude-oil mechanisms are omitted, which affects completeness rather than making these stated facts false. Sources: BOT_AUG_2026 PDF 1 (indexes 0). |
| `h02-workflow-abstention` | **unsupported** | The retrieved contexts include the food/weather/cost, energy/crude-oil and core pass-through explanations. An empty response is not justified by missing task evidence. Sources: BOT_AUG_2026 PDF 1 (indexes 0). |
| `h02-workflow-w1` | **contradicted** | The returned material provides the causal explanation needed for the question. “Comprehensive” should not erase the explicit relevant mechanisms. Sources: BOT_AUG_2026 PDF 1 (indexes 0). |

Reference check: **supported**. The reference is supported by the causal explanations on BOT PDF page 1.

Questions for the human reviewer:
- Does the short legacy answer adequately explain the causes, or must weather, production costs and crude oil be explicit?

### h03: Which activities supported private investment and consumption in Thailand in August 2026?

Required facts and observed coverage:

| Fact | Source | Retrieved: legacy / workflow | Answer: legacy / workflow |
|---|---|---|---|
| Private investment increased particularly in machinery/equipment. | BOT_AUG_2026 PDF 1,2 (indexes 0,1) | complete / complete | complete / missing |
| The investment narrative links support to the technology cycle and data centers. | BOT_AUG_2026 PDF 1 (indexes 0) | partial / missing | missing / missing |
| Consumption increased slightly with services, especially hotels/restaurants. | BOT_AUG_2026 PDF 1,2 (indexes 0,1) | complete / missing | missing / missing |

Statement and gap assessments (the structured record retains exact field/span locators and text hashes; unchanged output text is in the local packet):

| ID | Assessment | Reason and source |
|---|---|---|
| `h03-legacy-s1` | **partially supported** | Machinery/equipment investment and stable tourism receipts are supported. Machinery is not established as the consumption activity; the answer leaves hotels/restaurants and investment drivers unstated. Stable receipts alone do not answer the consumption part. Sources: BOT_AUG_2026 PDF 1,2 (indexes 0,1); BOT_AUG_2026 PDF 1,2 (indexes 0,1); BOT_AUG_2026 PDF 1,2 (indexes 0,1). |
| `h03-workflow-abstention` | **partially supported** | The five contexts omit hotels/restaurants and the complete investment-driver phrase, so the full answer is unavailable in this retrieval. But machinery/equipment investment and detailed activities are present; a useful partial answer was possible. Sources: BOT_AUG_2026 PDF 1,2 (indexes 0,1); BOT_AUG_2026 PDF 1,2 (indexes 0,1); BOT_AUG_2026 PDF 1 (indexes 0). |
| `h03-workflow-w1` | **contradicted** | The returned BOT page-2 chunk names machinery/equipment, electrical/medical machinery, computer/office imports and vehicles. The blanket claim that no specific activities are given is false, even though consumption coverage is missing. Sources: BOT_AUG_2026 PDF 1,2 (indexes 0,1). |
| `h03-workflow-w2` | **supported** | A 2024 IEA source was returned, and forecasts are not observations. The generic caution does not make the relevant August-2026 BOT investment evidence unusable; the IEA distractor does not answer the question. Sources: IEA_SEA_2024 PDF 7,8 (indexes 6,7). |

Reference check: **supported**. The data-center driver is in the key highlight on the same source page, not inferred from the machinery detail.

Questions for the human reviewer:
- What minimum investment and consumption activities should appear in an acceptable brief?
- Would you accept an explicitly partial investment answer while requesting consumption evidence?

### h04: Under IEA STEPS, what annual electricity-demand growth and TWh levels are projected for Southeast Asia by 2035?

Required facts and observed coverage:

| Fact | Source | Retrieved: legacy / workflow | Answer: legacy / workflow |
|---|---|---|---|
| Electricity demand rises about 4% annually to 2035 in STEPS. | IEA_SEA_2024 PDF 7 (indexes 6) | complete / complete | complete / missing |
| The report’s starting demand level is over 1,300 TWh. | IEA_SEA_2024 PDF 7 (indexes 6) | complete / complete | missing / missing |
| Demand exceeds 2,000 TWh by 2035 in STEPS; do not substitute generation. | IEA_SEA_2024 PDF 7 (indexes 6) | complete / complete | missing / missing |

Statement and gap assessments (the structured record retains exact field/span locators and text hashes; unchanged output text is in the local packet):

| ID | Assessment | Reason and source |
|---|---|---|
| `h04-legacy-s1` | **supported** | Both the 4% demand growth and the separately labelled generation numbers are source-supported. However, the TWh clause answers generation, not the requested demand level; do not label the valid generation fact itself false. Sources: IEA_SEA_2024 PDF 7 (indexes 6); IEA_SEA_2024 PDF 86 (indexes 85). |
| `h04-legacy-s2` | **contradicted** | The 3%/10%/20% shares refer to solar PV alone. Applying them to all renewables changes the category; the report puts all-renewables generation above one-third in 2035. Sources: IEA_SEA_2024 PDF 7,86 (indexes 6,85). |
| `h04-workflow-abstention` | **unsupported** | All requested demand facts are together in returned chunk 6:2. Generation and scenario differences elsewhere do not justify an empty answer. Sources: IEA_SEA_2024 PDF 7 (indexes 6). |
| `h04-workflow-w1` | **partially supported** | The source gives rounded/bounded levels rather than an exact point estimate, but it does provide the requested STEPS demand baseline and above-2,000 TWh projection. APS is outside this question; generation figures are a different quantity. Sources: IEA_SEA_2024 PDF 7 (indexes 6); IEA_SEA_2024 PDF 86 (indexes 85). |
| `h04-workflow-w2` | **unsupported** | Different scenarios or different quantities do not establish contradictory facts. No incompatible same-scope annual demand growth rates are identified in this warning. Sources: IEA_SEA_2024 PDF 7 (indexes 6); IEA_SEA_2024 PDF 86 (indexes 85). |
| `h04-workflow-w3` | **supported** | The source is historical and its 2035 figures are forecasts. The question explicitly asks for that report’s projection, so the caution is appropriate context, not an abstention reason. Sources: IEA_SEA_2024 PDF 7,8 (indexes 6,7). |

Reference check: **supported**. The reference correctly uses demand above 2,000 TWh, not generation above 2,200 TWh.

Questions for the human reviewer:
- Would you remove generation context or retain it as separately labelled background?
- How would you correct the solar-versus-all-renewables sentence?

### h05: What regional EV battery-cell capacity and planned expansion does the IEA describe, and what is Indonesia and the Philippines’ combined share of mined nickel?

Required facts and observed coverage:

| Fact | Source | Retrieved: legacy / workflow | Answer: legacy / workflow |
|---|---|---|---|
| Existing regional EV battery-cell capacity was 16 GWh at end-2023. | IEA_SEA_2024 PDF 8,161 (indexes 7,160) | complete / complete | missing / complete |
| Planned committed additions were 39 GWh/almost 40 GWh by 2030, not total resulting capacity. | IEA_SEA_2024 PDF 8,161 (indexes 7,160) | complete / complete | partial / complete |
| Indonesia plus the Philippines supplied about 65% of global mined nickel, not refining. | IEA_SEA_2024 PDF 8,9,35 (indexes 7,8,34) | missing / missing | missing / missing |

Statement and gap assessments (the structured record retains exact field/span locators and text hashes; unchanged output text is in the local packet):

| ID | Assessment | Reason and source |
|---|---|---|
| `h05-legacy-s1` | **partially supported** | 39 GWh committed additions and 23 GWh preliminary announcements are supported. “Capacity ... increase to 39 GWh of ... additions” leaves stock versus additions ambiguous, and the existing 16 GWh stock is absent. Sources: IEA_SEA_2024 PDF 8,161 (indexes 7,160). |
| `h05-legacy-s2` | **supported** | The named countries and roughly 1% figure match the committed-2030 discussion. This should not be read as a statement about the current installed-capacity ranking. Sources: IEA_SEA_2024 PDF 161 (indexes 160). |
| `h05-legacy-s3` | **supported** | The 2024 announcement, 10 GWh, partnership and USD 9.8 billion are explicitly in PDF page 162 and the retrieved chunk. This is source attribution, not independent real-world verification; page 172 has a different date/budget whose relationship is unresolved (see SI-1). Sources: IEA_SEA_2024 PDF 162 (indexes 161); IEA_SEA_2024 PDF 172 (indexes 171). |
| `h05-legacy-s4` | **supported** | Correct only within its explicit “provided evidence” scope: none of the five captured contexts supplies the combined nickel percentage. The complete source and corpus DO supply about 65%; this is a retrieval miss, not global source absence. Sources: IEA_SEA_2024 PDF 8,9,35 (indexes 7,8,34). |
| `h05-workflow-c1` | **supported** | The cited chunk explicitly distinguishes 16 GWh existing stock, 39 GWh committed additions and 23 GWh preliminary announcements with their time bases. Sources: IEA_SEA_2024 PDF 8,161 (indexes 7,160). |
| `h05-workflow-c2` | **supported** | Countries, global proportion and 2030 committed-capacity context match the cited chunk. Sources: IEA_SEA_2024 PDF 161 (indexes 160). |
| `h05-workflow-c3` | **supported** | The cited executive-summary chunk explicitly links Indonesia’s expected hub role to its natural resources. Sources: IEA_SEA_2024 PDF 8,162 (indexes 7,161). |
| `h05-workflow-w1` | **partially supported** | Indonesia’s 2025/2030 capacity announcements are in a returned chunk, so the Indonesia absence is wrong. The captured contexts do not provide a Philippine battery expansion figure; that country-specific detail is not required by this regional question. Sources: IEA_SEA_2024 PDF 162 (indexes 161). |
| `h05-workflow-w2` | **unsupported** | Country-level figures for different years and a regional committed-additions figure are not automatically contradictory. The warning establishes no same-scope inconsistency. Sources: IEA_SEA_2024 PDF 8,161 (indexes 7,160); IEA_SEA_2024 PDF 162 (indexes 161). |
| `h05-workflow-w3` | **supported** | The publication year is 2024, and “may not reflect” current conditions is a qualified freshness caution. It does not negate the requested historical report summary. Sources: IEA_SEA_2024 PDF 7,8 (indexes 6,7). |
| `h05-workflow-w4` | **supported** | Within the five captured contexts, Malaysia/Viet Nam are named without their detailed country capacity additions. The full PDF page 162 has further details after the retrieved span. These country breakdowns were not required. Sources: IEA_SEA_2024 PDF 161 (indexes 160); IEA_SEA_2024 PDF 162 (indexes 161). |
| `h05-workflow-w5` | **supported** | No specific Philippine battery expansion figure appears in the captured contexts. This is a narrow local absence, not a verified claim that the entire report lacks it; it is also not the requested mined-nickel statistic. Sources: IEA_SEA_2024 PDF 162 (indexes 161). |
| `h05-workflow-w6` | **supported** | The dated source contains forecasts, and they should remain labelled projections. This does not answer or excuse the missing mined-nickel share. Sources: IEA_SEA_2024 PDF 7,8 (indexes 6,7). |

Reference check: **supported**. Almost 40 GWh is compatible with the detailed 39 GWh committed additions. The page-index-7 locator is incomplete for the word mined, which continues on index 8; index 34 supplies a complete statement. Add those locators only in a future dataset revision.

Questions for the human reviewer:
- Does the additions wording need clarification before use?
- Should the unrequested factory cost/timeline details be omitted pending resolution of SI-1?
- Which source span should support the mined-nickel percentage?

## Reference and source discrepancies

No reference answer was found to require a factual rewrite within this source audit. The h05 page locator needs qualification: PDF page 8 ends with the percentage and PDF page 9 supplies “mined production”; page 35 offers a complete alternate locator. “Almost 40 GWh” in the reference is compatible with the detailed 39 GWh of committed additions. References and benchmark locators remain unchanged.

**SI-1 - unverifiable source relationship:** PDF page 162 states a 2024 start-up announcement and USD 9.8 billion backing; page 172 describes an opening in 2023 and a USD 1.1 billion project. The pinned report alone does not establish whether these dates and budgets describe identical project/phase/investment scope. Neither paragraph is silently declared authoritative. Human reviewer should omit the optional facility detail or preserve explicit paragraph attribution until the relationship is checked. No external verification is performed in this audit.

The solar-versus-renewables error belongs to the generated legacy h04 answer, not the reference. The missing nickel answer belongs to retrieval coverage, because relevant unselected chunks exist (`IEA_SEA_2024:7:4` and `IEA_SEA_2024:34:1`). Do not infer missing knowledge in the complete report from a top-five retrieval miss.

## Prioritized development backlog

These are proposed follow-up changes, not implemented changes or demonstrated improvements. Use development cases; these five inspected cases are no longer unseen.

1. **P1 - Require question-fact coverage before declaring evidence unavailable; preserve supported partial answers.**
   Evidence: h02-workflow-abstention, h03-workflow-abstention, h03-workflow-w1, h04-workflow-abstention. Acceptance check: On development-only cases, require a supported partial answer when specific investment evidence is available, and no blanket missing-evidence statement when required facts were returned.

2. **P1 - Distinguish demand/generation, solar/all-renewables, stocks/additions, scenario and time scopes.**
   Evidence: h04-legacy-s2, h04-workflow-w2, h05-legacy-s1, h05-workflow-w2. Acceptance check: Use development contrasts with identical units but different measures/scenarios; no incompatible scope substitution or unsupported conflict label.

3. **P1 - Retrieve for each requested subtopic and inspect adjacent/complete evidence spans within the existing bounded workflow.**
   Evidence: h05-legacy-s4, h03-workflow-abstention. Acceptance check: A development battery-plus-nickel request must cover both subtopics and the complete mined-production unit; do not infer new benchmark improvement from these already inspected cases.

4. **P2 - Make gap messages specific to requested facts and distinguish captured-context absence from whole-source absence.**
   Evidence: h01-workflow-w1, h01-workflow-w2, h01-workflow-w3, h05-workflow-w1, h05-workflow-w4, h05-workflow-w5. Acceptance check: No invented requirement for unrequested country breakdowns or exact figures; freshness cautions must not suppress explicitly historical questions.

5. **P2 - Treat source/reference reconciliation as an explicit review task.**
   Evidence: h05-legacy-s3. Acceptance check: Flag SI-1 and propose a versioned locator update for h05 without modifying this frozen dataset or promoting source attribution to independently verified truth.

The existing [boundary-case findings](validation-2026-10-21.md#reserved-boundary-cases-with-the-real-local-model) remain follow-up risks. This audit does not re-adjudicate h06-h10 or convert automated boundary attempts into human evidence.

## Human reviewer checklist

- Read the question, both unchanged outputs and the source excerpts before consulting Ragas scores.
- Check metric, category, time period, scenario, units and each selected citation.
- Decide whether the required-fact checklist is appropriate; record disagreements with this assistant audit.
- Distinguish an unsupported claim, a supported but incomplete answer, an unjustified abstention and a genuine retrieval miss.
- Resolve or explicitly defer SI-1 and any layout/source ambiguity; do not manufacture certainty.
- Enter your own reviewer alias, correctness/completeness judgments and notes in the existing `human_review.csv` only after review. It remains untouched and pending here.

## Completion record

Coverage: 10 legacy response units, 6 workflow claims, 15 warnings, 3 abstentions and six workflow citation links. These are coverage counts, not model-quality scores.

Integrity and coverage validation is recorded in the structured audit and the ignored local verification report. Human adjudication, external reviewer usage, usefulness and production readiness remain unestablished.
