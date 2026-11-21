# Decision on source-bound category prose

Both member phrases in the actual v9 response exactly matched the source. Neither contained the requested affirmative sentence. The v9 result failed before final NeMo and stays failed. The offline probe ran with sockets blocked and substituted only the membership renderer in the local process. It projected the archived response to one cited candidate, with no fallback or editorial revision. The probe did not start NeMo or persist a draft.

| Option | Private requirement | Result and trade-off |
| --- | --- | --- |
| Application renders verified phrases | The model provides both exact source phrases in their required fields. Validate phrase order and complete qualifiers, then render one sentence from the verified category and its source groups. | The saved response passes these phrase checks in replay. The application authors the clause and logs it as rendering. |
| Keep full model-written sentences | The model supplies one complete affirmative sentence per field. Keep sentence validators and explore whether the decoder can enforce a supported clause shape. | Preserves fully model-written prose. The saved response fails the sentence check. Real grammar support and model compliance are unverified. |

Recommended: application rendering for this narrow, unambiguous membership path. Leave conversion prose and other claim types on their existing routes. A missing qualifier, swapped field, altered group, ambiguous category or conflicting definition cannot be silently resolved by the renderer. Final NeMo still checks the cited draft. Keep raw fields, application rendering and human correction separately attributable.

Candidate sentence: “The other gases category includes blast furnace gas and other manufactured and waste gases derived from fossil fuels.” It cites eia-generation-2023. Six additional synthetic checks verify both options with different facts, including qualifier removal and wrong-group rejection. This is an offline design decision, separate from a generation grant and owner draft acceptance.
