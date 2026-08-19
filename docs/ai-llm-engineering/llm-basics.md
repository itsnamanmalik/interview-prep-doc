---
icon: material/school-outline
---

# Basics of LLMs

### What is an LLM, mechanically?

A large language model is a neural network trained to predict the next **token** given the tokens before it. Everything else — chat, reasoning, tool use, code generation — is that one objective plus scale, plus post-training.

The dominant architecture is the **decoder-only transformer**. The core operation is self-attention: for each token, the model computes how much every earlier token should influence it, then mixes their representations accordingly. Because attention compares every token to every other, cost grows **quadratically** with sequence length — which is why context windows were historically small and why long-context serving is an engineering problem, not just a config value.

### Tokens, not words

Models operate on sub-word tokens produced by a tokenizer (BPE or similar). Rules of thumb for English prose: roughly **1 token ≈ 4 characters ≈ 0.75 words**. Code, JSON, non-English text and unusual strings tokenize far less efficiently — sometimes 2–3× worse.

Two consequences that matter in interviews:

- **Tokenizers are model-specific.** Estimating cost or context usage with a different model's tokenizer is simply wrong, often by 15–30%. Every serious provider exposes a token-counting endpoint or ships its tokenizer; use the one matching the model you will actually call.

- **Token counts change between model generations,** even within one vendor. A prompt that fits comfortably on one model can overflow on another with an identical advertised context window.

### The context window

The context window is the maximum number of tokens the model can attend to in one request — **input plus output together**. It is working memory, not storage: nothing persists between requests. Chat APIs are stateless, so a "conversation" means resending the whole history every turn, which is why token cost grows quadratically over a long session unless you cache or compact.

Ranges you should expect rather than memorise: small/edge models 8K–32K, mainstream hosted models 128K–200K, current frontier models up to ~1M. Bigger is not automatically better — see *Lost in the middle* below.

### Prefill and decode — why latency behaves oddly

Inference has two distinct phases with different performance characteristics:

- **Prefill** processes the whole prompt in parallel. It is **compute-bound** and determines *time to first token* (TTFT).

- **Decode** generates output one token at a time, each step attending over everything before it. It is **memory-bandwidth-bound** and determines *tokens per second*.

This explains behaviour that otherwise looks strange: doubling the prompt barely changes throughput but noticeably delays the first token, while doubling the output length roughly doubles total latency. It is also why streaming matters so much for perceived speed — you show the first token instead of waiting for the last, even though total time is unchanged.

### The KV cache

During decode, the model would otherwise recompute keys and values for every previous token at every step. Instead it caches them — the **KV cache**. This is the single most important object in LLM serving:

- It makes decode tractable (linear rather than quadratic re-computation).

- It consumes GPU memory proportional to `batch_size × sequence_length`, so it — not the model weights — is usually what limits concurrency.

- Managing it well is the entire value proposition of servers like vLLM. See [AI Infra & Architecture](ai-infra-and-architecture.md).

Note this is **not** the same thing as *prompt caching*, a provider-side feature that reuses a prompt prefix across separate API requests.

### How a model gets built

1. **Pretraining** — next-token prediction over a very large corpus. This is where knowledge and general capability come from, and where essentially all the compute goes.

1. **Supervised fine-tuning (SFT)** — training on curated instruction/response pairs so the model answers rather than merely continues text.

1. **Preference optimisation** — [RLHF](https://arxiv.org/abs/2203.02155), RLAIF, or [DPO](https://arxiv.org/abs/2305.18290): training against preference judgements to make outputs more helpful, harmless and honest.

A **base** model completes text. An **instruct/chat** model has been through steps 2 and 3. Interview trap: the *knowledge cutoff* comes from pretraining, so a model can be newly released and still unaware of last month's events — that is what retrieval and web tools are for.

### Sampling, and why "temperature 0" is not determinism

Each step produces a probability distribution over the vocabulary. Decoding parameters shape how a token is drawn from it:

- **Greedy** takes the highest-probability token.

- **Temperature** flattens (`>1`) or sharpens (`<1`) the distribution.

- **Top-k** samples from the k most likely tokens; **top-p (nucleus)** samples from the smallest set whose cumulative probability exceeds p.

Two things worth saying out loud:

- **Temperature 0 was never a determinism guarantee.** Floating-point non-associativity, variable batching and kernel scheduling all introduce run-to-run variation. Reproducibility needs seeds *and* a fixed serving configuration, and even then providers rarely promise it.

- **Reasoning-oriented models increasingly remove these knobs entirely,** replacing them with a reasoning-depth or "effort" control. Some current models reject `temperature`/`top_p` outright.

So "how do you make output more deterministic?" is now better answered with *constrain the output* — structured outputs, JSON schemas, enums, tool calls — than with *lower the temperature*.

### Reasoning models

A newer class of model spends extra tokens on internal deliberation before answering, exposed as a depth or effort setting rather than a prompt trick. Engineering implications:

- **You pay for reasoning tokens**, usually at output rates, and they often dominate the bill on hard tasks.

- **Output-token limits bound reasoning plus answer together.** Under-size the limit and the model burns its budget thinking and gets truncated mid-answer — a very common production bug.

- **Latency is much less predictable.** A single request can take minutes. Design for streaming, timeouts and async checkpoints.

- **They are not universally better.** On extraction, classification and formatting, a cheap non-reasoning model is usually equal and far faster.

### Embeddings

An embedding maps text to a dense vector such that semantically similar text lands nearby, usually compared with **cosine similarity**. Embeddings are the substrate of retrieval, clustering, deduplication and classification — see [RAG](rag.md).

State these precisely:

- **Embeddings are model-specific.** Vectors from two different models are not comparable at all. Changing embedding model means **re-embedding the entire corpus** — plan for it as a migration, not a config change.

- Typical dimensionality is 384–3072. Higher is not automatically better; it costs memory, index build time and query latency.

- Embeddings capture *semantic* similarity and are weak on exact identifiers — order numbers, SKUs, error codes. That is the argument for hybrid search.

### Lost in the middle

Models attend most reliably to the **start and end** of a long context; material buried in the middle is measurably more likely to be missed ([Liu et al.](https://arxiv.org/abs/2307.03172)). Practical implications:

- Put instructions first, and repeat the critical constraint at the end of a very long prompt.

- Order retrieved passages by relevance and keep the count small — five good chunks beat fifty mediocre ones.

- A million-token window is a capability, not an instruction to fill it. Irrelevant context reduces accuracy *and* costs money.

### Hallucination

A model produces the most plausible continuation, not the true one. It has no separate internal notion of "I know this" versus "this pattern fits". Mitigations, roughly in order of effectiveness:

1. **Ground it** — retrieval, tools, or the source document in-context, with citations.

1. **Constrain it** — structured outputs so the shape cannot drift.

1. **Verify it** — run the code, check the claim against the source, use a second model as a judge.

1. **Give it an exit** — explicitly permit "I don't know" and "the context does not contain this".

The senior framing: hallucination is not a bug to be patched but a property to be **engineered around**, and the engineering effort should scale with the cost of being wrong. A wrong autocomplete suggestion and a wrong dosage calculation do not warrant the same guardrails.

### Terms worth being able to define crisply

| Term | Definition |
| --- | --- |
| Token | Sub-word unit the model actually reads and writes |
| Context window | Max input + output tokens for one request |
| KV cache | Per-request cache of attention keys/values; bounds concurrency |
| Prefill / decode | Parallel prompt processing / sequential token generation |
| TTFT | Time to first token — dominated by prefill |
| Temperature / top-p | Sampling controls (absent on some reasoning models) |
| Embedding | Dense vector used for semantic similarity |
| Knowledge cutoff | End of pretraining data; not the release date |
| SFT / RLHF / DPO | Post-training stages that turn a completer into an assistant |
| Quantisation | Lower-precision weights (INT8/INT4) to cut memory |
| Distillation | Training a small model on a large model's outputs |
| MoE | Mixture of Experts — routes each token to a subset of parameters |
