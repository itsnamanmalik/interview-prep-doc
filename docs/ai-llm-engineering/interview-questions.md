---
icon: material/comment-question
---

# Interview Questions

A checklist for the AI/LLM part of a senior interview. If you can answer these out loud without notes, you are prepared. Each links to the page that covers it.

### Fundamentals

1. Explain what happens between sending a prompt and receiving the first token. → [LLM Basics](llm-basics.md)
1. Why do output tokens cost more and take longer than input tokens?
1. What is the KV cache, and why does it limit how many concurrent requests a GPU can serve? → [AI Infra](ai-infra-and-architecture.md)
1. Difference between prompt caching and the KV cache.
1. What does temperature actually change? Does `temperature=0` give you determinism?
1. Difference between pretraining, supervised fine-tuning, and preference optimisation.
1. What is a reasoning model doing differently, and when is it worth the latency?
1. Why does a model hallucinate, and what does that tell you about how to design around it?
1. What is "lost in the middle" and what does it imply about how you order context?
1. Roughly how many tokens is a page of English text? Why is that number model-specific?

### Model selection

1. You have five features: a chat assistant, a bulk classifier, a code reviewer, a summariser, and an agent that files tickets. How do you choose a model for each? → [Choosing a Model](choosing-a-model.md)
1. How would you decide between a frontier model and a small fast one for a given task?
1. What is a cascade, and when does it backfire?
1. How do you compare two models when the benchmark scores disagree with your team's impressions?
1. How do you calculate cost per completed task rather than cost per call?
1. What has to be true before you would self-host an open-weight model? → [AI Infra](ai-infra-and-architecture.md)
1. A new model version ships. What is your process for adopting it?

### Prompting and context

1. What goes in the system prompt versus the user turn, and why does it matter for caching? → [Prompting & Context](prompting-and-context.md)
1. How do you get reliably structured output, and what still needs validating?
1. When does chain of thought help, and when does it just cost tokens?
1. Your prompt works on 90 percent of inputs. How do you find and fix the other 10 without breaking the 90?
1. How does prompt caching work, and what invalidates it?
1. A conversation grows past the context window. What are your options?
1. How do you version prompts, and why does that matter operationally?

### RAG

1. Walk me through a RAG pipeline end to end. → [RAG](rag.md)
1. How do you choose a chunk size?
1. Why is vector search alone often not enough? What does hybrid search add?
1. Explain reranking. Why not just retrieve fewer chunks with a better embedding model?
1. What is Reciprocal Rank Fusion and why is it used?
1. Your RAG answers are wrong. How do you find out whether it is retrieval or generation? → [Evaluation](evaluation-and-observability.md)
1. How do you enforce per-user document permissions in a vector search? → [Safety](safety-and-guardrails.md)
1. A document is updated. What has to happen in the index? What if it is deleted? → [Scaling RAG](scaling-production-rag.md)
1. You need to change embedding models. How do you roll that out with no downtime?
1. What is your latency budget for a RAG answer, broken down per stage?
1. When is RAG the wrong solution?

### Fine-tuning

1. Our model doesn't know about our internal product. RAG or fine-tuning? → [Fine-Tuning vs RAG](fine-tuning-vs-rag.md)
1. Why is fine-tuning for factual knowledge usually a mistake?
1. Explain LoRA well enough that I know you understand what it trains.
1. How many examples do you need, and what makes them good?
1. What is catastrophic forgetting and how would you detect it?
1. What is the long-term cost of owning a fine-tuned model?

### Agents

1. What is the difference between a workflow and an agent, and which do you reach for first? → [Agentic AI](agentic-ai.md)
1. Write the agent loop on the whiteboard. What are its termination conditions?
1. How do you design a tool so the model uses it correctly?
1. An agent takes 40 steps for a task that needs 4. How do you debug that?
1. How do you stop an agent looping forever or spending unbounded money?
1. Where do you put a human in the loop, and how do you decide?
1. How do you evaluate an agent, given the final answer is not the whole story? → [Evaluation](evaluation-and-observability.md)
1. When is multi-agent worth the complexity, and when is it just latency?

### MCP & Skills

1. What is MCP and what problem does it solve? → [MCP & Skills](mcp-and-skills.md)
1. Name MCP's server primitives and its client primitive. Which client primitives were deprecated, and what replaced them?
1. Which transports does MCP define, and when would you use each?
1. MCP is a stateless protocol. What does that buy you, and what has to travel on every request?
1. What is an Agent Skill, and how does progressive disclosure keep it cheap?
1. Why is a skill's `description` the most important line in the file?
1. When would you write a Skill instead of adding a tool, and vice versa?
1. How do MCP `prompts` and Skills overlap, and how do you choose between them?
1. What is the security exposure of installing a third-party MCP server or Skill?
1. An agent has the right tools but uses them inconsistently. What is your fix?

### Frameworks

1. When does LangChain earn its place, and when would you use the provider SDK directly? → [LangChain](langchain.md)
1. What does LangGraph give you that a `while` loop does not? → [LangGraph](langgraph.md)
1. Explain checkpointing and why `thread_id` is a security boundary.
1. How would you implement human-in-the-loop approval mid-graph?
1. What is a reducer in a graph state, and why do you need one for messages?

### Architecture and operations

1. Draw the architecture of a production LLM feature. → [AI Infra](ai-infra-and-architecture.md)
1. Why put a gateway in front of the models rather than calling SDKs from each service?
1. A provider has an outage. What happens to your product?
1. Your monthly bill tripled. How do you find out why?
1. How would you cut p95 latency on an LLM endpoint by half?
1. What breaks first when traffic goes 10x?
1. How do you handle a request that legitimately takes three minutes?
1. What do you log per request, and what must never be logged?

### Evaluation

1. How do you know a prompt change is an improvement? → [Evaluation](evaluation-and-observability.md)
1. Build me an eval suite for a support-answering feature. Where do the examples come from?
1. What are the failure modes of LLM-as-judge, and how do you mitigate them?
1. What do you gate in CI, and on what threshold?
1. What alerts do you set in production, and what does each catch?
1. How do you detect drift when nothing in your system changed?

### Safety and security

1. What is prompt injection, and what is the difference between direct and indirect? → [Safety](safety-and-guardrails.md)
1. Given that injection has no complete fix, how do you make a successful injection survivable?
1. Why is model output untrusted input?
1. How does an injected instruction exfiltrate data, and how do you block that path?
1. What are your rules for giving an agent a tool with side effects?
1. A user requests deletion of their data. What all has to be deleted?
1. Why is a confidently wrong answer a safety problem and not just a quality problem?

### Design exercises

Expect at least one of these as an open-ended design question. Structure the answer like a system design answer: requirements, then data flow, then evals and guardrails, then cost and latency, then failure modes. Say what you would *not* build.

- **Support assistant** over 50,000 help-centre articles and a ticket history, for 200 enterprise tenants with per-tenant data isolation.
- **Code review bot** that comments on pull requests without becoming noise people mute.
- **Document processing pipeline** turning 10,000 scanned invoices a day into structured records with an accuracy guarantee.
- **Internal search** across Slack, wiki, code, and tickets, respecting each system's permissions.
- **Meeting notes** to summary, decisions, and assigned action items in a tracker.
- **Data analyst assistant** that answers business questions over a warehouse, safely.
- **Migrate a rules engine** with 400 hand-written rules to something LLM-assisted, without a quality cliff on day one.

For each, the interviewer is listening for the same five things: did you choose the right model tier per step and say why; did you reach for retrieval before fine-tuning; did you decide where a human sits; can you say how you would know it works; and did you bound cost, latency, and blast radius.

### Questions worth asking them

Senior interviews are two-way, and these separate teams that have shipped from teams that have demoed:

- What does your eval suite look like, and does it gate deploys?
- How do you decide which model a feature uses, and how often does that change?
- What is your cost per active user, and do you track it per feature?
- What was your worst AI-related incident and what changed afterwards?
- Where do you have a human in the loop today, and what would it take to remove one?
- Who owns prompts — engineering, product, or a mix?
