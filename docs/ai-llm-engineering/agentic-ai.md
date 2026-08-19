---
icon: material/robot-outline
---

# Agentic AI

An **agent** is an LLM in a loop with tools, deciding its own next step until a goal is met. That autonomy is the capability and the risk: a workflow you control fails predictably, an agent fails creatively.

### Workflow vs agent — get this distinction right

| | Workflow | Agent |
| --- | --- | --- |
| Control flow | You write it | The model decides |
| Steps | Known in advance | Discovered at run time |
| Cost / latency | Predictable | Variable, sometimes wildly |
| Debuggability | Straightforward | Requires tracing |
| Fails | Predictably | Creatively |

**Most production "agents" should be workflows.** If you can enumerate the steps, write them as code and call the model for the parts that need judgement. Reach for a real agent only when the task is genuinely open-ended and cannot be specified in advance.

The four questions worth asking before building one:

1. **Complexity** — is the task multi-step and hard to fully specify up front?
1. **Value** — does the outcome justify the extra cost and latency?
1. **Viability** — is the model actually capable at this task type?
1. **Cost of error** — can mistakes be caught and recovered (tests, review, rollback)?

A "no" to any of them means drop a tier: a workflow, or a single well-prompted call.

### The agent loop

Every agent framework is a variation on this:

```python
messages = [{"role": "user", "content": task}]

for step in range(MAX_STEPS):                 # always bound the loop
    response = model.complete(messages, tools=TOOLS)

    if not response.tool_calls:               # model answered instead of acting
        return response.text

    messages.append(response.as_assistant_message())

    results = []
    for call in response.tool_calls:          # execute, possibly in parallel
        try:
            results.append(execute(call))
        except Exception as exc:
            results.append(error_result(call, exc))   # feed errors back, don't crash

    messages.append({"role": "user", "content": results})

raise StepLimitExceeded(step)
```

Four details that separate a toy from production:

- **Bound the loop.** No step cap means an unbounded bill and a possible infinite loop.

- **Return errors to the model rather than raising.** A tool failure is information the agent can act on; a stack trace ends the run.

- **Return all results from one turn together.** Splitting parallel tool results across messages teaches the model to stop parallelising.

- **Append the model's message verbatim.** Dropping or editing tool-call metadata breaks the next turn.

### Common patterns

Roughly in increasing order of autonomy:

| Pattern | Shape | Fits |
| --- | --- | --- |
| **Chaining** | Output of A feeds B feeds C | Decomposable, fixed pipelines |
| **Routing** | Classify, then dispatch to a specialist path | Mixed request types |
| **Parallelisation** | Fan out, then aggregate | Independent subtasks; multi-perspective review |
| **Evaluator–optimiser** | Generate → critique → revise, loop | Quality matters more than latency |
| **Orchestrator–workers** | A planner delegates to sub-agents | Genuinely parallel, independent tracks |
| **ReAct** | Interleave reasoning and acting | The general-purpose default ([paper](https://arxiv.org/abs/2210.03629)) |

**Evaluator–optimiser is underused.** A generate-then-critique loop with a *separate* critic prompt (ideally a fresh context, so it is not anchored on its own reasoning) is the cheapest large quality win available.

### Tool design is the actual work

Agent quality is mostly tool quality. The model can only be as good as the interface you give it.

- **Describe *when* to call it, not just what it does.** "Call this when the user asks about current prices or recent events" outperforms "Gets prices." Trigger conditions in the description measurably improve should-call rate.

- **Keep the surface small.** Beyond roughly 10–20 tools, selection accuracy degrades; group them or use a retrieval step to surface the relevant subset.

- **Make results terse and structured.** Dumping a 50KB API response burns context and buries the signal. Return the fields that matter.

- **Return actionable errors.** `"City 'Xyz' not found. Provide a valid city name."` lets the agent recover; `"KeyError: 'city'"` does not.

- **Make tools idempotent where you can,** because retries happen.

- **Promote an action to its own tool when you need to gate, render, audit or parallelise it.** A generic `run_shell` gives your harness an opaque string; a `send_email` tool gives it a typed call it can require approval for.

```python
{
  "name": "search_orders",
  "description": (
      "Find a customer's orders. Call this whenever the user asks about order "
      "status, delivery, or refunds. Returns at most 10 orders, newest first."
  ),
  "input_schema": {
      "type": "object",
      "properties": {
          "customer_id": {"type": "string", "description": "Internal customer UUID"},
          "status": {"type": "string", "enum": ["open", "shipped", "delivered", "cancelled"]},
      },
      "required": ["customer_id"],
      "additionalProperties": False,
  },
}
```

### Memory

| Kind | Scope | Implementation |
| --- | --- | --- |
| **Working** | Within a run | The message list itself |
| **Episodic** | Across runs | Summaries of prior sessions, retrieved |
| **Semantic** | Domain knowledge | RAG over documentation |
| **Procedural** | Learned methods | Notes the agent writes and re-reads |

The practical version: give the agent a place to write notes and tell it to consult them. Even a plain Markdown file works, and models measurably improve when they can. Curate it — an unbounded, un-pruned memory becomes noise that degrades every future run.

### Multi-agent systems

Multiple agents help when subtasks are genuinely independent and each needs its own context. They hurt when the work is sequential — you pay context re-establishment on every handoff for no parallelism.

- **Orchestrator–worker** is the reliable topology: one planner, N workers, results returned to the planner.

- **Keep delegation one level deep.** Workers that spawn workers become untraceable and unbounded.

- **Cap the fan-out.** Some models delegate eagerly; an explicit ceiling on concurrent sub-agents is the reliable lever.

- **Commit to the delegation.** An orchestrator that re-derives its worker's findings has paid twice for one result.

- **Watch for shared-state collisions** when several agents write the same files.

**Be honest about the cost:** a multi-agent run can be an order of magnitude more expensive than a single call. Justify it with parallelism or context isolation, not novelty.

### Failure modes and their fixes

| Failure | Symptom | Fix |
| --- | --- | --- |
| **Infinite loop** | Same tool, same args, forever | Step cap; detect repeated calls and inject a nudge |
| **Wrong tool** | Reaches for the wrong capability | Better descriptions; fewer tools; few-shot examples |
| **Context exhaustion** | Degrades then fails mid-run | Compaction, stale-result clearing, external memory |
| **Compounding error** | Step 3 built on step 1's mistake | Verification steps; checkpoints |
| **Premature completion** | Claims done with work unfinished | Explicit completion criteria; a verifier |
| **Fabricated progress** | Reports actions it never took | Require claims to cite tool results; audit the trace |
| **Cost blowout** | One run consumes the daily budget | Token budget per run; hard caps; alerting |
| **Destructive action** | Deletes the wrong thing | Approval gates on irreversible tools; dry-run mode |

### Guardrails that actually matter

- **Step and token budgets per run,** enforced in the harness rather than requested in the prompt.

- **Human approval on irreversible actions.** Gate by reversibility: reads run free, writes to external systems require confirmation.

- **Least-privilege credentials.** The agent's key should permit exactly what the task needs.

- **Sandbox code execution.** Container, network egress rules, resource limits, timeouts. Model-authored shell commands are untrusted input.

- **Treat tool output as untrusted.** A retrieved document can contain instructions — see [Safety & Guardrails](safety-and-guardrails.md).

- **Make every run replayable.** Persist the full trace; you cannot debug an agent from a final answer alone.

### Evaluating agents

Final-answer accuracy is not enough — an agent can reach the right answer through an unacceptable path.

- **Task success rate** on a fixed scenario suite.
- **Steps to completion** — a rising trend signals degradation.
- **Tool-call precision** — how often the chosen tool was the right one.
- **Cost and token spend per completed task.**
- **Trajectory review** — did it take a sane path, or thrash and get lucky?
- **Recovery rate** — when a tool failed, did it adapt?

Build a scenario suite with known-good outcomes and run it on every prompt, model or tool change. See [Evaluation & Observability](evaluation-and-observability.md).

### MCP — the tool-integration standard

The [Model Context Protocol](https://modelcontextprotocol.io/) is an open standard for connecting models to tools and data sources. Its value is combinatorial: instead of every application implementing every integration, an MCP **server** exposes a capability once and any MCP **client** can consume it.

Worth knowing that it exists, that it is provider-neutral, and that the security model is the interesting part — an MCP server is code you are granting tool access to, so provenance, permission scoping and the fact that server-supplied tool descriptions enter your prompt all matter.

The protocol details, and how MCP differs from Agent Skills, are on [MCP & Skills](mcp-and-skills.md).

### The interview answer

> Most things called agents should be workflows — if I can enumerate the steps, I write them in code and call the model only for the judgement calls, because a workflow fails predictably and an agent fails creatively. When the task genuinely is open-ended I build the standard loop with a hard step cap, tool errors fed back as observations rather than raised, and every run fully traced so it is replayable. The quality lever is almost always tool design rather than prompt wording: few tools, descriptions that say when to call them, terse structured results, and actionable errors. Guardrails go in the harness, not the prompt — token and step budgets, approval gates on irreversible actions, least-privilege credentials, sandboxed execution. And I evaluate the trajectory, not just the final answer, because an agent that got there by thrashing will stop getting there.
