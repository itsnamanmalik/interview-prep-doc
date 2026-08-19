---
icon: material/server-network
---

# AI Infra & Architecture

### The reference architecture

Almost every serious LLM application converges on these layers:

```
Client
  │
Application  ──── prompt registry (versioned)
  │              eval harness / CI gate
LLM gateway  ──── routing · caching · rate limits · budgets · fallback · audit
  │
  ├── hosted provider APIs
  └── self-hosted models (inference server + GPUs)
  │
Data layer   ──── vector store · keyword index · document store · cache
  │
Observability ─── traces · token/cost metrics · eval scores · feedback
```

The two pieces teams skip and later regret are the **gateway** and the **eval harness**. Everything else can be added incrementally; those two are load-bearing.

### The LLM gateway

A single internal choke point for all model traffic. Buy one or build a thin one, but do not let provider SDKs spread through your codebase.

What it earns you:

| Concern | Why it belongs in the gateway |
| --- | --- |
| **Routing** | Send each task to the right tier; A/B models without touching app code |
| **Fallback** | Provider outage or rate limit → retry elsewhere, one place |
| **Caching** | Exact and semantic response caching, shared across services |
| **Budgets** | Per-team/per-tenant spend caps, enforced not requested |
| **Rate limiting** | Protect the shared provider quota from one noisy service |
| **Audit** | Every prompt and completion logged with redaction, for incidents and compliance |
| **Key management** | Provider credentials in one place, rotatable |
| **Portability** | Swapping provider becomes a gateway config change |

Minimum viable version — an interface plus one implementation per provider:

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    cached_input_tokens: int = 0

class LLMClient(Protocol):
    def complete(self, *, prompt_id: str, variables: dict, tier: str) -> Completion: ...
```

Note what the app passes: a **prompt id** and a **tier**, not a prompt string and a model name. That is what keeps model and prompt choices operational rather than hardcoded.

### Hosted API vs self-hosted

| | Hosted API | Self-hosted (open weights) |
| --- | --- | --- |
| Time to first token of value | Hours | Weeks |
| Unit cost at low volume | Low | Very high (idle GPUs) |
| Unit cost at high steady volume | High | Can be much lower |
| Capability ceiling | Highest available | Behind frontier, closing |
| Data residency / air-gap | Contractual | Fully under your control |
| Fine-tuning freedom | Limited | Total |
| Ops burden | Provider's | Yours: GPUs, scaling, upgrades, on-call |
| Latency floor | Network + queue | Can be lower, co-located |

**Default to hosted APIs.** Self-host when you have a concrete reason — data residency, regulatory constraints, high steady volume with a fixed workload, or a fine-tune you cannot do otherwise. "It'll be cheaper" is only true above a volume threshold you should calculate first, and it rarely includes the engineering time.

### Serving open-weight models

**The KV cache, not the weights, usually limits concurrency.** Weights are a fixed cost; the cache grows with `batch_size × sequence_length`. This drives everything about inference-server choice.

Techniques worth being able to name:

- **Continuous batching** — new requests join the batch as others finish, instead of waiting for a whole batch to complete. The single largest throughput win, often several times naive batching.

- **Paged attention** — allocate the KV cache in fixed pages like virtual memory, eliminating fragmentation and allowing much higher concurrency. This is [vLLM](https://github.com/vllm-project/vllm)'s core idea.

- **Prefix caching** — share the KV cache for a common prompt prefix across requests. Enormous for RAG and agents with a fixed system prompt.

- **Quantisation** — INT8/INT4 weights cut memory and raise throughput at some quality cost. Measure the loss on your eval set rather than trusting a benchmark.

- **Speculative decoding** — a small draft model proposes tokens, the large model verifies in parallel. Real latency wins on predictable text.

- **Tensor / pipeline parallelism** — split a model that does not fit on one GPU. Adds interconnect sensitivity; NVLink versus PCIe matters.

Rough capacity arithmetic worth being able to do aloud: weights ≈ `params × bytes_per_param` (2 bytes at FP16, so a 7B model ≈ 14 GB), then add KV cache and activation overhead — usually assume you need meaningfully more than the weight size.

### Latency engineering

| Lever | Effect |
| --- | --- |
| **Stream** | Perceived latency drops to first-token time; total unchanged |
| **Smaller model for the easy path** | Often the biggest real win |
| **Prompt caching** | Cuts prefill, which is TTFT |
| **Parallelise independent calls** | Three sequential 300 ms calls → one 300 ms wait |
| **Shorter outputs** | Decode is sequential — output length is near-linear in latency |
| **Co-locate** | Same region as the provider endpoint or your GPUs |
| **Skip the LLM** | Cache, rules, or a classifier for the trivial cases |

Set an explicit budget per stage and alert on p95, not the mean. LLM latency distributions have long tails, and the mean hides them.

### Reliability

Provider APIs fail. Design for it:

- **Retry with exponential backoff and jitter** on 429 and 5xx. Never retry a 400 — the request is wrong and will stay wrong.

- **Idempotency.** A retried "send the email" tool call must not send two.

- **Circuit breakers.** Stop hammering a provider that is down; fail fast to the fallback.

- **Cross-provider fallback.** The strongest argument for the gateway: a hard outage becomes degraded quality rather than downtime. This requires prompts that work acceptably on both, which is a real constraint to test.

- **Timeouts everywhere,** sized for the worst realistic case. Reasoning models can legitimately take minutes; a 30-second timeout will cut them off mid-answer.

- **Graceful degradation.** Define what the product does when the model is unavailable: cached answer, non-AI path, or an honest error.

### Cost architecture

Instrument first — you cannot optimise a bill you cannot attribute.

```python
# Attribute every call. Without these dimensions, cost review is guesswork.
log_usage(
    request_id=rid, tenant_id=tenant, feature="rag_answer",
    model=c.model, tier="workhorse", prompt_version="rag@7",
    input_tokens=c.input_tokens, cached_input_tokens=c.cached_input_tokens,
    output_tokens=c.output_tokens, cost_usd=price(c),
)
```

Then, in descending order of typical impact:

1. **Right-size the model per task** — see [Choosing the Right Model](choosing-a-model.md).
1. **Prompt-prefix caching** — frequently the single largest saving.
1. **Shorten outputs.** Output tokens cost several times input tokens.
1. **Cache responses** for repeated queries, keyed by tenant and permissions.
1. **Batch offline work** — batch endpoints are commonly discounted heavily.
1. **Trim retrieved context.** Five reranked chunks, not twenty.
1. **Cap per-request and per-run spend** in the gateway, enforced.

### Deployment patterns

- **Synchronous request/response** — chat, autocomplete. Needs streaming and tight timeouts.

- **Async job** — long documents, agent runs. Enqueue, return a job id, notify on completion. The right default for anything that can exceed a few seconds.

- **Batch** — nightly enrichment, bulk classification. Use discounted batch endpoints.

- **Streaming pipeline** — process events as they arrive, with backpressure so a provider slowdown does not build an unbounded queue.

The common mistake is forcing a long agent run into a synchronous HTTP request, then fighting gateway timeouts. If it can take minutes, it is a job.

### Data layer

| Store | Holds | Notes |
| --- | --- | --- |
| **Vector index** | Embeddings + metadata | Sized by vector count × dimensions |
| **Keyword index** | Inverted index (BM25) | Needed for hybrid search |
| **Document store** | Canonical chunk text | Do not treat the vector DB as source of truth |
| **Cache** | Responses, embeddings, prefixes | Redis or similar; key by tenant |
| **Trace store** | Requests, traces, eval results | Grows fast; set retention |

**Keep the source of truth outside the vector store.** You will re-embed — treat the index as a derived artefact you can rebuild.

### Security architecture

- **Prompts and completions are sensitive data.** Redact before logging; set retention; check the provider's data-use and retention terms.

- **Model output is untrusted input.** Never `eval` it, interpolate it into SQL, or execute it unsandboxed.

- **Tool credentials are least-privilege,** scoped to what the task needs.

- **Multi-tenant isolation is enforced at retrieval,** not after — see [Scaling Production RAG](scaling-production-rag.md).

- **Egress control** on any sandbox that runs model-authored code.

See [Safety & Guardrails](safety-and-guardrails.md) for the injection and abuse surface.

### Maturity checklist

| Level | You have |
| --- | --- |
| **Prototype** | Direct SDK calls, prompts in code, no evals |
| **Shipped** | Prompts versioned, structured outputs, tracing, retries |
| **Production** | Gateway, eval suite in CI, cost attribution, caching, fallback |
| **Mature** | Per-task model routing, automated regression gates, feedback loop into evals, budget enforcement, incident playbooks |

Most teams believe they are at Production and are actually at Shipped. The tell is whether a model or prompt change can be **shown** not to have regressed quality — which requires the eval harness, not opinion.
