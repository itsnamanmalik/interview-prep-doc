---
icon: material/rocket-launch-outline
---

# Deployment & Performance

### The serving stack

FastAPI is an ASGI application; something has to run it.

- **Uvicorn** — the standard ASGI server (`uvloop` + `httptools` when available).

- **Gunicorn + `UvicornWorker`** — Gunicorn supervises, Uvicorn serves. Gives you battle-tested process management, graceful reloads and worker recycling.

- **Hypercorn** — HTTP/2 and HTTP/3 support.

- **Granian** — Rust-based, a newer alternative.

```bash
# Development
uvicorn app.main:app --reload

# Production, single supervisor with 4 worker processes
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --graceful-timeout 30 \
  --max-requests 10000 \
  --max-requests-jitter 1000
```

`--max-requests` recycles workers periodically, which papers over slow memory leaks. In Kubernetes the common alternative is one Uvicorn process per container and letting the orchestrator handle replicas and restarts — simpler, and it makes autoscaling metrics honest.

### How many workers?

Start at roughly **`2 × CPU cores`** for an I/O-bound async service and measure. The familiar `2 × cores + 1` is Gunicorn advice for *blocking* WSGI workers, where each can only serve one request at a time; an async worker holds thousands, so you need fewer.

Constraints that actually bound the number:

- **Memory.** Each worker is a full Python process. A large ML model loaded per worker multiplies fast.

- **Database connections.** `workers × pool_size` must stay under the database's `max_connections`. Four workers at `pool_size=10, max_overflow=20` can demand 120 connections — put PgBouncer in front, or shrink the pool.

- **Blocked loops.** More workers do not fix a blocking call; they give you more loops to block.

### Behind a reverse proxy

Terminate TLS at the proxy and forward the real client information:

```bash
uvicorn app.main:app --proxy-headers --forwarded-allow-ips='*'
```

Without `--proxy-headers`, `request.client.host` is your proxy's IP and generated URLs come out as `http://` — which breaks OAuth redirects and rate limiting by IP. Restrict `--forwarded-allow-ips` to the proxy's address in production, since trusting `X-Forwarded-For` from anywhere lets clients spoof their IP.

### A production Dockerfile

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv export --no-dev --format requirements-txt > requirements.txt \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY . .
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```

Multi-stage keeps build toolchains out of the runtime image; the non-root `USER` is table stakes in review.

### Health checks

Separate liveness from readiness, and mean different things by them:

```python
from fastapi import FastAPI, Response, status

app = FastAPI()

@app.get("/livez")
async def livez():
    return {"status": "alive"}            # is the process up? no dependencies

@app.get("/readyz")
async def readyz(response: Response):
    checks = {"db": True, "cache": True}  # actually probe them
    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"checks": checks}
```

Checking the database in the liveness probe is a classic outage amplifier: a brief DB blip makes Kubernetes kill every pod, turning a degradation into a full outage.

### Where the time actually goes

Before tuning the framework, measure. In practice the order is almost always:

1. **Database queries** — missing indexes, N+1 access, `SELECT *` on wide tables.

1. **Sequential external calls** — three 100 ms calls awaited one after another instead of `asyncio.gather`.

1. **Blocking the event loop** — the single worst FastAPI-specific mistake.

1. **Serialisation** — large response payloads through Pydantic.

1. **Framework overhead** — genuinely small, and the last thing worth attacking.

### Practical wins

**Reuse HTTP connections.** One client for the process, not one per request:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=5.0, limits=httpx.Limits(max_connections=100))
    yield
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan)
```

**Use a faster JSON encoder** when payloads are large:

```python
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)   # pip install orjson
```

**Add GZip** for large text responses:

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Stream big payloads** instead of materialising them:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/export")
async def export():
    async def rows():
        for i in range(100_000):
            yield f"{i}\n"
    return StreamingResponse(rows(), media_type="text/plain")
```

**Set timeouts on every outbound call.** A dependency with no timeout turns their outage into yours and exhausts your worker pool.

**Always set a `response_model`** or skip validation deliberately — never let a 50k-item list be validated field by field without knowing you chose that.

### Observability

- **Structured JSON logs** with a request/correlation id propagated through middleware.

- **Prometheus metrics** — `prometheus-fastapi-instrumentator` gives request rate, latency histograms and in-progress counts cheaply.

- **OpenTelemetry tracing**, which matters more here than in a monolith because an async service usually fans out to several dependencies.

- **Event loop lag** as a metric. It is the leading indicator that something is blocking, and nothing else tells you as directly.

### Deployment checklist

- Migrations run as a **separate step**, never in `lifespan` (four workers, four racing migrations).

- `/docs`, `/redoc` and `/openapi.json` disabled or authenticated.

- Secrets from the environment or a secret manager; `pydantic-settings` fails fast at boot if one is missing.

- Graceful shutdown honoured so in-flight requests drain — `--graceful-timeout` above the p99 latency.

- Resource limits set, and a `preStop` hook or `terminationGracePeriodSeconds` aligned with the drain window.

- Load tested with something realistic (`locust`, `k6`) against production-like data volumes, not an empty database.
