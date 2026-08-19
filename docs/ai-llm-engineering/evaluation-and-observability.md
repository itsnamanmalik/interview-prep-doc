---
icon: material/chart-line
---

# Evaluation & Observability

The distinguishing question in a senior interview is not "have you used an LLM" but **"how do you know it works, and how would you know if it broke?"** Everything on this page answers that.

### Why evals matter more than in normal software

| Normal software | LLM feature |
| --- | --- |
| Deterministic — same input, same output | Stochastic; correct answers vary in wording |
| Failures throw | Failures return confident prose |
| Unit tests catch regressions | Nothing catches them unless you built it |
| Correctness is binary | Correctness is graded, often by another model |
| Upgrading a dependency is safe-ish | Changing a prompt word or model version can silently regress a whole class of inputs |

Without an eval suite you cannot answer "is this change an improvement?", which means every prompt tweak is a guess and every model upgrade is a leap of faith.

### The golden set

Start here, before any clever tooling.

- **50 to 200 examples** is enough to be useful. Teams stall waiting for 10,000; a hand-built 80 beats a nonexistent 5,000.
- **Draw from real traffic**, not imagination. Your users' phrasing is not yours.
- **Deliberately include the hard cases:** ambiguous queries, out-of-scope questions, adversarial inputs, empty retrieval, multi-hop questions, non-English input if relevant, and the specific failures that caused incidents.
- **Store the expected output or a rubric**, plus a category label so you can score per slice.
- **Version it in git** alongside the prompts. An eval set is source code.

```python
# One record. Keep it boring and diffable.
{
    "id": "refund-policy-eu-001",
    "category": "policy_lookup",
    "input": "can i get my money back after 40 days in germany",
    "must_contain": ["14 days", "statutory"],
    "must_not_contain": ["30 days"],
    "expected_citations": ["policy/eu-returns#section-3"],
    "notes": "Colloquial phrasing; EU-specific rule differs from US default.",
}
```

### Scoring methods, cheapest first

| Method | Use for | Cost | Caveat |
| --- | --- | --- | --- |
| **Exact / regex match** | Classification, extraction, structured fields | Free | Brittle on prose |
| **Schema validation** | Structured outputs | Free | Valid ≠ correct |
| **Deterministic checks** | Citations resolve, no forbidden strings, length caps, JSON parses | Free | Only catches what you specify |
| **Retrieval metrics** | RAG recall@k, MRR, nDCG | Free | Needs labelled relevance |
| **Embedding similarity** | Rough semantic drift | Cheap | Similar ≠ correct; use as a signal, not a gate |
| **LLM-as-judge** | Open-ended quality, faithfulness, tone | Moderate | Needs its own validation, see below |
| **Human review** | Ground truth, calibrating the judge | Expensive | Reserve for a sample and for disputes |

**Use the cheapest method that can detect the failure you care about.** Most teams reach for a judge when a regex would do.

### LLM-as-judge, done properly

It works, and it is the only scalable way to grade open-ended output, but it is a measurement instrument that itself needs calibration.

Rules that make it trustworthy:

1. **Grade one dimension per call.** "Rate this 1 to 10" produces noise. "Is every factual claim supported by the provided context? yes/no plus the unsupported claims" produces signal.
1. **Use a rubric with concrete anchors,** not adjectives. Say what a fail looks like.
1. **Ask for a verdict plus a reason,** and read the reasons during development — that is where you discover your rubric is ambiguous.
1. **Prefer binary or 3-point scales** over 1 to 10. Models cluster around 7.
1. **Pairwise comparison beats absolute scoring** when comparing two versions: "which answer better satisfies the rubric, A or B, or tie?" Randomise position to counter position bias.
1. **Validate the judge against humans** on 50 examples. If judge and human agree less than about 80 percent of the time, fix the rubric before trusting any number it produces.
1. **Beware self-preference.** A model grading its own family's output can be generous. Reduce it with a strict rubric and a different judge model where practical.

```python
JUDGE = """You are grading one answer against one rubric. Be strict.

Question: {question}
Context provided to the assistant: {context}
Answer: {answer}

Rubric: every factual claim in the answer must be supported by the context.
Claims of general knowledge are acceptable only if clearly framed as such.

Return JSON: {{"supported": true|false, "unsupported_claims": [string], "reason": string}}
"""
```

### RAG-specific metrics

Decompose, or you cannot tell a retrieval bug from a generation bug:

| Metric | Question it answers | Failure it isolates |
| --- | --- | --- |
| **Recall@k** | Was the right chunk in the top k? | Retrieval |
| **Precision@k / nDCG** | Is the ranking any good? | Reranking |
| **Context relevance** | Is retrieved context on-topic? | Chunking, embeddings |
| **Faithfulness / groundedness** | Is the answer supported by that context? | Generation, hallucination |
| **Answer relevance** | Does it actually answer the question? | Prompt |
| **Citation accuracy** | Do citations point at the sentences used? | Prompt, post-processing |

If recall@k is high but faithfulness is low, the generator is the problem. If recall@k is low, no prompt work will save you. See [RAG](rag.md) for the fixes.

### Agent-specific metrics

Trajectory matters, not only the final answer:

- **Task completion rate** on a fixed scenario set.
- **Steps to completion** versus a known-good path — creeping upward means the model is flailing.
- **Tool-call validity** — schema-valid arguments, correct tool chosen.
- **Unnecessary tool calls** — the main cost leak.
- **Recovery rate** after an injected tool failure. Test this by deliberately failing a tool.
- **Cost and latency per completed task,** not per call.

### Running evals in CI

This is what turns evals from a science project into engineering.

- **Gate on the diff, not the absolute score.** "No category regresses by more than 2 points" is enforceable; "quality above 90" is not, on day one.
- **Run the cheap deterministic checks on every commit;** run the full judged suite on prompt, model, or retrieval changes, and nightly.
- **Fail the build on schema violations, dropped citations, and safety regressions.** Those are bugs, not taste.
- **Report per-category** so a 3-point average drop that is actually one category collapsing is visible.
- **Pin model versions** in CI so an eval run is reproducible. Auto-upgrading models means your baseline moves under you.
- **Budget the suite.** A 200-example judged suite with a judge call each is a few hundred model calls; keep it under a few minutes and a few dollars or people will skip it.

### Observability in production

Evals tell you about your test set. Production tells you about reality.

**Trace every request** with a single correlation id spanning retrieval, model calls, tool calls, and the response.

```python
# The fields that make an incident debuggable at 2am.
{
    "trace_id": "...", "tenant_id": "...", "user_id_hash": "...",
    "feature": "rag_answer", "prompt_version": "rag@7",
    "model": "...", "model_version": "...", "tier": "workhorse",
    "temperature": 0.2,
    "retrieval": {"query_rewritten": true, "candidates": 40, "returned": 5,
                  "top_score": 0.71, "doc_ids": [...], "latency_ms": 120},
    "tokens": {"input": 4120, "cached_input": 3800, "output": 260},
    "cost_usd": 0.0091,
    "latency_ms": {"ttft": 420, "total": 1830},
    "stop_reason": "end_turn", "tool_calls": 2, "retries": 0,
    "guardrail_flags": [], "feedback": null,
}
```

**Metrics to alert on:**

| Signal | Why it matters |
| --- | --- |
| p95 latency, TTFT separately | Users feel TTFT; timeouts come from total |
| Error and retry rate by provider | Early warning of a provider incident |
| Token usage per request | A creeping input count is a prompt or retrieval bug |
| Cost per day per feature and per tenant | Where the bill comes from |
| Empty-retrieval rate | Ingestion broke, or users moved on to new topics |
| Refusal / guardrail-block rate | Over-blocking is a silent product failure |
| Truncation rate (`max_tokens` hit) | Answers being cut off |
| Thumbs-down and escalation-to-human rate | The only true product signal |

**Watch for drift.** Nothing in the model changed, yet quality fell: usually the input distribution moved (new user segment, new product line, a viral use case) or the corpus went stale. Cluster recent queries periodically and compare against your eval categories; queries with no matching category are your next eval examples.

**Redact before logging.** Prompts and completions carry user data. Redact PII, set retention, and restrict access — a trace store is one of the most sensitive datastores you own.

### Closing the loop

The pipeline that separates teams that improve from teams that plateau:

```
production trace → thumbs-down or flagged → triage
   → add to eval set as a failing case → fix (prompt, retrieval, model, tool)
   → eval suite proves the fix and no regression → ship → observe
```

Every incident should end with a new eval case. That is how the suite stops being your guesses and becomes a record of every way the system has actually failed.

### What to say in an interview

> I treat the eval suite as the deliverable, not an afterthought. Concretely: a versioned golden set of real inputs with per-category labels; cheap deterministic checks — schema, citations resolve, forbidden strings — on every commit; an LLM-judge suite on prompt and model changes, gated on per-category regression rather than an absolute score, with the judge itself calibrated against human labels. In production, one trace id across retrieval and generation, tokens and cost attributed per feature and per tenant, alerts on p95 TTFT, empty-retrieval rate and truncation rate, and every thumbs-down triaged into the eval set. That is what makes a model upgrade a routine change instead of a gamble.
