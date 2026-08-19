---
icon: material/tune-variant
---

# Choosing the Right Model

The most common architectural mistake in LLM applications is picking one model for everything — usually the largest available — and never revisiting it. Model choice is a **per-task** engineering decision with the same shape as choosing a database: capability floor first, then constraints, then measurement.

Deliberately no model names or prices here. Those change monthly; the method does not.

### The decision, in order

1. **What is the task, precisely?** "Summarise" and "decide whether to refund" have very different error costs.

1. **What is the capability floor?** The cheapest model that passes your eval, not the best model available.

1. **What are the hard constraints?** Latency budget, context length, modality, data residency, self-hosting requirement.

1. **What does being wrong cost?** This sets how much verification you buy, and often the tier.

1. **Measure on your own data.** Public leaderboards narrow the shortlist; only your eval set decides.

Answer 1–4 on paper and the shortlist is usually two or three models. Then step 5 picks.

### Capability tiers

Every provider's lineup, and the open-weight ecosystem, sorts into roughly the same tiers. Reason in tiers and your architecture survives model churn.

| Tier | Characteristics | Fits |
| --- | --- | --- |
| **Frontier / reasoning** | Best multi-step reasoning, long-horizon agentic work; slowest and most expensive; often variable latency | Hard debugging, multi-file code changes, complex planning, ambiguous analysis, LLM-as-judge on hard cases |
| **Mid / workhorse** | Near-frontier on most tasks at a fraction of cost and latency | The default for production traffic: RAG answering, drafting, moderate tool use, code review |
| **Small / fast** | Weak reasoning, strong on well-specified narrow tasks; very cheap, very fast | Classification, routing, extraction, tagging, reranking, guardrail checks, simple rewrites |
| **Specialised** | Embeddings, rerankers, transcription, vision-only, code completion | Use these instead of a chat model wherever one exists |
| **Open-weight** | Any of the above tiers, self-hostable | Data residency, unit-cost at very high volume, fine-tuning, offline/edge |

**The single highest-leverage habit: default to the workhorse tier and justify moving off it in either direction.** Most teams overpay by running frontier models on workhorse tasks, then conclude "LLMs are too expensive".

### Match the task to the tier

| Task | Start at | Why |
| --- | --- | --- |
| Intent classification / routing | Small | Narrow, well-specified, latency-critical |
| Entity extraction to a schema | Small + structured output | The schema does the hard part |
| RAG question answering | Mid | The retrieved context does the reasoning work |
| Summarisation | Small–Mid | Scale with document complexity, not length |
| Content drafting | Mid | Quality is judged by a human anyway |
| Code review / bug finding | Mid–Frontier | Reasoning depth correlates directly with real bugs found |
| Multi-file refactor, migration | Frontier | Long-horizon coherence is exactly the tier's advantage |
| Agentic tool loops | Mid for narrow, Frontier for open-ended | Failure compounds across steps |
| LLM-as-judge | One tier above the model being judged | A judge no stronger than the generator adds noise |
| Semantic search | Embedding model | Never a chat model |
| Reranking | Cross-encoder reranker | Purpose-built, an order of magnitude cheaper |

### Constraints that override tier

**Latency.** Separate two numbers: time to first token (perceived responsiveness) and total completion time. A conversational UI needs low TTFT and can stream; a batch pipeline cares only about throughput and should use batch endpoints where offered, often at a large discount. If your budget is under a second, frontier reasoning models are simply out.

**Context length.** Size for the realistic worst case, not the average, and remember input *and* output share the window. Needing a very long window is often a design smell — retrieval or compaction is usually cheaper and more accurate than a giant prompt.

**Modality.** Vision, audio and document input vary a lot by model. Check the actual limits (resolution caps, page counts, per-image token cost) rather than the marketing claim.

**Deployment.** Data residency, air-gapping, or contractual constraints may force open-weight self-hosting regardless of quality. Know the real cost: GPUs, autoscaling, KV-cache tuning, evaluation and on-call — see [AI Infra & Architecture](ai-infra-and-architecture.md).

### The cost model people get wrong

Three facts that change decisions:

1. **Output tokens cost several times input tokens** — commonly ~5×. Shortening verbose responses usually beats trimming prompts.

1. **Prompt caching changes the arithmetic.** Cached prefix reads typically cost ~10% of normal input. A large stable system prompt reused across requests can dominate your bill or be nearly free depending on whether you got caching right.

1. **A cheaper model that needs retries or a bigger prompt can cost more.** Compare cost per *successfully completed task*, never per token.

```
cost_per_task = (input_tokens × in_rate)
              + (output_tokens × out_rate)
              + (retry_rate × full_request_cost)
              + (escalation_rate × frontier_request_cost)
```

A small model at 80% success that escalates the remaining 20% to a frontier model is frequently cheaper *and* faster at the p50 than sending everything to the frontier model.

### Routing and cascading

Two patterns for using more than one model, both of which read as senior:

**Cascade (escalate on failure).** Try cheap; escalate when the result fails a check.

```python
def answer(question: str) -> str:
    draft = small_model.complete(question)
    if confident(draft):              # schema valid, self-reported confidence, verifier pass
        return draft
    return frontier_model.complete(question)
```

**Router (classify then dispatch).** A tiny model or plain heuristic labels the request and picks the target.

```python
ROUTES = {
    "faq":        "small",
    "code":       "frontier",
    "summarise":  "mid",
}

def route(request: str) -> str:
    intent = classifier.classify(request)      # small model or rules
    return ROUTES.get(intent, "mid")           # workhorse as the safe default
```

Both need the same discipline: **the fallback must be observable.** Log which tier served each request and the escalation rate. A cascade whose escalation rate silently drifts to 90% is a frontier-only system with extra latency.

Do not add routing on day one. Ship on the workhorse tier, find out where it actually fails, then route around *those* cases.

### Evaluating candidates — the part that decides it

Public benchmarks are contaminated, gamed, and measure tasks that are not yours. They are useful only for building a shortlist. The decision comes from your own eval:

1. **Build a golden set** — 50–200 real inputs with known-good outputs, including the hard and weird ones. This is the highest-return artefact in the whole project.

1. **Define grading up front** — exact match, schema validity, a rubric, or an LLM judge with a written rubric. Decide before you look at results.

1. **Run every candidate on identical prompts,** then again with each prompt tuned per model. Prompts are not perfectly portable; a model can look bad purely because the prompt was written for another one.

1. **Record quality, p50/p95 latency, and cost per task together.** A single quality number hides the trade-off you are actually making.

1. **Re-run on every model or prompt change.** This is a regression suite, not a one-off bake-off.

See [Evaluation & Observability](evaluation-and-observability.md) for how to build and run this.

### Keep the choice reversible

Model selection is a decision you will revisit every few months, so build for swapping:

- **Put an interface in front of the model.** One internal `LLMClient` (or an LLM gateway) so provider SDKs are not spread through your codebase.

- **Keep prompts as versioned data,** not string literals inline in business logic.

- **Pin explicit model versions.** Never point production at a floating "latest" alias — output shifts under you with no deploy.

- **Never let a provider-specific parameter leak into domain code.** Reasoning-effort settings, safety toggles and cache directives belong in the adapter.

- **Expect the API surface to move.** Sampling knobs get removed, reasoning controls get added, prefill tricks stop working. Isolating this is exactly what the adapter is for.

Frameworks help here: LangChain's [universal init](https://python.langchain.com/docs/how_to/chat_models_universal_init/) lets one code path target many providers by identifier string, which is convenient for A/B testing candidates.

### Anti-patterns

- **"We use the biggest model" as an architecture.** Expensive, slow, and no evidence it is needed.

- **Choosing from a leaderboard alone.** Benchmark rank does not predict performance on your data.

- **Chasing every new release.** Re-qualifying a model costs real engineering time; only move when your eval shows a win that matters.

- **One model for every task in the system.** Classification and multi-file refactoring should not share a model.

- **Using a chat model for embeddings or reranking.** Purpose-built models are better and dramatically cheaper.

- **No eval set.** Without one you cannot tell an upgrade from a regression, and every model discussion becomes opinion.

- **Ignoring the cheap-model option after prompt work.** A well-prompted small model with a schema often matches a poorly-prompted large one.

### The interview answer

> Model selection is per-task, not per-application. I establish the capability floor by task type, apply hard constraints — latency budget, context length, modality, deployment — and then pick the cheapest tier that clears my eval set rather than the strongest model available. In practice that means a workhorse-tier default, small fast models for classification, extraction and routing, purpose-built embedding and reranker models for retrieval, and frontier reasoning models reserved for long-horizon agentic and hard-debugging work. I compare candidates on cost per *successfully completed task* including retries and escalations, not per token, and I keep the choice reversible behind an internal client interface with pinned model versions and versioned prompts, because this decision gets revisited every few months.
