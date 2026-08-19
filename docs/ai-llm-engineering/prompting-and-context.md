---
icon: material/text-box-edit-outline
---

# Prompting & Context Engineering

Prompt engineering is writing the instruction. **Context engineering** is deciding what occupies the window at all — and at senior level that is the larger, harder problem.

### What actually moves quality

Roughly in order of impact:

1. **Give the model the information it needs.** Most "the model is dumb" reports are missing-context problems.

1. **Be specific about the output.** Format, length, audience, what to leave out.

1. **Show, don't describe.** Two or three good examples beat a paragraph of adjectives.

1. **Structure long prompts.** Delimited sections (XML-ish tags or headings) so boundaries are unambiguous.

1. **Give it room to reason** on hard problems — a reasoning model's depth setting, or an explicit "work through it first" instruction.

1. **Let it refuse.** "If the context doesn't contain the answer, say so" measurably cuts fabrication.

### System prompt vs user turn

The system prompt sets durable role, rules and format. The user turn carries the specific task and data. Two operational reasons the split matters:

- **Caching.** The system prompt is the stable prefix. Interpolating a timestamp or user ID into it destroys cache hits for everything after it.

- **Trust.** Retrieved documents and tool output are *untrusted data*, not instructions. Keep them in the user turn, delimited, and say so explicitly — see [Safety & Guardrails](safety-and-guardrails.md).

```text
SYSTEM
You are a support assistant for an e-commerce API.

<rules>
- Answer only from the provided <context>. If it is insufficient, say so.
- Never invent order IDs, prices, or policy details.
- Cite the source id for every factual claim, like [doc-3].
</rules>

<format>
Two to four sentences, plain prose, no preamble.
</format>

USER
<context>
[doc-3] Refunds are processed within 5 business days.
</context>

Question: How long do refunds take?
```

### Structured outputs beat "please return JSON"

Asking for JSON in prose gets you JSON *most* of the time. Constraining the output gets it every time — the difference between a pipeline and a pipeline plus a retry loop.

Every major provider now offers some form of schema-constrained output (JSON-schema response formats, or a tool/function call whose arguments are the schema). The engineering pattern is the same everywhere: **define the schema once as a typed model, and let the API enforce it.**

```python
from pydantic import BaseModel

class Ticket(BaseModel):
    category: str
    urgency: int          # 1-5
    needs_human: bool
    summary: str

# Pass Ticket.model_json_schema() as the response schema (or as a tool's
# parameter schema). Validate the result back into Ticket before using it —
# schema enforcement guarantees shape, not that the values make sense.
ticket = Ticket.model_validate_json(response_text)
```

Two notes that read as current:

- **Enums and tight types do real work.** `urgency: int` with a range beats `urgency: str` interpreted downstream.

- **The old trick of prefilling the assistant turn** with `{"` to force JSON is deprecated or rejected outright on several current models. Offering it as the answer dates your experience.

### Chain of thought, and when it is already handled

Asking a model to reason before answering improves multi-step accuracy — the [Chain-of-Thought](https://arxiv.org/abs/2201.11903) result. On current reasoning models this is largely built in and **configured** rather than prompted, via a depth/effort control.

Engineering points that matter more than the prompt wording:

- **Output limits bound reasoning plus answer together.** Under-size the limit and the model spends its budget thinking and gets truncated. This is one of the most common production bugs with reasoning models.

- **Higher depth is not free or always better.** On extraction and classification it adds cost and latency for no gain; on ambiguous multi-step work it is the whole point.

- **Reasoning traces are usually summarised, not raw.** Don't build product logic that depends on parsing them.

- **Don't ask for reasoning you throw away.** If you only need the answer, constrain the output; if you need the rationale, ask for it as a field.

### Few-shot examples

Examples are the most reliable steering tool. Rules that hold across models:

- **Cover the edge cases, not the easy path.** The examples exist to disambiguate.

- **Be consistent in format.** Inconsistent examples teach inconsistency.

- **Show the desired output, not the forbidden one.** Positive examples outperform "do not do X".

- **Watch for recency bias** — with imbalanced labels, models drift toward the last example shown. Shuffle or balance.

- **Zero-shot first.** Examples cost tokens on every call; add them only where they measurably help.

### Prompt caching — the highest-leverage cost lever

Most providers can cache a prompt **prefix** so repeated requests skip re-processing it. Typical economics: cached reads around **10%** of normal input cost, writes at a small premium, break-even after two or three requests.

The single invariant, and the only thing you really need to remember: **it is a prefix match, so any byte change invalidates everything after it.**

Put stable content first, volatile content last. The classic invalidators:

| Mistake | Why it kills the cache |
| --- | --- |
| `datetime.now()` in the system prompt | Prefix differs on every request |
| A user or session ID early in the prompt | No sharing across users |
| `json.dumps(d)` without `sort_keys=True` | Non-deterministic key order |
| Adding or reordering a tool mid-conversation | Tool definitions render first — invalidates everything |
| Switching model mid-conversation | Caches are model-scoped |

Verify with whatever cache-hit counter the provider returns in usage metadata. If it reads zero across identical-prefix requests, stop tuning and go find the invalidator. Most providers also have a **minimum cacheable prefix**; below it caching silently does nothing rather than erroring.

### Managing a window that fills up

Long agent runs eventually exceed any context window. The options, and what each costs:

| Technique | What it does | Trade-off |
| --- | --- | --- |
| **Truncation** | Drop oldest turns | Cheap; silently loses early decisions |
| **Summarisation / compaction** | Replace old turns with a summary | Keeps the thread; lossy, costs a call |
| **Selective clearing** | Drop stale tool results, keep structure | Cheap; the detail is gone |
| **Retrieval** | Keep history externally, fetch what's relevant | Scales indefinitely; retrieval can miss |
| **External memory** | Model reads/writes notes to a file or store | Survives restarts; needs curation |

Production agents usually run several at once: compaction for the conversation, retrieval for the corpus, a memory file for durable learnings.

### Prompt versioning

Prompts are production configuration and deserve the same discipline as code:

- **Store them as versioned artefacts,** not string literals buried in business logic.

- **Pin the prompt version alongside the model version** — a prompt is only validated against a specific model.

- **Log which prompt version produced each output.** Without it you cannot debug a regression.

- **Gate changes on the eval set.** A prompt edit is a deploy; treat "it looked better in the playground" as a hypothesis, not a result.

### Common anti-patterns

- **SHOUTING IN CAPS.** On instruction-following models `CRITICAL: YOU MUST ALWAYS` overtriggers — the tool fires when it shouldn't. Plain declaratives work better, and current models generally need *less* forceful prompting than older ones.

- **Negative-only instructions.** "Don't be verbose" is weaker than one short example of the desired length.

- **Stuffing the window because it's big.** See lost-in-the-middle in [Basics of LLMs](llm-basics.md).

- **Prompting instead of engineering.** If the model needs a fact it was never given, no phrasing fixes it.

- **Treating retrieved text as instructions.** That is prompt injection waiting to happen.

- **Tuning prompts by vibes.** Without an eval set, every prompt change is a coin flip you cannot score.
