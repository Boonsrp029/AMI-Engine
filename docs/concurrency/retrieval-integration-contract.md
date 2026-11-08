# Corpus-backed retrieval integration contract

Status: implementation-ready interface for Workstream B, based on the current
`ami-subtasks-v1` scheduler and C synthesis implementation. This is an offline
integration specification; it does not authorize model generation, live services,
browser activation, or deployment.

## 1. Existing integration boundary

The opt-in path is already wired as:

```text
Plan + existing queued Store run
  -> run_stored_plan(..., operation, compose, safety)
  -> run_plan(..., operation(Context) -> Result)
  -> Report(results in declared plan order, deduplicated sources and origins)
  -> C mapping + branch bindings + composition
  -> final safety check
  -> parent-only, attempt-fenced draft persistence
```

The sequential browser path and `PilotEngine.run()` remain independent and are
still the default. A B adapter implements the trusted `operation(Context) ->
Result` callback. C consumes `Report.results` and `Report.sources`; a component's
evidence must be supported by a branch explicitly bound to that component.
The runner verifies attempt, plan and corpus identity, source/citation validity,
final safety and publication fencing. SQLite remains parent-writer-only.

Relevant existing interfaces are `Plan`, `Subtask`, `Identity`, `Context`,
`DependencyRef`, `Result`, `Source`, `Report` and `AggregateSource` in
`src/pilot/subtasks/contracts.py` and `scheduler.py`; `project_report()` and
`compose_report()` in `synthesis.py`; and `run_stored_plan()` in `runner.py`.
The canonical rules and lifecycle are in [contract-v1.md](contract-v1.md).
No shared schema or scheduler redesign is needed for the first adapter.

## 2. B adapter inputs and outputs

### Inputs

| Input | Existing field / rule |
|---|---|
| Analyst request | `Plan.query`; this remains the parent request and is not replaced by a subtask query. |
| Branch operation | `Subtask.operation`: `retrieve` or `inspect_sources`. |
| Retrieval input | `Subtask.query`, 1–500 characters; required for `retrieve`. |
| Inspection input | `Subtask.source_ids`, one to five IDs; required for `inspect_sources`. Each ID must occur in a completed declared dependency result; inspection cannot be used as an arbitrary corpus-ID oracle. |
| Provenance | `Context.identity` (run, attempt, plan and corpus hashes), `Context.child_attempt_id`, and `Context.dependency_refs`. |
| Limits | 1–5 declared subtasks, retrieval concurrency 1–2 (default 2), max 5 returned source records per branch, branch timeout default 30 seconds, parent deadline at most 180 seconds. |
| Cancellation | `Context.cancelled()` and `Context.cancellation` / `parent_cancellation`; the adapter must check before expensive work and before returning. |

The adapter must be importable and spawn-pickleable when used with the stored
runner. It receives its configured corpus path as adapter configuration; it must
hash the exact file bytes and require equality with
`Context.identity.corpus_sha256` before retrieval and before returning. It must
not write the Store, call a model, call a hosted service, or let source text
authorize another operation.

### Result envelope

Return the existing frozen `Result`, echoing the exact launched identity and
dependency refs:

```python
Result(
    identity=context.identity,
    subtask_id=context.task.subtask_id,
    child_attempt_id=context.child_attempt_id,
    dependencies=context.dependency_refs,
    outcome="evidence" | "missing",
    sources=(...),
    elapsed_seconds=<finite nonnegative duration>,
    diagnostic="none" | "no_matching_evidence",
)
```

Each `Source` carries `source_id`, exact original `content`, its UTF-8 SHA-256,
the same `corpus_sha256`, role (`support` or `context`), title, source URL if
actually available, publication date if present, document name and zero-based
page index if present. Do not put a publisher label into `url`; for the current
Silver fixture `source` contains publisher names and there are no URL, published,
document-name or page-number fields. Missing metadata stays empty/unknown.
Never use title-prepended search text as evidence content. Return sources in
original backend rank order; rank is represented by tuple position, since the
current `Source` schema has no score or rank field.

For `inspect_sources`, require dependency results and require every requested
ID to be among their returned source IDs. Re-read only those records from the
pinned corpus and verify their identity/content hash before returning. The
requested records can retain `support`; any same-document/page neighbors that
the source metadata can establish may be returned as `context`. The current
Silver fixture has no document/page metadata, so inspection returns the
requested records only. An unknown ID or an ID not authorized by a declared
dependency is invalid operation input (technical failure), not a missing
answer.

For the first adapter, BM25 hits are support records and no-hit results are
`outcome="missing"`, `diagnostic="no_matching_evidence"`, with no support-role
records. `missing` may carry context-role records only. `conflicting` exists in
the generic envelope but BM25 ranking cannot establish semantic conflict; B
must not infer conflict merely because multiple records are returned. A later
conflict detector needs a separately specified and tested rule.

### Identity, ordering and aggregation

- The parent request, plan and every branch result pin the SHA-256 of the same
  exact single corpus file. A changed, missing or unreadable file is a technical
  branch failure; it is not a missing-evidence answer.
- Use the source's stable `feed_id` as `source_id`. Reject duplicate IDs and
  collisions where an ID maps to different content or metadata. The existing
  BM25 reader has a deterministic layer/record-index fallback for missing IDs;
  the B adapter must either preserve that exact fallback and pin it to corpus
  bytes, or fail closed. It must document which behavior it implements.
- Echo `context.dependency_refs` exactly. The coordinator checks all identities
  and computes dependency-result hashes; adapters cannot substitute another
  branch attempt's data.
- `run_plan()` returns results in declared plan order regardless of finish
  order. Each adapter's `sources` order is preserved within its result.
- Aggregation deduplicates only a source ID whose non-role fields match exactly;
  differing content or metadata under one ID fails. Identical records retain
  every `(subtask_id, role)` origin. No evidence is silently truncated.
- C must bind each answer component to its branch IDs and may cite only support
  sources returned by those bound completed branches. Context-role rows are
  visible as context, not citation support. Structural linkage is not semantic
  entailment; C retains responsibility for claim validation and completeness.

### Failure and partial-result semantics

| Condition | Adapter/coordinator result | Composition effect |
|---|---|---|
| Valid ranked hits | Completed `evidence` result | Available to C, subject to mapping and support validation. |
| No BM25 result above the existing positive-score rule | Completed `missing` result with `no_matching_evidence` | A completed evidence gap, distinct from worker failure. C may return a supported partial brief from other required branches. |
| Optional branch fails / times out | Failed/cancelled branch; explicit `Report.missing_branches` | Composition may proceed only when required branches completed; partial warning is added. |
| Required branch fails / times out / is blocked | Required branch failure; remaining branches are cancelled/fenced | No composition or draft publication. |
| Corpus hash mismatch, invalid JSON/schema, duplicate/colliding source identity, malformed output, identity/dependency mismatch | Technical failure, never `missing` | Required/optional policy above applies; no silent fallback. |
| Cancellation or deadline before accepted completion | Cancelled/failed; late result fenced | No late evidence enters aggregate or persistence. |

Automatic retry is not allowed. An explicit retry creates a new parent attempt
and fresh child IDs. Worker diagnostics must be bounded and contain no raw
tracebacks, credentials or untrusted content dumps.

## 3. First supported backend and corpus prerequisite

**First supported backend:** local BM25, using the existing deterministic
implementation in `src/agents/local_retriever.py` (or the already-loaded raw
search path in `src/pilot/engine.py`) without changing its ranking algorithm.
Use a fixed per-branch limit of five, consistent with `Result.sources` max size
and the current retriever's default. `Subtask` has no `top_k` field, so exposing
a configurable branch limit would require an explicit contract revision.

**First pinned corpus:** the checked-in single-file export
`data/silver_level/silver_market_feeds.json` (20 rows at inspection), or another
single JSON export with the same record shape. The stored runner hashes one file
with `Path.read_bytes()` before and after the run; a directory accepted by the
standalone BM25 API is not supported by this runner contract. Keep the same
canonical file path/hash in `Store.create`, `Plan.corpus_sha256` and
`run_stored_plan(corpus_path=...)`.

The current fixture provides `feed_id`, title, publisher label, raw/clean text
and sector, but no publication timestamp suitable for `Source.published`, URL,
`doc_name` or `page_num`. This corpus is suitable for proving the adapter
contract and BM25 overlap; it cannot prove dated/page-resolvable source behavior
or live-source quality. For those fields, a future single-file prepared corpus
must include verified metadata. Folder-wide Meridional ingestion, dense/local
embeddings, Databricks Vector Search, rank-score exposure and conflict
classification remain later decisions, not implied by this first implementation.

## 4. Ownership and integration map

| Workstream | Owned files | Dependency / integration rule |
|---|---|---|
| **A — scheduler and shared runtime** | `src/pilot/subtasks/contracts.py`, `scheduler.py`, `persistence.py`, `runner.py`, `_handoff.py`; shared `Store`, process/runtime and API changes remain A-owned if proven necessary. | B uses the existing contracts. A alone changes shared runtime/schema/API/identity/worker files; no such change is required by this adapter specification. |
| **B — retrieval adapters** | New `src/pilot/subtasks/retrieval.py` (or a narrowly named adapter module) and new `tests/test_subtask_retrieval.py`; B may add adapter-specific fixtures under `tests/fixtures/subtasks/`. | Implement both declared read-only operations against the pinned local JSON corpus. Import contracts; do not edit scheduler, Store, Plan/Result schema or existing local BM25 behavior. |
| **C — synthesis** | `src/pilot/subtasks/synthesis.py`, C-owned validators/helpers and C unit tests. | Consume A `Report` and B `Result` envelopes; own component-to-branch bindings, support-only citations, factual coverage, conflict/partial handling. Do not edit B adapter. |
| **D — cross-component reliability** | `tests/integration/subtasks/` integration tests and D-owned integration fixtures. | Exercise actual B callback through A scheduler and C composition, using synthetic fixed records/barriers. Do not repair module-owned test fixtures; report failures to A/B/C owner. |
| **E — progress API/UI** | UI: `src/pilot/index.html`, `tests/browser/progress-interface.cjs`, `tests/test_progress_interface.py`, `docs/concurrency/progress-interface-e.md`. API handoff: `docs/concurrency/e-api-handoff.md`. The already integrated GET route is in A-owned `src/pilot/api.py` and `src/pilot/_identity.py`; its projection is A-owned `src/pilot/subtasks/persistence.py`, backed by `src/pilot/store.py`. | E consumes A's read-only `/api/runs/{id}/progress` projection. A retains ownership of the route, identity policy, snapshot reads and projection. Retrieval fields are not a second progress schema; no E changes are required for B. |
| **F — packaging/CI** | F packaging workflows/scripts/docs explicitly assigned by F. | After A–E interface stabilization, pin corpus file/image/source identity and test sequential-default plus explicit opt-in mode. No publication is included. |

Cross-workstream implementation must use isolated worktrees and the current
ownership table. `src/pilot/engine.py`, `src/pilot/api.py`, `src/pilot/store.py`,
`contracts.py`, scheduler and C synthesis are not shared edit targets for B.

## 5. B implementation passes and acceptance

1. **Freeze adapter input/output fixture.** Build a tiny single JSON fixture with
   explicit unique IDs, text, publisher, and optional dated/page metadata. Hash
   exact bytes. Include equal-score rows, zero-hit query, malformed rows, duplicate
   IDs and same-ID/different-content collision.
2. **Implement read-only local adapter.** It loads/verifies the pinned file,
   uses the existing BM25 scoring/tokenization and stable input-order tie break,
   returns up to five exact-content `Source`s, and handles both `retrieve` and
   `inspect_sources`. Inspection is limited to requested known IDs and never
   opens arbitrary paths. Add cancellation/deadline checks around load/search.
3. **Validate envelope and provenance.** Return exact `Identity`, child ID,
   dependency refs and elapsed time; verify content hashes, corpus hash, field
   provenance, source ID uniqueness, support/context roles and declared operation
   arguments. Invalid corpus/identity is technical failure; zero hits is
   completed missing evidence.
4. **Demonstrate integration.** Pass the callback through `run_plan` and C's
   `project_report` using fixed synthetic mapping/composition and confirm stable
   ranked order, cross-branch origins, citation branch binding, and failure
   fencing. D owns the full barrier/cancel/restart/review-export integration
   scenarios.

Acceptance checklist:

- [ ] Same file bytes match `Plan`, existing parent run and adapter on entry and
  return; changed bytes fail as technical errors.
- [ ] Independent branch results preserve existing BM25 tie/rank order and
  overlap only up to the plan limit of two; no model call occurs.
- [ ] `feed_id`/fallback IDs are deterministic, unique and collision-checked;
  exact source content and available metadata survive unchanged.
- [ ] `inspect_sources` requires declared dependencies, accepts only IDs
  returned by those completed dependencies, and reads no arbitrary filesystem
  path or network data.
- [ ] Empty search is a completed missing result; corrupt inputs, collisions,
  deadline/cancellation and invalid identities are not mislabeled as absence.
- [ ] Dependency hashes/identities are echoed exactly; aggregator ordering and
  source-origin retention are stable across completion orders.
- [ ] C cannot cite context-only or unbound-branch sources; partial and required
  failure policies remain unchanged.
- [ ] Targeted tests, full integrated offline suite when integration changes
  justify it, `pip check`, dependency-hash checks and `git diff --check` pass.
- [ ] No generation, Ragas, hosted/Databricks calls, dependency change, public
  API/schema migration, approval/export, commit/push or deployment occurred.

## 6. Open decisions and handoff

No unresolved choice blocks B's first local adapter if the inputs stay as
specified. Review before expanding scope:

- Should the first source corpus require an explicit stable `feed_id`, or retain
  the existing deterministic layer/index fallback?
- What future prepared export supplies publisher URL, publication date and
  locators, and how will it retain a canonical single-file hash?
- Is BM25 `missing` defined solely as no positive score (recommended parity with
  current retriever), or should a future calibrated threshold be separately
  specified? Do not tune a threshold in B's adapter pass.
- Hosting the corpus, local model/GPU resource budgets, Databricks fallback,
  retrieval-concurrency increases and concurrent whole analyst requests remain
  unselected. Keep model access serialized at one and retrieval concurrency at
  no more than two.

**Next implementation step:** B creates an isolated worktree and implements
`src/pilot/subtasks/retrieval.py` plus its unit tests against the single-file
fixture above. B consumes, but does not modify, `Plan`/`Result`/`Source`,
`Context`, `run_plan()` and `project_report()`. When B's target tests pass, D
adds one cross-component fixed-response integration case; C participates only
if a concrete support-binding defect appears. A integrates only an evidenced
shared-runtime defect. Exact current code/tests/evidence remain authoritative;
the historical v1.69 quality limitations and closed generation allowances are
unchanged by this design document.
