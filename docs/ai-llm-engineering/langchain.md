---
icon: material/link-variant
---

# LangChain

LangChain is a framework for composing LLM applications: a provider-agnostic model interface, a composition primitive, and a large library of integrations (vector stores, loaders, tools, retrievers).

Its real value is **not** the abstractions people quote — it is that swapping providers, vector stores or embedding models becomes a one-line change instead of a refactor.

### Provider-agnostic model interface

The most useful thing in the library for a portable codebase — one code path, any provider, selected by identifier string:

```python
# pip install langchain
from langchain.chat_models import init_chat_model

# The identifier is "provider:model". Read it from config, never hardcode.
model = init_chat_model(os.environ["LLM_MODEL"], temperature=0)

response = model.invoke("Summarise the CAP theorem in two sentences.")
print(response.content)
```

This is what makes A/B testing candidate models cheap — see [Choosing the Right Model](choosing-a-model.md). Note that not every parameter is portable: a sampling setting valid on one model is rejected by another, so keep provider-specific knobs in config rather than scattered through code.

### Messages

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

messages = [
    SystemMessage("You are a terse technical assistant."),
    HumanMessage("What is a KV cache?"),
]
response = model.invoke(messages)
```

`SystemMessage`, `HumanMessage`, `AIMessage`, `ToolMessage` map onto every provider's roles. The framework handles the per-provider translation.

### LCEL — the composition primitive

LangChain Expression Language pipes components with `|`. Anything implementing the `Runnable` interface composes, and every chain gets `invoke`, `batch`, `stream` and their async variants for free.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "You answer only from the provided context. If it is absent, say so."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

chain = prompt | model | StrOutputParser()

chain.invoke({"context": "Refunds take 5 business days.", "question": "How long for a refund?"})
chain.batch([{...}, {...}])          # concurrent
for token in chain.stream({...}):    # streaming, no extra code
    print(token, end="")
```

`StrOutputParser` exists because `model.invoke` returns a message object; the parser unwraps `.content`. That one line trips up almost everyone the first time.

### Structured output

The most useful single feature in day-to-day work — bind a schema and get a validated object:

```python
from pydantic import BaseModel, Field

class Ticket(BaseModel):
    category: str = Field(description="billing | technical | account")
    urgency: int = Field(ge=1, le=5)
    needs_human: bool

structured = model.with_structured_output(Ticket)
ticket = structured.invoke("My card was charged twice and I need this fixed today.")
print(ticket.urgency, ticket.category)     # a real Ticket instance
```

Under the hood this uses whichever mechanism the provider supports — native JSON-schema response formats, or a tool call whose arguments are the schema. That indirection is exactly the kind of portability worth having.

### Retrieval

The retriever interface is what makes vector stores swappable:

```python
retriever = vector_store.as_retriever(
    search_type="mmr",                    # maximal marginal relevance: relevance + diversity
    search_kwargs={"k": 5, "fetch_k": 30, "filter": {"tenant_id": "acme"}},
)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

Two things to note for interviews: the `filter` belongs **in** the search call, not applied afterwards (see [Scaling Production RAG](scaling-production-rag.md)), and `mmr` is a cheap way to stop five near-duplicate chunks filling the context.

### Tools and tool calling

```python
from langchain_core.tools import tool

@tool
def get_order_status(order_id: str) -> str:
    """Look up the delivery status of an order.

    Call this whenever the user asks where their order is.
    """
    return lookup(order_id)

model_with_tools = model.bind_tools([get_order_status])
response = model_with_tools.invoke("Where is order A-4021?")
print(response.tool_calls)   # [{'name': ..., 'args': {...}, 'id': ...}]
```

The docstring becomes the tool description, so write it for the model — state *when* to call it, not just what it does.

**`bind_tools` does not execute anything.** It returns the model's *intent*; you run the tool and feed a `ToolMessage` back. For the loop itself, use [LangGraph](langgraph.md) — this is precisely where plain LangChain stops.

### Memory

Chat history is threaded through a runnable rather than hidden in a stateful object:

```python
from langchain_core.runnables.history import RunnableWithMessageHistory

with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,          # (session_id) -> BaseChatMessageHistory
    input_messages_key="question",
    history_messages_key="history",
)

with_history.invoke({"question": "..."}, config={"configurable": {"session_id": "user-42"}})
```

The older `ConversationBufferMemory` / `ConversationChain` classes are legacy. Naming them as current dates your experience — and the modern approach is better anyway, because history is explicit and the session store is yours.

### When LangChain earns its place

**Use it for:**

- **Provider and store portability** — the strongest reason by far.
- **Prototyping speed** — dozens of loaders, splitters, retrievers already written.
- **Structured output and tool binding** across heterogeneous providers.
- **Streaming and batching for free** via the Runnable interface.

**Skip it when:**

- **The app is one prompt and one call.** A provider SDK is fewer moving parts.
- **You need exact control of the request payload.** Abstractions hide provider-specific parameters.
- **Debuggability matters more than convenience.** Deep `|` chains produce difficult stack traces.
- **Dependency weight is a constraint.** It pulls in a lot.

### Honest criticisms, and the balanced answer

- **Abstraction overhead.** Simple things get wrapped in several layers.
- **Churn.** The API has changed substantially across versions; a lot of tutorials are stale.
- **Debuggability.** Errors deep in a chain are hard to localise without tracing.
- **Leaky abstractions.** Provider differences surface anyway, at the worst moment.

The balanced position for an interview: *use LangChain for the integration layer — models, stores, loaders, retrievers — and write the orchestration yourself, or in LangGraph, where you want explicit control.* That splits the difference between "framework for everything" and "reinvent every integration".

### The relationship to LangGraph

| | LangChain | LangGraph |
| --- | --- | --- |
| Shape | Directed pipeline (DAG) | State machine with cycles |
| Fits | Prompt → model → parse | Agent loops, retries, human-in-the-loop |
| State | Passed through the chain | Explicit, typed, checkpointed |
| Loops | Awkward | Native |

Rule of thumb: **LCEL until you need a cycle, then LangGraph.** An agent is a cycle by definition, which is why every non-trivial agent ends up there.
