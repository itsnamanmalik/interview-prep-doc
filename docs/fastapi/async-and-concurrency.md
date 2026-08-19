---
icon: material/lightning-bolt
---

# Async & Concurrency

This is the area senior FastAPI interviews probe hardest, because it is where the framework is easiest to get badly wrong.

### `async def` vs `def` — what actually happens

| | `async def` endpoint | `def` endpoint |
| --- | --- | --- |
| Runs on | The event loop, in the main thread | A worker thread from AnyIO's thread pool |
| Concurrency | Thousands of in-flight requests per process | Bounded by the thread pool (40 threads by default) |
| Blocking call inside | **Stalls every other request in the process** | Only occupies its own thread |
| Use when | Your I/O libraries are async (`httpx`, `asyncpg`, async SQLAlchemy) | Your libraries are sync (`requests`, `psycopg2`, sync ORM) |

The counter-intuitive rule: **if your code blocks, `def` is safer than `async def`.** FastAPI will move it off the loop for you.

```python
import time
import anyio
from fastapi import FastAPI

app = FastAPI()

@app.get("/bad")
async def bad():
    time.sleep(2)          # blocks the event loop: every other request waits
    return {"ok": True}

@app.get("/fine")
def fine():
    time.sleep(2)          # runs in a worker thread, loop stays free
    return {"ok": True}

@app.get("/best")
async def best():
    await anyio.sleep(2)   # yields to the loop, other requests proceed
    return {"ok": True}
```

### Why one blocking call is so damaging

An event loop is a single thread running a queue of ready callbacks. `await` is a yield point: it hands control back so the loop can service someone else. A blocking call never yields, so for its whole duration the loop cannot progress *any* request — including health checks, which is how a single slow endpoint takes a pod out of rotation.

With four workers and one endpoint blocking for two seconds, your effective capacity is four requests every two seconds, no matter how much CPU is idle.

### Offloading blocking work correctly

When you must call a sync library from an `async def` endpoint, push it to a thread:

```python
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool

app = FastAPI()

def legacy_report(customer_id: int) -> dict:
    import time
    time.sleep(0.1)                      # a blocking SDK, or psycopg2, or requests
    return {"customer_id": customer_id}

@app.get("/report/{customer_id}")
async def report(customer_id: int):
    return await run_in_threadpool(legacy_report, customer_id)
```

`anyio.to_thread.run_sync` is the same mechanism if you prefer the AnyIO API directly. Threads solve *blocking I/O*; they do not solve CPU-bound work, because the GIL still serialises Python bytecode.

### CPU-bound work

Neither the loop nor a thread pool helps. Use processes, or better, get the work out of the request path entirely:

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from fastapi import FastAPI

def crunch(n: int) -> int:
    return sum(i * i for i in range(n))

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = ProcessPoolExecutor(max_workers=2)
    yield
    app.state.pool.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/crunch")
async def do_crunch(n: int = 1_000_00):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(app.state.pool, crunch, n)
    return {"result": result}
```

In production, a task queue (Celery, ARQ, Dramatiq) is usually the better answer than a process pool inside the web tier, because it survives deploys and gives you retries.

### Running independent I/O concurrently

Sequential `await`s do not overlap. `asyncio.gather` is what turns three 100 ms calls into one 100 ms wait:

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

async def fetch(name: str) -> str:
    await asyncio.sleep(0.1)
    return name

@app.get("/slow")
async def slow():
    a = await fetch("a")           # 300 ms total
    b = await fetch("b")
    c = await fetch("c")
    return [a, b, c]

@app.get("/fast")
async def fast():
    a, b, c = await asyncio.gather(fetch("a"), fetch("b"), fetch("c"))
    return [a, b, c]               # ~100 ms total
```

Use `asyncio.gather(..., return_exceptions=True)` when one failure should not cancel the siblings, and `asyncio.timeout` (3.11+) to bound the whole group.

### Async generators as dependencies

`yield` dependencies can be async, which is how you get an async session or client with guaranteed cleanup:

```python
from typing import Annotated
from fastapi import Depends, FastAPI
import httpx

app = FastAPI()

async def http_client():
    async with httpx.AsyncClient(timeout=5.0) as client:
        yield client

@app.get("/proxy")
async def proxy(client: Annotated[httpx.AsyncClient, Depends(http_client)]):
    return {"client_is_async": isinstance(client, httpx.AsyncClient)}
```

Creating a fresh `AsyncClient` per request is wasteful in real systems — a single client held on `app.state` for the process lifetime reuses connections, and is what you should say in an interview.

### Classic mistakes to name

- **`requests` inside `async def`.** Blocking HTTP on the loop. Use `httpx.AsyncClient`.

- **`time.sleep` instead of `asyncio.sleep`.** Same problem, more obvious.

- **A sync DB driver in an async endpoint.** `psycopg2` blocks; use `asyncpg` or SQLAlchemy's async engine, or make the endpoint `def`.

- **Forgetting `await`.** The coroutine is never scheduled; you return a coroutine object and FastAPI fails to serialise it. `RuntimeWarning: coroutine ... was never awaited` is the tell.

- **CPU work in `async def`.** Tight loops cannot be interleaved; the loop is captive until they finish.

- **Shared mutable state across requests.** With one loop and many interleaved requests, a module-level dict is shared. `await` points are where another request can observe your half-finished mutation.

- **Assuming `async` means parallel.** One event loop is one thread. Async buys *concurrency* while waiting, never parallel CPU.

### How many workers?

For I/O-bound async services, start at roughly `2 × CPU cores` Uvicorn workers and measure. The classic Gunicorn advice of `2 × cores + 1` was written for blocking WSGI workers and over-provisions for async. Raising the worker count does not fix a blocked event loop; it just gives you more loops to block.
