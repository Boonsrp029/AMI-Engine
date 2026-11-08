# Workstream B: local retrieval adapter

Status: implementation and offline verification record for the first corpus-
backed `ami-subtasks-v1` adapter. This does not qualify model quality or a live
deployment.

## Existing behavior retained

`src/agents/local_retriever.py` remains the ranking authority. The adapter uses
its `_read_records`, `_tokens`, and `_bm25_scores` functions with the existing
positive-score rule, stable input-order tie break, and a fixed five-record cap.
It does not call the engine, a model, Ragas, Databricks, or a hosted service.
The default sequential workflow and public retriever API are unchanged.

`LocalBM25Adapter` stores only a corpus path, so the callback is picklable for
the existing stored runner. It reloads a fresh single-file snapshot per
operation, checks the exact file SHA-256 against the launched identity, and
checks the file again immediately before returning. Cancellation/deadline is
checked before loading, after loading and before return.

## Evidence envelope decisions

- A retrieval hit becomes a `support` candidate in original rank order. Empty
  positive-score results become a completed `missing` result with
  `no_matching_evidence`. Multiple hits do not imply semantic conflict.
- Inspection only accepts IDs from the exact completed results listed in the
  task's declared dependencies. It revalidates the requested records against
  the current pinned file and returns the requested order, without guessing
  neighbors.
- An inspected record that was context-only remains context-only. Inspection
  cannot promote it into claim support. A context-only inspection result is
  `missing` with diagnostic `none`; this means no support-role source was
  available, not that the corpus search itself had no hits.
- Original source content is never title-prefixed or rewritten. `timestamp`
  and `ingested_at` are not treated as publication dates. The current corpus's
  `source` field is a publisher label, not a URL; `url` stays empty unless a
  separate absolute HTTP(S) `url` field exists. `doc_name` and zero-based
  `page_num` are retained only when valid.
- Stable `feed_id` is used when present. Missing IDs retain the same deterministic
  layer/accepted-row-index fallback as the existing BM25 reader. Duplicate IDs
  fail closed, even when their text is identical. Distinct IDs with identical
  text remain distinct evidence records.
- Invalid JSON, malformed rows, invalid metadata, corpus changes, unauthorized
  inspection IDs, and dependency/source mismatches are technical failures, not
  evidence gaps. The adapter does not infer contradictions; synthesis owns
  semantic conflict and answer validation.

## Ownership and handoff

Owned files for this pass:

- `src/pilot/subtasks/retrieval.py`
- `tests/test_subtask_retrieval.py`
- `docs/concurrency/b-retrieval-adapter.md`

Workstream C can consume the adapter through `run_plan(..., operation=adapter)`
and the existing `Report`. It should bind claims to completed branches and
cite only `support` sources from those branches. This adapter proves source
identity and structural provenance; it does not prove that a retrieved passage
semantically entails a generated claim.

Workstream D can use the scheduler-through-adapter test as a module-level
integration example. D still owns cross-component cancellation, restart,
review, export, and broader race tests. No scheduler, schema, API, Store, or
synthesis file was changed here.

## Offline checks

The focused adapter module passes **11 tests**. The combined targeted run of
the adapter module, existing subtask contract/scheduler tests, and scheduler
execution integration passes **62 tests**. Coverage includes the checked-in
20-row Silver snapshot, rank parity with the public BM25 retriever, a
deterministically reordered pair of branches, dependency-limited inspection,
and source-origin preservation. Tests use local files and deterministic
coordination only; they make no model or network calls.

These checks establish adapter contracts and scheduler integration, not
semantic relevance, model answer quality, independent usefulness, or production
qualification.

Syntax compilation, `git diff --check`, and a whitespace check over the three
new files pass. No dependency manifest was edited. Current SHA-256 values are:

| Manifest | SHA-256 |
|---|---|
| `requirements.txt` | `4bc238785549332a1196ab5954f996890ed12b1370c1834f396ede567af64726` |
| `requirements-etl.txt` | `6d987c055f02ff572fc60c1cf87a922fe573ff417641307700d1b3fa6fddee1b` |
| `requirements-serving.txt` | `b9f8abc4b20928e4351088a14e17a2a94f6322499fbd794d5ef3ec320bc4e7be` |

`pip check` does not pass in the existing virtual environment. It reports
`protobuf 7.36.0` conflicting with the installed `databricks-sdk 0.94.0` and
`databricks-vectorsearch 0.75`, and installed `openai 1.109.1` conflicting
with `openai-agents 0.22.0` (which requires OpenAI 3.x). This adapter pass did
not alter dependency declarations or attempt to repair the environment.
