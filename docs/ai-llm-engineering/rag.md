---
icon: material/file-search-outline
---

# RAG

**Retrieval-Augmented Generation** ([Lewis et al., 2020](https://arxiv.org/abs/2005.11401)) means fetching relevant text at query time and putting it in the prompt, so the model answers from supplied evidence rather than parametric memory.

### Why RAG rather than fine-tuning

| | RAG | Fine-tuning |
| --- | --- | --- |
| Adds new **knowledge** | Yes | Poorly and expensively |
| Teaches new **behaviour/format** | Weakly | Yes |
| Update latency | Seconds — reindex a document | Hours to days — retrain |
| Attribution | Natural (cite the chunk) | None |
| Access control | Enforceable at retrieval time | Baked into weights |
| Cost per query | Higher (more input tokens) | Lower |

The heuristic: **RAG for what the model should know, fine-tuning for how it should behave.** They compose — see [Fine-tuning vs RAG](fine-tuning-vs-rag.md).

### The pipeline

```
INGEST (offline)
  load → clean → chunk → embed → index (+ metadata)

QUERY (online)
  query → [rewrite] → embed → search (vector + keyword)
        → rerank → assemble context → generate → cite
```

Most production failures are in **retrieval**, not generation. When answers are wrong, measure retrieval first: if the right chunk was never fetched, no amount of prompt work will save the answer.

### Chunking

The highest-leverage and most-underestimated decision. Too large and you dilute the embedding and waste tokens; too small and you sever the context needed to make the passage meaningful.

| Strategy | How | Use when |
| --- | --- | --- |
| **Fixed-size + overlap** | N tokens, 10–20% overlap | Default baseline; homogeneous prose |
| **Recursive** | Split on paragraph → sentence → word until it fits | General-purpose; the usual starting point |
| **Structure-aware** | Split on Markdown headings, code blocks, HTML sections | Docs, wikis, source code |
| **Semantic** | Split where embedding similarity drops | Unstructured text where topics drift |
| **Parent-document** | Embed small chunks, return the larger parent | Precision of small + context of large |

Practical defaults: **400–800 tokens with ~15% overlap**, then tune against an eval set. Always store the source, title and section with the chunk — you need them for citation and filtering, and prepending the document title to each chunk measurably improves retrieval on its own.

### Embedding and indexing

Choose the embedding model on the same evidence basis as the generation model — the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) narrows the shortlist, your own retrieval eval decides. Things that actually matter:

- **Dimensionality** drives index memory and query latency, not just quality.

- **Max input length** must exceed your chunk size, or chunks get silently truncated at embed time.

- **Domain fit** beats leaderboard rank — a general model can underperform on legal, medical or code corpora.

- **Switching cost is a full re-embed** of the corpus, so treat the choice as a migration decision.

Vector indexes trade recall for speed:

| Index | Idea | Notes |
| --- | --- | --- |
| **Flat** | Brute-force compare every vector | Exact, fine to ~100k vectors |
| **HNSW** | Navigable small-world graph | The common default; fast, memory-hungry |
| **IVF** | Cluster, then search nearest clusters | Lower memory, needs training |
| **PQ / quantisation** | Compress vectors | Big memory savings, some recall loss |

These are **approximate** nearest-neighbour indexes: they trade a little recall for a lot of latency. Knowing that "ANN is approximate and recall is a tuning parameter" is the point.

### Hybrid search — the single biggest win

Dense vectors capture meaning; keyword search (BM25) captures exact tokens. Each fails where the other succeeds. Query `ERR_4021` and an embedding model returns semantically "error-ish" passages; BM25 returns the exact one.

Combine ranked lists with **Reciprocal Rank Fusion**, which needs no score calibration:

```python
def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Merge ranked ID lists. `k` damps the influence of top ranks."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)

fused = reciprocal_rank_fusion([vector_hits, bm25_hits])
```

### Reranking

Retrieve broadly, then re-score precisely. A **cross-encoder** reads query and document *together*, which is far more accurate than comparing two independent embeddings — and far too slow to run over the whole corpus.

```
vector + BM25  →  top 50 candidates  →  cross-encoder rerank  →  top 5  →  prompt
```

This two-stage shape is the standard production answer: cheap high-recall first stage, expensive high-precision second stage.

### Query transformation

The user's question is often a poor search query.

- **Rewriting** — turn a conversational follow-up into a standalone query. Essential in chat: *"what about the second one?"* retrieves nothing on its own.

- **Decomposition** — split a multi-hop question into sub-queries and retrieve for each.

- **HyDE** — have the model write a *hypothetical answer* and embed that; it often sits closer to the real passage than the question does.

- **Multi-query** — generate several phrasings and fuse the results.

Each adds an LLM call, so each adds latency and cost. Query rewriting in multi-turn chat almost always pays for itself; the others need measuring.

### Metadata filtering and access control

**Do the filtering in the search, not after it.** Post-filtering means asking for 10 results, discarding 8, and answering from 2.

Access control is the security-critical case: a chunk the user may not read must never enter the prompt. Filter by tenant, ACL or role *inside* the query, and treat retrieval as part of your authorisation surface.

### Generation and citation

```python
PROMPT = """Answer the question using only the numbered sources below.
Cite the source id inline for every factual claim, like [3].
If the sources do not contain the answer, say exactly:
"I don't have enough information to answer that."

<sources>
{sources}
</sources>

Question: {question}"""
```

Three things this does: constrains the model to the evidence, makes answers auditable, and gives an explicit escape hatch instead of forcing a guess.

### Evaluating RAG

Score the stages separately or you cannot tell what broke.

**Retrieval** — precision@k, recall@k, MRR, NDCG. Build a small golden set of question → relevant-chunk pairs; a few hundred examples is enough to catch regressions.

**Generation** — faithfulness (is every claim supported by the retrieved context?), answer relevance, and citation correctness. Frameworks like [Ragas](https://docs.ragas.io/en/stable/) automate the common metrics.

The diagnostic table worth memorising:

| Symptom | Likely cause |
| --- | --- |
| Right chunk retrieved, wrong answer | Prompt or model problem |
| Right chunk never retrieved | Chunking, embedding, or missing hybrid search |
| Right chunk retrieved but ranked low | Needs reranking |
| Confidently wrong with no relevant chunk | Missing "I don't know" instruction |
| Correct but unciteable | Metadata not stored at ingest |

### When RAG is the wrong tool

- **Aggregation questions.** "How many tickets mentioned billing last quarter?" is SQL, not similarity search.

- **Whole-document reasoning.** "Summarise this contract" wants the document in context, not five chunks of it.

- **Small corpora.** Under a few hundred pages, put it all in a long-context prompt with caching and skip the infrastructure.

- **Behaviour, tone, format.** That is prompting or fine-tuning.

Recognising that RAG is not the answer is itself a senior signal — see [Scaling Production RAG](scaling-production-rag.md) for what it takes when it *is*.
