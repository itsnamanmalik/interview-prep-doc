---
icon: material/brain
---

# AI/LLM Engineering

Engineering notes on building with large language models — deliberately
**provider-neutral**. Concepts, trade-offs and failure modes transfer across
vendors and open-weight models; specific model names, prices and API parameters
change every few months and are the one thing worth looking up fresh.

## Good References:

**Foundations**

- [Attention Is All You Need — the transformer paper.](https://arxiv.org/abs/1706.03762)

- [The Illustrated Transformer — the best visual explanation.](https://jalammar.github.io/illustrated-transformer/)

- [Hugging Face Transformers documentation.](https://huggingface.co/docs/transformers/index)

- [Training language models to follow instructions (InstructGPT / RLHF).](https://arxiv.org/abs/2203.02155)

- [Direct Preference Optimization (DPO).](https://arxiv.org/abs/2305.18290)

**Prompting & reasoning**

- [Prompt Engineering Guide.](https://www.promptingguide.ai/)

- [Chain-of-Thought Prompting.](https://arxiv.org/abs/2201.11903)

- [Lost in the Middle — how position affects long-context recall.](https://arxiv.org/abs/2307.03172)

**RAG**

- [Retrieval-Augmented Generation for Knowledge-Intensive NLP (the original RAG paper).](https://arxiv.org/abs/2005.11401)

- [Retrieval-Augmented Generation for LLMs: A Survey.](https://arxiv.org/abs/2312.10997)

- [HNSW explained — the index most vector databases use.](https://www.pinecone.io/learn/series/faiss/hnsw/)

- [MTEB leaderboard — embedding model benchmarks.](https://huggingface.co/spaces/mteb/leaderboard)

- [Ragas — RAG evaluation framework.](https://docs.ragas.io/en/stable/)

**Agents & tools**

- [Building effective agents.](https://www.anthropic.com/engineering/building-effective-agents)

- [ReAct: Synergizing Reasoning and Acting in Language Models.](https://arxiv.org/abs/2210.03629)

- [Toolformer — models learning to call APIs.](https://arxiv.org/abs/2302.04761)

- [Model Context Protocol (MCP) — open standard for tool/data connections.](https://modelcontextprotocol.io/)

- [MCP architecture overview — participants, layers and primitives.](https://modelcontextprotocol.io/docs/learn/architecture)

- [MCP specification.](https://modelcontextprotocol.io/specification/latest)

- [MCP reference server implementations.](https://github.com/modelcontextprotocol/servers)

- [Agent Skills — the open standard for packaging procedural knowledge.](https://agentskills.io)

- [Agent Skills specification.](https://agentskills.io/specification)

- [LangChain documentation.](https://python.langchain.com/docs/introduction/)

- [LangGraph documentation.](https://langchain-ai.github.io/langgraph/)

**Model selection & comparison**

- [Artificial Analysis — independent quality, price and latency benchmarks across providers.](https://artificialanalysis.ai/)

- [LMArena — human-preference leaderboard.](https://lmarena.ai/)

**Infrastructure**

- [vLLM — high-throughput inference server.](https://github.com/vllm-project/vllm)

- [llama.cpp — CPU/edge inference.](https://github.com/ggml-org/llama.cpp)

- [Qdrant documentation.](https://qdrant.tech/documentation/)

- [LoRA: Low-Rank Adaptation.](https://arxiv.org/abs/2106.09685)

**Safety**

- [OWASP Top 10 for LLM Applications.](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
