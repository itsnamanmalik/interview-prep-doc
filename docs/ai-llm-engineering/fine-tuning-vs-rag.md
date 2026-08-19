---
icon: material/tune-variant
---

# Fine-Tuning vs RAG vs Prompting

A very common senior interview question, usually phrased as "the model doesn't know about our data — what do you do?" The wrong answer is "fine-tune it". The right answer is an ordering with reasons.

### The escalation ladder

Work down it, and stop as soon as quality is acceptable:

1. **Better prompt** — clearer instructions, examples, structured output. Hours. Reversible.
1. **Retrieval (RAG)** — put the right facts in the context at query time. Days. Reversible.
1. **Tools** — let the model call your systems for live data and actions. Days.
1. **A stronger model** — often cheaper than a week of engineering. Minutes to try.
1. **Fine-tuning** — change the model's behaviour with training data. Weeks. Semi-permanent.
1. **Continued pretraining** — new domain, new vocabulary, large corpus. Months, rarely justified.

Most teams that reach for step 5 have not exhausted steps 1 to 4. The most common actual outcome of "we need to fine-tune" is that a better prompt plus retrieval solved it.

### What each technique is for

| | Prompting | RAG | Fine-tuning |
| --- | --- | --- | --- |
| **Teaches** | What to do now | What is true now | How to behave |
| **Good for** | Format, tone, task framing | Facts, private data, freshness, citations | Consistent style, domain output format, hard-to-specify conventions, smaller-model uplift |
| **Bad for** | Large knowledge | Behaviour change | Facts (see below) |
| **Update cost** | Edit text | Re-index a document | Retrain |
| **Freshness** | Immediate | Minutes | Stale from day one |
| **Citations** | No | Yes, natural | No |
| **Per-request cost** | Baseline | Higher (more input tokens) | Can be lower (shorter prompts, smaller model) |
| **Latency** | Baseline | + retrieval | Can be lower |
| **Reversible** | Instantly | Instantly | Retrain or roll back a version |
| **Access control** | n/a | Per-query filtering | Impossible — weights have no ACL |

### The rule that decides most cases

**Knowledge → retrieval. Behaviour → fine-tuning.**

Fine-tuning for facts fails in a specific and expensive way: the model learns the *style* of your documents and becomes more fluent at inventing things that sound like them. It will not reliably recall a specific number, cannot cite where it came from, cannot be updated when the fact changes, and cannot enforce who is allowed to see it. Every one of those is a hard requirement in most business applications, and retrieval gives you all four.

### When fine-tuning is genuinely right

- **A rigid output format** you cannot get reliably from prompting, especially a domain-specific one.
- **Tone and style** that takes hundreds of words of prompt to approximate and still drifts.
- **A narrow, high-volume, stable task** — classification, extraction, routing — where a fine-tuned small model matches a large model's quality at a fraction of the cost and latency. This is the strongest economic case.
- **Implicit conventions** in your domain that are easier to demonstrate with 500 examples than to describe in prose.
- **Prompt-length reduction** where a 3,000-token instruction block can be baked in — a real cost and latency win at scale.
- **Distillation:** use a frontier model to generate high-quality labelled data, then fine-tune a small model on it. A well-trodden path to cheap production inference.

Note that all of these are behaviour or economics, not knowledge.

### When it is the wrong tool

- The knowledge changes. Anything you would ever need to update.
- You need citations or provenance.
- Different users may see different data — weights cannot be permission-filtered.
- You have fewer than a few hundred good examples.
- You have no eval suite. Fine-tuning without one is unmeasurable, and you will not know whether you improved the target task while degrading everything else.
- The current prompt has not been seriously iterated on.

### They compose

The strongest production setups use both. Fine-tune for the shape of the answer, retrieve for the content of it. A fine-tuned model that reliably produces your citation format and house tone, fed reranked chunks at query time, beats either technique alone.

Also fine-tune *around* the model where it is cheaper: an embedding model fine-tuned on your domain's query-document pairs often improves RAG recall more than anything you can do to the generator.

### How fine-tuning actually works

| Method | What it does | Notes |
| --- | --- | --- |
| **Full fine-tuning** | Updates all weights | Expensive; needs real infrastructure; risks catastrophic forgetting |
| **LoRA / QLoRA** | Trains small low-rank adapter matrices, base weights frozen | The practical default. Tiny artefacts, cheap, swappable per task, near-full quality |
| **Preference tuning (DPO and similar)** | Trains on chosen-versus-rejected pairs | For "prefer this style of answer"; needs preference data |
| **Prompt / prefix tuning** | Learns soft prompt vectors | Cheap, limited, largely superseded by LoRA |

[LoRA](https://arxiv.org/abs/2106.09685) is worth being able to explain: freeze the base weights, train a pair of low-rank matrices per layer whose product is added to the original weights. Because the adapter is small, you can train on modest hardware, store many adapters cheaply, and swap them per tenant or per task.

### Data is the whole job

Fine-tuning quality is dominated by data quality, not hyperparameters.

- **Hundreds to a few thousand examples** is the usual useful range for behaviour tuning with LoRA. Quality beats quantity sharply.
- **The examples must look exactly like production input,** including the messy parts. Train on clean text and serve on OCR output and it will not transfer.
- **Consistency matters more than volume.** Contradictory examples teach the model to be inconsistent. Two annotators with different conventions will produce a model that averages them badly.
- **Hold out a real test set** before you start, and never train on it.
- **Include the negative cases:** the inputs where the right behaviour is to refuse, ask a question, or return empty.
- **Scrub PII.** You cannot unlearn one example from a set of weights, so a deletion request against training data means a retrain.

### Evaluation is mandatory

Before you train, you need the eval suite from [Evaluation & Observability](evaluation-and-observability.md), because fine-tuning has a characteristic failure: it improves the target metric while quietly degrading general capability.

Always measure at least:

1. The target task, on a held-out set.
1. **A general capability set** — instruction following, reasoning, refusals. This is where forgetting shows up.
1. Cost and latency, against the baseline you are trying to beat.

And compare against the honest baselines: the best prompt on the current model, and the same prompt on the next model tier up. A fine-tune that loses to "use a better model and a better prompt" is a maintenance burden with no upside.

### The lifecycle cost people forget

A fine-tuned model is a long-lived dependency:

- It is pinned to a base model. When a better base ships, your fine-tune is now the *old* model, and adopting the new one means retraining and re-evaluating.
- Your data drifts; the model does not.
- You need the training data, the pipeline, and the eval suite maintained and reproducible, not in a notebook on someone's laptop.
- You need a rollback path, which means keeping the previous version deployed.

The right question is not "would fine-tuning improve this?" but **"is this improvement worth owning a trained artefact for the next two years?"** For a narrow high-volume task with real unit economics, often yes. For "the model should know our docs", no.

### What to say in an interview

> I treat it as a ladder: prompt, then retrieve, then tools, then a stronger model, and only then fine-tune. The dividing line is that retrieval teaches the model what is true and fine-tuning teaches it how to behave — so fine-tuning for facts is an anti-pattern, because it cannot be updated, cannot cite, cannot be permission-filtered, and mostly makes the model more fluent at inventing things. Where I would fine-tune is a narrow high-volume task where a LoRA on a small model matches a frontier model at a fraction of the cost, or a rigid output format prompting can't hold. And I'd insist on the eval suite first, including a general-capability set to catch forgetting, plus an honest baseline of best-prompt-on-a-better-model — because a fine-tune that loses to that is just a long-lived maintenance cost.
