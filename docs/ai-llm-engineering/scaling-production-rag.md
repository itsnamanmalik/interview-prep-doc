---
icon: material/chart-timeline-variant
---

# Scaling a Production RAG Pipeline

A demo RAG pipeline is a weekend. A production one is a distributed system with an ingestion pipeline, a serving path, a latency budget, an authorisation surface and an eval harness. This page is what changes between the two.

### What breaks first, in order

1. **Retrieval quality** on real queries that look nothing like your test set.

1. **Freshness** — the corpus changes and the index does not.

1. **Latency** — the pipeline is a serial chain of network calls.

1. **Cost** — every query pays for retrieved tokens, every reindex pays to re-embed.

1. **Multi-tenancy** — one tenant's data leaks, or one tenant's volume degrades everyone.

1. **Silent regression** — nobody notices quality dropped because nothing is measured.

### Ingestion as a real pipeline

The demo version is a script. The production version is an idempotent, incremental, observable pipeline.

```
source → change detection → parse → clean → chunk → embed → upsert → verify
                ↑                                                       │
                └────────────── dead-letter + retry ────────────────────┘
```

**Incremental, not full rebuild.** Hash each source document; re-process only what changed. A nightly full re-embed of a large corpus is both expensive and a long window of staleness.

**Idempotent upserts.** Use a deterministic chunk ID — `hash(source_id, chunk_index, content_hash)` — so a replayed batch overwrites rather than duplicating. Duplicate chunks are the most common cause of "the model keeps repeating itself".

**Deletes must propagate.** A document removed at source that lingers in the index is a correctness *and* compliance problem. Tombstone or hard-delete by `source_id`.

**Parsing is where quality is quietly lost.** PDF tables flattened into word salad, HTML nav bars embedded as content, headers repeated on every page. Budget real time here — bad parsing cannot be fixed downstream by any amount of prompt work.

**Dead-letter everything.** One malformed document should not stall the batch. Queue failures with the error and reprocess after fixing the parser.

### Re-embedding is a migration

Changing embedding model invalidates every vector. Plan it like a schema change:

1. Build the new index alongside the old one.

1. Shadow-read: serve from old, score both against the eval set.

1. Cut over behind a flag when the new index wins.

1. Keep the old index until you are confident, then drop it.

Version the index name with the embedding model (`docs_v3_bge_large`) so the pairing is explicit and a mismatched query path fails loudly instead of returning garbage.

### The serving path and its latency budget

A naive pipeline is a serial chain, and the numbers add up fast:

```
embed query        20-50 ms
vector search      10-50 ms
keyword search     10-30 ms   (parallel with vector)
rerank             50-200 ms
generation        500-3000 ms  ← dominates
```

What actually helps:

- **Parallelise the retrieval fan-out.** Vector and keyword search are independent; run them concurrently.

- **Stream the generation.** It does not reduce total time but it moves perceived latency from seconds to hundreds of milliseconds.

- **Cap the candidate set.** Reranking 200 candidates instead of 50 rarely improves the answer and triples that stage.

- **Cache aggressively** — see below.

- **Make query rewriting conditional.** It costs a full LLM round trip; only do it when the query is a follow-up or is very short.

```python
import asyncio

async def retrieve(query: str, k: int = 50):
    vector_hits, keyword_hits = await asyncio.gather(
        vector_search(query, k=k),
        keyword_search(query, k=k),
    )
    fused = reciprocal_rank_fusion([vector_hits, keyword_hits])
    return await rerank(query, fused[:k])
```

### Caching, at three layers

| Layer | What it caches | Hit rate | Notes |
| --- | --- | --- | --- |
| **Exact-match** | Normalised query → final answer | Low–moderate | Trivial to add; watch personalisation and permissions |
| **Semantic** | Embedding-similar query → answer | Moderate | Threshold too loose and you serve wrong answers |
| **Prompt prefix** | Stable system prompt + instructions | Very high | Provider-side; biggest cost lever |
| **Embedding** | Text → vector | High on reindex | Embeddings are deterministic per model — always cache |

Two cautions worth stating unprompted:

- **Never cache across permission boundaries.** Key any answer cache by tenant *and* by the caller's effective access, or you will serve one user's document to another.

- **Semantic caching needs a conservative threshold and an eval.** "How do I cancel?" and "How do I cancel my *enterprise* contract?" are close in embedding space and have different answers.

### Multi-tenancy and access control

**Filter inside the query, never after it.** Post-filtering retrieves 10 and discards 8, leaving you answering from 2 — and it means unauthorised content briefly existed in your process.

Three isolation models:

| Model | Isolation | Cost | Fits |
| --- | --- | --- | --- |
| **Metadata filter** on a shared index | Logical | Lowest | Many small tenants |
| **Namespace/collection per tenant** | Strong | Moderate | Tens to hundreds of tenants |
| **Index per tenant** | Physical | Highest | Few large or regulated tenants |

Treat retrieval as part of the authorisation surface and test it like one: a per-tenant test that asserts tenant A's queries can never surface tenant B's chunks belongs in CI.

### Scaling the vector store

- **Know your index's rebuild cost.** Graph indexes like HNSW are expensive to build and cheap to query; some cluster-based indexes need training on a representative sample.

- **Tune recall explicitly.** ANN search has knobs (candidate list size, probe count) that trade latency for recall. Measure recall against a brute-force baseline on a sample — do not assume the defaults suit you.

- **Quantise when memory-bound.** Large recall gains per byte, with a small measurable loss; validate it rather than trusting the claim.

- **Shard by tenant or time,** not randomly — so filters prune whole shards.

- **Separate read and write paths.** Bulk upserts during query peak will hurt p99.

### Freshness

Pick the weakest guarantee your product can tolerate, because each step up costs more:

| Need | Approach |
| --- | --- |
| Daily is fine | Scheduled incremental batch |
| Minutes | Change-data-capture / webhooks into a queue |
| Seconds | Streaming ingest + immediate upsert |
| Read-your-writes | Write-through, or query source-of-truth for recent items |

State the guarantee explicitly in your design. "Eventually consistent, typically under five minutes" is an answer; "it updates automatically" is not.

### Cost control

- **Retrieved tokens are the dominant input cost.** Five well-reranked chunks cost a fraction of twenty mediocre ones and usually answer better.

- **Cache prompt prefixes.** Often the largest single saving available.

- **Tier the models** — a small model for query rewriting and routing, a workhorse for answering, a frontier model only for escalated hard cases. See [Choosing the Right Model](choosing-a-model.md).

- **Batch offline embedding** — batch endpoints are frequently discounted substantially.

- **Cap context length per request.** An unbounded retrieved-context budget is an unbounded bill.

### Observability

Log every stage, with IDs, for every request:

```json
{
  "request_id": "req_123",
  "tenant_id": "acme",
  "query": "...",
  "rewritten_query": "...",
  "retrieved_ids": ["doc-3#2", "doc-9#0"],
  "reranked_ids": ["doc-9#0", "doc-3#2"],
  "context_tokens": 2140,
  "model": "workhorse-v2",
  "prompt_version": "rag-answer@7",
  "latency_ms": {"embed": 31, "search": 44, "rerank": 120, "generate": 1830},
  "cache": {"prefix_hit_tokens": 1900},
  "citations": ["doc-9#0"],
  "feedback": null
}
```

The two metrics that catch real regressions:

- **Retrieval hit rate** — how often the known-correct chunk appears in the top-k, measured against your golden set on every deploy.

- **Citation groundedness** — what fraction of factual claims trace to a retrieved chunk. This is your hallucination canary.

Add a thumbs-up/down and *store it with the retrieved IDs*. Negative feedback plus the chunks that produced it is the highest-quality training data for improving retrieval.

### Advanced retrieval, and when it earns its keep

Add these only when the eval says the simple pipeline is the bottleneck:

| Technique | Buys you | Costs |
| --- | --- | --- |
| **Parent-document retrieval** | Small-chunk precision, large-chunk context | Extra store, more tokens |
| **Multi-vector** (summary + raw) | Robustness to query phrasing | More index, more embed cost |
| **Contextual chunk headers** | Big recall win, very cheap | One-off LLM pass at ingest |
| **Graph / entity-linked** | Multi-hop questions | Substantial build complexity |
| **Agentic retrieval** (model queries iteratively) | Handles decomposition naturally | Unbounded latency; needs step caps |
| **Fine-tuned embeddings** | Domain-specific gains | Training data + full re-embed |

The senior instinct: exhaust **chunking, hybrid search and reranking** before reaching for anything on this list. Those three fix the large majority of real retrieval failures, and each of the above adds a moving part.

### Rollout checklist

- Golden eval set built, with retrieval and generation scored separately
- Retrieval hit rate gating deploys in CI
- Per-tenant isolation test in CI
- Incremental, idempotent ingestion with dead-lettering
- Deletes propagate to the index
- Index name versioned with the embedding model
- Prompt-prefix caching verified via usage counters, not assumed
- Answer caches keyed by tenant and permission scope
- Full-stage tracing with prompt and model versions logged
- Latency budget documented per stage, with alerts on p95
- Freshness guarantee written down and tested
- Fallback behaviour defined for "retrieval returned nothing"
