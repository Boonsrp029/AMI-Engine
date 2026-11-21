# Fact coverage for concurrent evidence selection

The cq1-a20 replay showed that projection restores an omitted background unit through fallback. An earlier omission prototype also allowed a required maintenance cost to disappear when another claim shared its component. [Omission replay](../scoped-explicit-subject-development-2026-11-13/cq1-a20-omission-replay.json) · [Omission boundary results](../scoped-explicit-subject-development-2026-11-13/omission-boundary-results.json)

The [offline check](check-fact-coverage.py) exercises a proposed distinction between a requested fact, evidence that answers it directly, and text needed to interpret that evidence. One span can answer multiple facts. Two distinct facts in the same component require separate decisions. A fact without support remains explicitly unresolved. Necessary context stays attached to the selected fact and does not become a separate answer claim. [Seven check results](fact-coverage-results.json)

## Proposed contract change

1. Derive explicit fact slots from the question or a reviewed subtask plan before inspecting evidence. Record each slot's original question anchor and originating component. Do not supply reference answers to the model.
2. Require an exact span decision for each fact slot. Only use spans in the slot's bound branches. Preserve source and span hashes, offsets, the role of any context span, and the original mapping. Conflicts retain opposing evidence and unresolved facts retain scoped gaps.
3. Compose over the retained evidence. Require independent support for number, measure, geography, denominator, period and modality. Prevent fallback from reintroducing background excluded from the projection. Keep raw selection, application projection, fallback and editorial wording separate.

The fixtures manually declare which passages answer each fact. The prototype verifies accounting against those declarations. It does not establish that the application can derive fact slots or identify direct support from arbitrary questions and sources. An incorrect classification could still omit a fact or accept related background. Before runtime integration, test candidate slot derivation and span assignments against independently labeled examples without handing their answer labels to the selector. Include multiple facts in one component, context-dependent evidence, partially supported requests and conflicting records.

No runtime code or frozen evidence changed. No model calls ran. The failed diagnostic remains closed, and the previous CQ1 roster remains preserved. Integration would change the private concurrent mapping contract. Generation would require a separate, frozen allowance.

## Current selector baseline

The [offline baseline](check-fact-selection-baseline.py) supplies only questions and candidate text to the existing request splitter and relevance hints. It loads assistant-authored [fixture labels](fact-selection-labels.json) afterward. Four cases cover distinct costs, contextual reporting, partial support and conflict.

- One component covered the two requested 2021 cost facts. The hint list kept installation cost and a 2023 forecast while omitting the actual maintenance cost.
- The 2021 repair-cost request received hints for a different measure and a different year. It has no directly responsive passage in the fixture.
- Both reporting components received the responsive statement and its temporal context. Both conflicting capacity values also appeared in that case's hints. Hints carry no decision about whether a passage is direct support, context or one side of a conflict.

The baseline confirms that the existing hints cannot be used as an evidence allowlist. The next candidate should begin with separately anchored cost fields and test measure/year filtering without discarding applicable context or opposing records. This check exercised ranking hints only. It did not run the mapper or score generated drafts. [Baseline results](fact-selection-baseline-results.json)

## Literal cost candidate

An offline candidate split the coordinated installation and maintenance request into two measure/year slots. It matched both actual 2021 cost spans and excluded the 2023 forecast. In the partial fixture, the maintenance slot matched and the repair slot had no exact candidate. A separate fixture preserved both same-year storage values and excluded the prior-year value, capability statement and definition. An empty candidate list only describes this matcher's output. It cannot establish that evidence is absent. [Candidate and checks](check-cost-fact-anchors.py) · [Results](cost-fact-anchor-results.json)

The parser covers a narrow sentence and question shape. It declined the historical reporting and reservoir cases. It does not validate that two costs share a subject or geographical scope, so it cannot turn opposing candidates into a confirmed conflict. Keep it offline. The evidence supports evaluating candidate hints and their scope, not using this rule to restrict all model choices or restart CQ1.

## Exact excerpts and context roles

An [offline resolver](check-exact-fact-decisions.py) uses the existing exact-span verifier and stores a direct span, answer offsets and same-record context separately for each requested fact. With fixed decisions for the unmodified cq1-a20 source, it returns “electricity use” and “the utility” from one supporting sentence while preserving “could periodically report” in that sentence. The contextual sentence is attached as context. It is not a standalone claim. Missing decisions, an unbound source, changed span text, invalid offsets and duplicate roles were rejected. An explicit unresolved result was preserved. [Check results](exact-fact-decision-results.json)

The negative semantic control deliberately assigned “electricity use” to the recipient. It passed structural validation. Exact offsets are useful for auditing a selection but cannot qualify its meaning. A candidate runtime contract would therefore require the mapper's direct/context roles and exact-source adjudication during qualification. This prototype covers a single direct span per fact and no conflict state. The broader proposal must retain competing records and independently necessary evidence before it can replace current selection.

The model-facing contract would change, although the public Draft would be unchanged. The next decision is whether to develop that private contract offline or retain the current inference path. Do not use a case-specific alias, reviewed answer, or these fixed decisions as production inputs. A model run requires a separate explicit grant after the chosen contract is implemented and frozen.

## Multipassage and conflict states

The [offline extension](check-multipassage-fact-decisions.py) resolved a canal-access fixture using two passages, preserved two competing width records as separate alternatives and kept an unanswered fees request explicit. Six negative checks rejected a single conflict side, duplicate direct span, unbound source, evidence attached to missing status, empty support group and reused source identity across alternatives. [Nine check results](multipassage-fact-decision-results.json)

The checks validate assignments after they are supplied. Distinct record IDs alone do not establish a real disagreement. Review must confirm a shared subject, period and measure and verify each claim against its extracted evidence. The prototype has no model-facing schema or composition integration. The decision before implementation is whether to introduce fact-level decisions for the opt-in concurrent path. The failed cq1-a20 result and the qualification roster remain preserved.

## Model-facing schema and request size

The [offline request check](check-fact-wire-budget.py) captured the real cq1-a20 mapper payload with sockets blocked and measured a draft fact-selection schema against the same question, candidate spans and branch bindings. The content plus existing framing and completion reservation was 3,597 tokens for the current request and 3,330 for the prototype, within the 4,096-token window. Static schema token counts fell from 18,220 to 377 by replacing generated ID enums with strings. These are local counts. Ollama decoding behavior and actual runtime usage remain unverified. [Measured request sizes](fact-wire-budget-results.json)

The smaller schema also removes constraints that the current decoder encodes. Before activating it, validate every fact ID, state, span ID, offset, request/branch binding and context role before composition. Preserve the existing geographic, temporal, numeric, conflict and injection checks. The prototype does not carry the existing geography fields or enforce per-branch coverage, so it cannot serve as a drop-in replacement. Keep the shared fallback and sequential workflow intact. The opt-in projection would need a separate treatment for context spans and unresolved facts so context cannot emerge as a fallback answer.
