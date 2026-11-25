# Explicit member fields for supported membership questions

The actual cq1-a48 mapper selected both requested members in one direct span. The raw composer returned one member. The current free-text schema parsed that answer before the new completeness guard rejected it. Repeating the same instructions has not established a quality pass.

The proposed offline change extends the already established verified-phrase membership route to a narrowly recognized affirmative source list answering “does category C include A and B?” Each source-listed requested phrase becomes a required target field. The existing renderer checks both complete phrases against the selected source relation and constructs one cited category sentence. Raw fields, application rendering, fallback and owner edits remain separately recorded. A field or qualifier mismatch fails explicitly. Partial, missing, conflicting or ambiguous evidence retains the existing general handling.

This changes the private response expected for the recognized yes/no membership shape. The public Draft schema, sequential workflow, retrieval, source identity, model/settings, call ceiling and approval/export behavior remain intact. The proposal is not activated in the current runtime and grants no generation.

| Choice | Composition behavior | Validation consequence |
| --- | --- | --- |
| Extend verified-phrase rendering | Require both exact source-listed phrases, then use the existing category renderer | A missing field fails parsing; a duplicated, altered or shortened phrase fails exact source validation |
| Keep model-written prose | Introduce one required sentence field per requested member, then validate and combine those sentences | Both fields are structurally required; correct sentence meaning, source scope and complete qualifiers remain necessary validation/review questions |

I recommend extending the verified-phrase renderer for this narrow membership shape. It reuses the previously accepted category-definition route and avoids another paraphrase of the selected names. It does not establish general semantic support or guarantee correct evidence selection. Final safety and actual-output source review remain required.

composition-contract-prototype.json contains six socket-blocked fixed-response checks with different facts involving reclaimed construction products. The existing schema and renderer accept both full phrases and reject a missing second field, duplicate first phrase, lost qualifier, wrong unit and the old incomplete free-text response. No runtime activation or actual inference occurred. These checks establish the proposed interface behavior only.

The next implementation should be isolated in a new preparation directory and version, preserving the current failed batch and its frozen source. Any following development run needs a new applicable allowance. The reserved qualification pool remains frozen and unattempted.
