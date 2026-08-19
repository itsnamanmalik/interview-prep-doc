# Porting status

Source: [Senior Dev Interview Handbook](https://docs.superhuman.com/d/Senior-Dev-Interview-Handbook_dtUhpLKUpJy)
(`superhuman://docs/tUhpLKUpJy`), 43 pages. Ported on 2026-07-27.

**All 43 source pages are complete.** Titles, section grouping and page ordering
match the source document's page tree. A further 31 pages were written for this
site and are listed below.

### Added after the port (not from the source document)

- **Python → Monkey Patching** (`docs/python/monkey-patching.md`).
- **Python → Pandas** (`docs/python/pandas.md`) and **Python → PySpark**
  (`docs/python/pyspark.md`), both at the end of the Python section.

  Both were written against, and verified on, the versions actually installed
  rather than from memory. Pandas is documented for **pandas 3.0**, where
  Copy-on-Write is mandatory and cannot be disabled, chained assignment raises
  `ChainedAssignmentError` instead of `SettingWithCopyWarning`, text columns
  default to the `str` dtype rather than `object`, and `observed=True` is the
  groupby default for categoricals. All 18 Python blocks were executed and every
  output comment in the page is the real printed value, including the 16.1 MB to
  0.3 MB `category` memory comparison. PySpark is documented for **Spark 3.5**,
  verified on a local session: AQE on by default, `autoBroadcastJoinThreshold`
  10485760b, a `groupBy` shuffle coalesced from the 200 default down to 1
  partition, `coalesce` unable to increase partition count, `BroadcastHashJoin`
  and `ShuffledHashJoin` appearing in real plans, and both `PartitionFilters`
  and `PushedFilters` on a partitioned Parquet read. All 14 of its Python blocks
  execute against a real local session.

  Three corrections came out of running them. `StorageLevel` is importable from
  `pyspark`, not `pyspark.sql`, which the first draft got wrong. `DataFrame.cache()`
  reports `Disk Memory Deserialized 1x Replicated` while the
  `StorageLevel.MEMORY_AND_DISK` constant is the *serialised* variant, so the
  common claim that `cache()` equals `persist(MEMORY_AND_DISK)` is not accurate
  for DataFrames; the page states the real level, `MEMORY_AND_DISK_DESER`. And
  PySpark 3.5's pandas-UDF version check imports `distutils`, removed in Python
  3.12, so `pandas_udf` cannot even be defined on 3.12+ and the verification run
  had to be pinned to Python 3.11; the page carries a warning admonition about
  it.
- **The whole FastAPI section** (`docs/fastapi/`, 13 pages): index, General
  Questions, Main Features, FastAPI vs Django, Async & Concurrency, Dependency
  Injection, Pydantic, SQLAlchemy, Alembic, Authentication & Security, Background
  Tasks & Email, Testing, Deployment & Performance.
- **The whole AI/LLM Engineering section** (`docs/ai-llm-engineering/`, 15 pages,
  placed after DevOps): index, LLM Basics, Choosing the Right Model, Prompting &
  Context, RAG, Scaling Production RAG, Fine-Tuning vs RAG, Agentic AI, MCP &
  Skills, LangChain, LangGraph, AI Infra & Architecture, Evaluation &
  Observability, Safety & Guardrails, Interview Questions.

  This section is deliberately **provider-neutral**: no vendor model tables, no
  vendor pricing, and no provider-specific SDK code, because those change every few
  months and are the one thing worth looking up fresh. Where a model has to be
  named in code it comes from configuration (`init_chat_model(os.environ["LLM_MODEL"])`),
  and capability is described in tiers — frontier/reasoning, mid/workhorse,
  small/fast, specialised, open-weight — rather than by product name. Choosing the
  Right Model exists specifically to cover selecting a model per task: capability
  floor, hard constraints, cost of error, cost-per-completed-task arithmetic,
  cascade and router patterns, and eval-driven selection on your own data. All 35
  external references were checked and return 200 (2026-07-31), and all 25 Python
  blocks parse.

  MCP & Skills was written against the live specifications rather than from
  memory, because both have moved: MCP protocol version `2026-07-28` is stateless
  with per-request `_meta`, uses a mandatory `server/discover`, and **deprecates
  the `sampling` and `logging` client primitives**, leaving `elicitation` as the
  only one. The page states this explicitly, since most 2025-era material still
  lists four. The Agent Skills frontmatter table (`name`, `description`,
  `license`, `compatibility`, `metadata`, `allowed-tools`) and its limits (64 and
  1024 characters, ~100 tokens of metadata per skill, body under ~5,000 tokens)
  come from [the published specification](https://agentskills.io/specification).

Every Python sample in the added pages was executed against the real libraries
rather than reviewed by eye: 55 of the 71 FastAPI blocks run standalone and pass,
and the 16 that cannot (Django-comparison snippets, Alembic revision modules,
blocks needing a live Postgres) are documented as such. The SQLAlchemy examples
were additionally integration-tested against an async SQLite engine, which
confirmed the models, `.scalars()` unwrapping, join tuples, `joinedload` and
`selectinload` behaviour, and that a lazy load in async really does raise
`MissingGreenlet`.

Two corrections came out of that testing and are reflected in the pages:

- `passlib[bcrypt]`, which most FastAPI tutorials still recommend, is broken on
  current installs — passlib (last released 2020) reads `bcrypt.__about__`, removed
  in bcrypt 4.1, and hashing then fails with a spurious 72-byte error. The auth
  page uses `pwdlib` instead and explains the trap.
- `OAuth2PasswordRequestForm` needs `python-multipart` or FastAPI raises at import
  time. The auth page now states this.

The Backend / Django section was also relabelled **Django** in the navigation. Its
directory is still `docs/backend-django/`, so page URLs are unchanged.

| Status | Count |
| --- | --- |
| Ported from the source document | 43 |
| Written for this site | 31 |
| Landing page | 1 |
| **Total pages on the site** | **75** |

## Where the content came from

Three routes were combined, because none alone was sufficient:

1. **Superhuman Docs MCP server** (`content_read`) for 28 pages. This gives the
   cleanest Markdown: real link URLs, code fences with language tags, and
   correct list nesting. The server enforces a **weekly limit of 30 requests**,
   which ran out after 28 pages.
2. **The doc's PDF export** (text layer) for the remaining 15 pages, plus
   everything the MCP route silently dropped (see below).
3. **The PDF's hyperlink annotations**, read with `pypdf`, for every URL. The
   PDF's *text* layer keeps only link text, but PDFs store hyperlinks separately
   as `/Link` annotations carrying the real `/URI`. Extracting those recovered
   all 66 links in the document, including the YouTube URLs behind the "Watch
   Video" buttons, which neither of the first two routes exposed.

Note that the doc's web URL is not a usable route: Superhuman Docs is a
client-rendered app behind authentication, so `WebFetch` returns only the page
shell (a title bar and nothing else), not the content.

## What the PDF export recovered that MCP had dropped

`content_read` renders a page body as Markdown but **discards image URLs, keeping
only alt text**, and the server declares no MCP resource support
(`resources/read` returns "Server does not support resources"), so there was no
second path to the image binaries. The source doc is behind authentication, so
`WebFetch` on the public URL returned a permission wall. The PDF export closed
all of those gaps:

| Asset | Page | How it was handled |
| --- | --- | --- |
| "Treads Vs Multiprocessing" comparison image | `python/threads-and-multiprocessing.md` | Rebuilt as a real Markdown table |
| Embedded Coda table "Select related vs Prefetch Related" | `backend-django/general-questions.md` | Rebuilt as a real Markdown table |
| `dir(int)` terminal screenshot | `python/magic-and-dunder-methods.md` | Transcribed to a code block |
| CAP theorem Venn diagram | `database/cap-theorem.md` | Recreated as SVG |
| Kubernetes architecture diagram | `devops/kubernetes.md` | Recreated as SVG |

Both diagrams are hand-authored SVG rather than output from a diagramming
library, so they render with no external network request and work offline. They
live as standalone files (`docs/assets/images/cap-theorem-venn.svg` and
`kubernetes-architecture.svg`) referenced with normal Markdown image syntax —
originally they were inlined in the page, but they were extracted to files so the
click-to-zoom lightbox picks them up like any other image. Each has a
`figcaption` stating it was recreated.

One image was recovered as a real file: the cover photo on Database → General
Questions, whose URL came through as page metadata from `document_outline`. It is
stored at `docs/assets/images/database-general-questions-cover.jpg`.

## Links

All 66 hyperlinks in the source document are present, verified two ways:

- **Completeness / no fabrication.** The set of source-doc links on the built
  site is compared against the PDF's link annotations: 66 links, 55 unique, an
  exact match in both directions. Nothing from the source is missing and no URL
  was invented.
- **Reachability.** All 57 unique external URLs on the site resolve (checked
  2026-07-31). The 22 YouTube videos were validated through YouTube's oEmbed
  endpoint, which returns the real video title — those titles match the link
  text in the doc, which independently confirms each URL is mapped to the right
  entry.

Two link details worth knowing, both faithful to the source rather than bugs:

- The Query Planner page's "Watch Video" points at *"Secret To Optimizing SQL
  Queries - Understand The SQL Execution Order"*, which is only loosely about
  query planning. That is the video the source links; it was not "corrected".
- The System Design reference *"Why, where, and when should we throttle or rate
  limit?"* now resolves to a video titled *"How to Protect Your Systems with
  Throttling & Rate Limiting - 5 Real-World Use Cases"* — same video, retitled
  on YouTube since the doc was written. The doc's original link text is kept.

## Known omission in the source

**Search Algorithms comparison table.** The page says "Here's a comparison of the
algorithms mentioned based on their time complexities:" and then has an empty
gap. This is missing in the original document too, confirmed against the PDF —
nothing was lost in this port. It is not flagged on the page itself, so the
sentence reads as it does in the source; the per-algorithm complexities are
listed in each section above it.

## Page-by-page

Legend for **Source**: `MCP` = read via the MCP server, `PDF` = taken from the
PDF export.

### Python (`docs/python/`)

| Page | File | Source | Notes |
| --- | --- | --- | --- |
| Python (section index) | `index.md` | MCP | |
| General Questions | `general-questions.md` | MCP | |
| Advanced Python | `advanced-python.md` | MCP | |
| Object Oriented Programming | `object-oriented-programming.md` | MCP | |
| Decorators | `decorators.md` | MCP | |
| Generators | `generators.md` | MCP | |
| Iterators | `iterators.md` | MCP | |
| Monkey Patching | `monkey-patching.md` | **New** | Not in the source document; written for this site |
| Design Patterns | `design-patterns.md` | MCP | |
| Async.IO | `asyncio.md` | MCP | |
| Threads & Multiprocessing | `threads-and-multiprocessing.md` | MCP + PDF | Comparison table rebuilt from PDF |
| Magic & Dunder Methods | `magic-and-dunder-methods.md` | MCP + PDF | `dir(int)` screenshot transcribed |
| Python Property Decorator – @property | `property-decorator.md` | MCP | |
| Pandas | `pandas.md` | **New** | Written for this site; verified against pandas 3.0 |
| PySpark | `pyspark.md` | **New** | Written for this site; verified on a local Spark 3.5 session |

### Data Structures & Algorithms (`docs/dsa/`)

| Page | File | Source | Notes |
| --- | --- | --- | --- |
| Datastructure & Algorithm (section index) | `index.md` | MCP | |
| Search Algorithms | `search-algorithms.md` | MCP | Table absent in source |
| Sorting Algorithms | `sorting-algorithms.md` | MCP | |
| Graphs | `graphs.md` | MCP | |
| Trees | `trees.md` | MCP | |

### Django (`docs/backend-django/`)

| Page | File | Source | Notes |
| --- | --- | --- | --- |
| Django (section index) | `index.md` | MCP | |
| General Questions | `general-questions.md` | MCP + PDF | Embedded table rebuilt from PDF |
| Celery | `celery.md` | MCP | |
| Unit Testing | `unit-testing.md` | MCP | |
| Websockets / Channels (Django) | `websockets-channels.md` | MCP | |
| Message Queue (Kafka) | `message-queue-kafka.md` | MCP | |
| Nginx | `nginx.md` | MCP | |

### Database (`docs/database/`)

| Page | File | Source | Source page ID | Notes |
| --- | --- | --- | --- | --- |
| Database (section index) | `index.md` | MCP | — | |
| General Questions | `general-questions.md` | MCP | — | Cover photo recovered |
| ACID Properties | `acid-properties.md` | MCP | — | |
| Query Planner | `query-planner.md` | MCP | — | |
| SQL Queries Questions | `sql-queries-questions.md` | PDF | `pages/section-fo5HNVEYWC` | |
| Monitor & Improve Database performance | `monitor-and-improve-performance.md` | PDF | `pages/section-N_fQy5sumd` | |
| Read Replica DB | `read-replica-db.md` | PDF | `pages/section-q4Zz76TMLW` | |
| Scaling Database | `scaling-database.md` | PDF | `pages/section-JTFAjVzfn-` | |
| Database Partitioning | `database-partitioning.md` | PDF | `pages/section-23UnKHnzEi` | |
| CAP Theorem | `cap-theorem.md` | PDF | `pages/section-C3LGe6eTXz` | Venn diagram recreated as SVG |

### System Design (`docs/system-design/`)

| Page | File | Source | Source page ID | Notes |
| --- | --- | --- | --- | --- |
| System Design (section index) | `index.md` | PDF | `pages/section-Qu1Six1FyQ` | |
| How to answer Interview Questions | `how-to-answer-interview-questions.md` | PDF | `pages/section-h3ympp-8qF` | |
| Design a Rate Limiter | `design-a-rate-limiter.md` | PDF | `pages/section-tqYdTIcgQj` | |
| Dirty Read | `dirty-read.md` | PDF | `pages/section-RpXgkLWvoq` | |
| Centralised Locking | `centralised-locking.md` | PDF | `pages/section-S3mhOjd_JI` | |

### DevOps (`docs/devops/`)

| Page | File | Source | Source page ID | Notes |
| --- | --- | --- | --- | --- |
| DevOps (section index) | `index.md` | PDF | `pages/section-5zSLE_dr4J` | |
| Docker | `docker.md` | PDF | `pages/section-rihZs54G1Q` | |
| Kubernetes | `kubernetes.md` | PDF | `pages/section-KttU0VaEBL` | Architecture diagram recreated as SVG |
| AWS Tools | `aws-tools.md` | PDF | `pages/section-tAmUb2VXpH` | |

### AI/LLM Engineering (`docs/ai-llm-engineering/`)

Not in the source document — written for this site, provider-neutral.

| Page | File | Covers |
| --- | --- | --- |
| AI/LLM Engineering (section index) | `index.md` | Grouped neutral references: foundations, prompting, RAG, agents, model comparison, infrastructure, safety |
| LLM Basics | `llm-basics.md` | Decoder-only transformers, tokens, context window, prefill vs decode, KV cache, training stages, sampling, reasoning models, embeddings, hallucination |
| Choosing the Right Model | `choosing-a-model.md` | Capability tiers, task-to-tier mapping, constraints, cost-per-completed-task, cascade and router patterns, eval-driven selection |
| Prompting & Context | `prompting-and-context.md` | System vs user turn, structured outputs, chain of thought, few-shot, prompt caching, context management, versioning |
| RAG | `rag.md` | RAG vs fine-tuning, chunking, embedding selection, index types, hybrid search + RRF, reranking, query transformation, citations, diagnostics |
| Scaling Production RAG | `scaling-production-rag.md` | Idempotent incremental ingestion, re-embedding as a migration, latency budget, caching layers, multi-tenancy, freshness, cost, observability |
| Fine-Tuning vs RAG | `fine-tuning-vs-rag.md` | The escalation ladder, knowledge vs behaviour, when fine-tuning is right, LoRA, data quality, lifecycle cost |
| Agentic AI | `agentic-ai.md` | Workflow vs agent, the agent loop, patterns, tool design, memory, multi-agent, failure modes, guardrails, MCP |
| MCP & Skills | `mcp-and-skills.md` | MCP participants/layers/primitives/transports, statelessness and discovery, Agent Skills format and progressive disclosure, side-by-side comparison, how they compose |
| LangChain | `langchain.md` | Provider-agnostic init, LCEL, structured output, retrievers, tools, memory, when it earns its place, honest criticisms |
| LangGraph | `langgraph.md` | `StateGraph`, reducers, cycles, checkpointing, `interrupt` for human-in-the-loop, streaming, topologies |
| AI Infra & Architecture | `ai-infra-and-architecture.md` | Reference architecture, the LLM gateway, hosted vs self-hosted, serving open weights, latency, reliability, cost, deployment patterns, maturity model |
| Evaluation & Observability | `evaluation-and-observability.md` | Golden sets, scoring methods, LLM-as-judge done properly, RAG and agent metrics, evals in CI, tracing, drift |
| Safety & Guardrails | `safety-and-guardrails.md` | Threat model, prompt injection, input/output guardrails, tenancy isolation, agent safety, privacy, the layered picture |
| Interview Questions | `interview-questions.md` | ~70 questions by topic, seven design exercises, questions to ask the interviewer |

## Faithfulness notes

A few oddities in the source were kept rather than silently corrected, so the
port stays a port and not a rewrite:

- Typos in the original are preserved verbatim: "Betweet" (Database → General
  Questions), "Treads Vs Multiprocessing", "preformance"/"archirecture"/
  "Syncronous" (Scaling Database), the stray `=` in the `CHANNEL_LAYERS` snippet
  (Websockets / Channels), the truncated "ASGI (" heading and the leading "n the
  Kafka ecosystem" (Message Queue).
- The trailing bare word `fixtures` at the end of the Unit Testing page is in the
  source and is kept.
- Complexity notation that came through MCP mangled (`O(n2)O(n^2)O(n2)`) was
  normalised to a single readable form in inline code, e.g. `O(n^2)`.
