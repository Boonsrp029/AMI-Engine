# Verified membership rendering — offline integration

The owner chose “Render verified phrases (Recommended)” for offline implementation. Composer v10 requires both model-selected phrases in their original slots, compares the complete phrases against the verified membership span and uses the bound affirmative relationship to render one cited sentence. It records the rendered sentence, span ID, source ID, content digest and offsets separately from the raw response and editorial correction. Ambiguous category matches continue through the existing general workflow. Conversion sentences and table-row selection keep their existing behavior.

The socket-blocked replay reused the exact v9 mapper and composer bytes and produced a cited candidate containing both groups. Replaying the existing NeMo boundary used mock accept and block outcomes. Both received the fully rendered sentence and the pinned source statement. The historical v9 failure remains unchanged. No actual model or NeMo invocation ran or persisted a review draft.

100 targeted tests passed. The stopped result and dependency manifest digests match their previous values. The revised 20-case pool remains frozen. Next freeze a new development contract for the current runtime. A separate direct run grant is required.
