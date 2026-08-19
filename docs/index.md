# Senior Dev Interview Handbook

Interview preparation notes covering Python, data structures and algorithms,
Django, FastAPI, databases, system design, DevOps and AI/LLM engineering.

## Sections

<div class="grid cards" markdown>

-   :fontawesome-brands-python: **[Python](python/index.md)**

    General questions, advanced language features, OOP, decorators,
    generators, iterators, design patterns, `asyncio`, threading,
    dunder methods, `@property`, pandas and PySpark.

-   :material-graph-outline: **[Data Structures & Algorithms](dsa/index.md)**

    Search algorithms, sorting algorithms, graphs and trees.

-   :simple-django: **[Django](backend-django/index.md)**

    Django internals, Celery, unit testing, Channels/WebSockets,
    Kafka and Nginx.

-   :simple-fastapi: **[FastAPI](fastapi/index.md)**

    Main features, differences from Django, async and concurrency,
    dependency injection, Pydantic, SQLAlchemy, Alembic, auth,
    background tasks and email, testing and deployment.

-   :material-database: **[Database](database/index.md)**

    SQL, ACID, the query planner, performance tuning, read replicas,
    scaling, partitioning and the CAP theorem.

-   :material-sitemap: **[System Design](system-design/index.md)**

    How to structure a system design answer, rate limiting,
    dirty reads and centralised locking.

-   :material-cog-sync: **[DevOps](devops/index.md)**

    Docker, Kubernetes and AWS services.

-   :material-brain: **[AI/LLM Engineering](ai-llm-engineering/index.md)**

    Provider-neutral notes on LLM mechanics, choosing the right model per
    task, prompting, RAG and scaling it, fine-tuning trade-offs, agents,
    LangChain/LangGraph, infrastructure, evaluation and guardrails.

</div>

## Running this site locally

Dependencies are managed with [uv](https://docs.astral.sh/uv/) and pinned in `uv.lock`.

```bash
uv sync          # create .venv from the lockfile
uv run mkdocs serve
```

Then open <http://127.0.0.1:8000>.

To build a static site into `site/`:

```bash
uv run mkdocs build
```
