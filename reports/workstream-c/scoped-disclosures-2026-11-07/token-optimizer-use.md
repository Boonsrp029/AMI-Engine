# Token Optimizer applied — 7 November 2026

Used the user-provided local package's `plugins/token-optimizer/skills/token-optimizer/SKILL.md`
and its Codex workflow. Runtime explicitly set to Codex, Python to the existing
project interpreter. Audit state/output was directed into this evidence directory;
no settings, hooks, memories, skill inventory or dependency declarations were edited.

The read-only `report`, `coach --json`, `quality current --json`, `codex-state --json`
and `codex-doctor --project ... --json` outputs are retained. Doctor identifies
plugin version **5.13.66**, missing compact-prompt/global-hook configuration and
optional status-line/project-hook warnings. Its exit 1 reports missing setup,
not an AMI application failure. Automatic Codex output substitution/compression
must not be claimed active. No setup change or paid keep-warm action was performed.

The tool estimates startup overhead at **21,206 tokens** and reports session
quality **56.2 / C**. These are the optimizer's estimates/heuristics, not measured
AMI answer quality, exact available context, subscription quota or production
readiness. Do not invent a verified context-saving percentage from them.

Applied working practices: bounded source reads, summarize diagnostic JSON rather
than printing it, retain full logs, targeted checks before one justified integrated
run, deterministic fixtures and no repeated model attempts. New application code
has no optimization dependency or additional model call.

An offline pinned-tokenizer comparison of consumed cq-p02 mapper payloads measures
**715 → 460 message-content tokens**, a reduction of **255**. Conservative totals
including 256 framing and 900 completion reservations are **1,871 → 1,616**; separate
schema-format counts are **1,069 → 953**. This reflects the deliberate new request
contract, not invisible plugin compression. Semantics differ, so it is not a quality
A/B test or a claim about actual generated output. New server token counts and
latency remain unknown. See `offline-context-comparison.json` and its reproducible
network-blocked script.

Codex configuration savings remain **unmeasured**, because no configuration was
changed. Any later hook/compact setup must have a backed-up concrete diff and
specific scope approval; it is separate from the approved AMI C implementation.
