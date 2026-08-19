---
icon: material/graph
---

# LangGraph

LangGraph models an LLM application as a **state machine**: nodes mutate shared state, edges decide what runs next, and cycles are first-class. It exists because agents are loops, and loops are exactly what a pipeline abstraction handles badly.

### The mental model

| Concept | What it is |
| --- | --- |
| **State** | A typed dict passed to every node; nodes return partial updates that are merged |
| **Node** | A function `(state) -> partial_state`. An LLM call, a tool, plain Python |
| **Edge** | Fixed transition from one node to the next |
| **Conditional edge** | A function reading state and returning the next node's name |
| **Checkpointer** | Persists state per step, enabling pause/resume, time travel and durability |

Everything else — the prebuilt agent, human-in-the-loop, multi-agent — is composed from those five.

### A minimal graph

```python
# pip install langgraph
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    # Annotated with a reducer: new messages are APPENDED, not overwritten.
    messages: Annotated[list, add_messages]

def call_model(state: State) -> dict:
    return {"messages": [model.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("model", call_model)
builder.add_edge(START, "model")
builder.add_edge("model", END)

graph = builder.compile()
graph.invoke({"messages": [("user", "What is a KV cache?")]})
```

**The reducer is the concept to understand.** Without `Annotated[list, add_messages]`, each node's return value *replaces* `messages` and you lose the conversation. With it, updates merge. Getting reducers wrong is the most common LangGraph bug.

### The agent loop as a cycle

This is the shape LangGraph exists for — the conditional edge back to `model` is the loop:

```python
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

def should_continue(state: State) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

builder = StateGraph(State)
builder.add_node("model", call_model)
builder.add_node("tools", ToolNode(TOOLS))

builder.add_edge(START, "model")
builder.add_conditional_edges("model", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "model")          # <-- the cycle

graph = builder.compile()
```

Read it aloud: call the model; if it asked for tools, run them and go back to the model; otherwise stop. That is the entire agent loop, and it is now inspectable, resumable and testable.

### Checkpointing — the feature that matters most

A checkpointer persists state after every step. This is what turns a script into a durable service:

```python
from langgraph.checkpoint.memory import MemorySaver          # dev only
# from langgraph.checkpoint.postgres import PostgresSaver    # production

graph = builder.compile(checkpointer=MemorySaver())

config = {"configurable": {"thread_id": "user-42"}}
graph.invoke({"messages": [("user", "Hi, I'm Alice")]}, config)
graph.invoke({"messages": [("user", "What's my name?")]}, config)  # remembers
```

What checkpointing buys you:

- **Conversation memory for free** — the thread is the history.
- **Crash resume** — a process restart continues from the last step rather than the beginning.
- **Human-in-the-loop** — pause mid-run, wait for input, resume.
- **Time travel** — rewind to an earlier checkpoint and branch.
- **Debuggability** — inspect the exact state at every step of a failed run.

Use an in-memory saver in tests only. Production needs a real backing store, and `thread_id` must be scoped per user or per session — a shared `thread_id` leaks one user's conversation into another's.

### Human-in-the-loop

The reason people adopt LangGraph for anything touching production systems:

```python
from langgraph.types import interrupt, Command

def request_approval(state: State) -> dict:
    decision = interrupt({"action": state["pending_action"]})   # pauses here, persists
    if decision != "approve":
        return {"messages": [("user", "The operator declined that action.")]}
    return {"approved": True}

# Resume later — possibly in a different process, hours later.
graph.invoke(Command(resume="approve"), config)
```

`interrupt` suspends the graph and checkpoints it. Because the state is durable, the approval can arrive from a web request, a Slack action or an email link, minutes or days later. Building that on a plain agent loop means hand-rolling serialisation of the entire loop state.

### Streaming

```python
for event in graph.stream(inputs, config, stream_mode="updates"):
    print(event)          # per-node state updates — the progress feed for a UI

for token, meta in graph.stream(inputs, config, stream_mode="messages"):
    print(token.content, end="")   # token-level, for chat
```

`stream_mode="updates"` is the one people miss: it gives you node-by-node progress, which is what a user watching a long agent run actually needs.

### Multi-agent topologies

Because nodes are arbitrary functions, a node can be another graph:

| Topology | Shape | Fits |
| --- | --- | --- |
| **Supervisor** | A router node dispatches to specialist nodes | Clear task categories |
| **Hierarchical** | Graphs nested as nodes | Large systems with sub-domains |
| **Network** | Any node may hand off to any other | Rare — hard to reason about |
| **Pipeline with review** | Generate → critique → revise cycle | Quality-critical output |

Supervisor is the topology to reach for. Keep delegation one level deep and cap concurrent workers — see [Agentic AI](agentic-ai.md) for why unbounded fan-out gets expensive.

### Production concerns

- **Bound the recursion.** `graph.compile(...)` / `invoke` accept a recursion limit; a cycle with a broken exit condition will otherwise run until it hits your bill.

- **Type the state deliberately.** It is the contract between nodes and the thing you will read when debugging. Keep it small — checkpointed state is serialised on every step.

- **Choose reducers explicitly.** Append-vs-replace per field. This is where subtle bugs live.

- **Scope `thread_id` per user/session,** and treat it as a security boundary.

- **Nodes should be pure and idempotent** where possible — they can be re-executed after a resume.

- **Persist to a real store** and plan checkpoint retention; long conversations accumulate.

### LangGraph vs plain LangChain vs hand-rolled

| | Hand-rolled loop | LangChain / LCEL | LangGraph |
| --- | --- | --- | --- |
| Cycles | Yes, you write them | Awkward | Native |
| Durability / resume | Build it yourself | No | Built in |
| Human-in-the-loop | Substantial work | No | `interrupt` |
| Observability | Your logging | Callback-based | State per step |
| Learning curve | Lowest | Low | Moderate |
| Dependencies | None | Heavy | Heavy |

**When to hand-roll instead:** a short, well-understood loop with no approval gates and no resume requirement is perhaps 40 lines of Python — see the loop in [Agentic AI](agentic-ai.md). Reach for LangGraph when you need **durability, human-in-the-loop, or a topology complex enough that hand-written control flow becomes hard to follow.** "It is the standard for agents" is not a reason; needing checkpointing is.

### The interview answer

> LangGraph models the application as a state machine — typed shared state, nodes that return partial updates merged by reducers, and conditional edges that make cycles first-class. That matters because an agent *is* a cycle, which pipeline abstractions handle badly. The feature I actually adopt it for is checkpointing: persisting state per step gives durable conversations, crash resume, time-travel debugging and genuine human-in-the-loop via `interrupt`, where the graph suspends and can resume from a different process hours later. For a short loop with no approval gates I would hand-roll it in about forty lines; I reach for LangGraph when I need durability or human approval, not because it is fashionable.
