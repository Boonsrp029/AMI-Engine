# Explicit requested-member coverage

The 20 November CQ1 batch stopped at cq1-a48 after three attempts. Its selected passage contained sulfur and tire-derived fuel; the raw composer named sulfur only. NeMo returned NO without a retained explanation. The failed attempt, two preceding passes and seventeen unattempted cases retain their original status. The earlier r07 failure and original nineteen reserved records also remain historical evidence.

## Current behavior and focused change

The existing category-definition path recognizes questions asking which members belong to a category and can render two verified source phrases. It does not recognize a yes/no question asking whether two named members belong to a source-listed category.

This pass strengthens the opt-in whole-span composer's existing completeness requirement. For a narrowly recognized question, one selected affirmative source list must explicitly name both requested members and match the requested category. Only then does the composition input receive a two-name coverage checklist. The original response schema and model-written prose continue to apply. A raw answer omitting either complete name fails before projection, fallback or safety. No answer repair or additional model call is introduced.

The recognizer leaves ambiguous matches, separately sourced members, absent support, negative lists and other question forms on the existing general path. A check for names establishes lexical coverage. It does not establish correct polarity, semantic support or scope. Final safety and exact-source review remain necessary. The NeMo NO reason from the original run remains unknown.

## Ownership and implementation passes

C owns the new private membership helper, its synthetic regressions and integration in `_scoped_generation.py`. Composition instructions advance to `cq-composer-v19-membership-coverage`. A's orchestration, B's retrieval, D's execution controls and the default sequential workflow require no edits.

1. Snapshot existing implementation, owner records, constraints and retained qualification evidence.
2. Add the coverage checklist and raw-output rejection through the normal scoped-composer entry point. Test different facts involving recovered construction materials, omissions, source identity, cross-unit substitution and missing evidence.
3. Replay the archived cq1-a48 mapper/composer responses with sockets blocked. Reconstructed requests are identified as such. The replay must reject the saved incomplete sentence without changing its historical assessment.
4. Prepare two consumed development cases and a separately revised future pool. Execute only under a new applicable grant. Qualify real outputs through technical, exact-source, completeness, safety and storage gates.

## Evidence and remaining qualification

The new development packet is in `reports/workstream-c/scoped-membership-coverage-development-2026-11-25/authorization-packet.md`. It fixes the model identity/settings, case order, output directory, source hashes and limits. The first case exercises explicit membership coverage; the second checks the previously declared category renderer.

The future pool retains seventeen unattempted cases with unchanged questions, plans, source corpus bytes and scope sidecars. Three consumed entries are replaced by unused EIA glossary questions on newly captured source facts. The source preparer has inspected their references. Only those three cases use the glossary corpus. Counts remain 10 answerable, 2 partial, 4 missing, 2 conflict and 2 injection. Thresholds remain 9/10, 2/2, 4/4, 2/2 and 2/2 with zero critical errors. Compilation requires two exact current development passes and grants no execution permission.

New exact outputs require owner source/wording adjudication before owner acceptance. Stored revision approval/export remains a separate existing action. Offline tests and saved-response replay do not establish new model quality or production qualification.
