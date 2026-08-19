---
icon: material/help-circle-outline
---

# General Questions

### What is FastAPI?

FastAPI is a modern Python web framework for building APIs, built on **Starlette** (ASGI toolkit, handles routing, middleware, WebSockets) and **Pydantic** (data validation and serialisation). Its defining idea is that ordinary Python type hints are the single source of truth: the same annotation drives request parsing, validation, serialisation, editor autocompletion and the generated OpenAPI schema.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

From that one signature FastAPI knows `item_id` comes from the path and must coerce to `int` (returning a 422 if it cannot), that `q` is an optional query parameter, and what the endpoint's schema looks like.

### Where do parameters come from if I do not say?

FastAPI infers the source from the signature, which is a common interview question because the rules are implicit:

- The name appears in the path string → **path parameter**.

- It is a scalar type (`int`, `str`, `bool`, `float`, `UUID`, `datetime`, `Enum`) and not in the path → **query parameter**.

- It is a Pydantic `BaseModel` → **request body** (JSON).

- It is declared with `Form`, `File`, `Header`, `Cookie`, `Depends`, `Body` → whatever that marker says.

Being explicit with `Annotated` is preferred in current FastAPI:

```python
from typing import Annotated
from fastapi import FastAPI, Path, Query

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(ge=1)],
    q: Annotated[str | None, Query(max_length=50)] = None,
):
    return {"item_id": item_id, "q": q}
```

### What is ASGI and why does FastAPI need it?

**WSGI** (Django, Flask) is a synchronous contract: one callable, one request, blocking until a response is returned. It has no way to express a long-lived connection or to yield control while waiting on I/O.

**ASGI** is the asynchronous successor. Its callable is `async` and receives `scope`, `receive` and `send`, which lets a single process interleave thousands of in-flight requests and also model WebSockets and server-sent events — protocols WSGI cannot represent at all.

FastAPI is an ASGI framework, so it is run by an ASGI server (`uvicorn`, `hypercorn`, `granian`), not by `gunicorn` alone.

### How does FastAPI generate API docs automatically?

Because every endpoint is fully described by its type hints, FastAPI can emit an **OpenAPI** schema with no extra work, served at `/openapi.json`, plus two interactive UIs:

- `/docs` — Swagger UI

- `/redoc` — ReDoc

You can rename or disable them:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Orders API",
    version="1.2.0",
    docs_url="/internal/docs",   # None disables it
    redoc_url=None,
    openapi_url="/internal/openapi.json",
)
```

Disabling docs in production is a common hardening step, since the schema documents your whole attack surface.

### What is the difference between `response_model` and a return type annotation?

Both tell FastAPI what shape to serialise, and both **filter** the response — fields not in the model are dropped, which is how you avoid leaking a password hash. The return annotation is the modern form; `response_model` still wins when the two disagree, which is useful when the function genuinely returns something else (an ORM object) than what you want on the wire.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserIn(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    username: str

@app.post("/users", response_model=UserOut)
async def create_user(user: UserIn):
    # Returning the input object is safe: password is not in UserOut,
    # so it never reaches the client.
    return user
```

### How do you return a non-200 status or an error?

Raise `HTTPException` for expected error paths, and set `status_code` on the decorator for the success path:

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()
items: dict[int, str] = {}

@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    item_id = len(items) + 1
    items[item_id] = name
    return {"item_id": item_id}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
            headers={"X-Error": "not-found"},
        )
    return {"item_id": item_id, "name": items[item_id]}
```

For cross-cutting translation of your own exception types, register a handler instead of repeating `try`/`except` in every endpoint:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class OutOfStock(Exception):
    def __init__(self, sku: str):
        self.sku = sku

app = FastAPI()

@app.exception_handler(OutOfStock)
async def out_of_stock_handler(request: Request, exc: OutOfStock):
    return JSONResponse(status_code=409, content={"detail": f"{exc.sku} is out of stock"})
```

### How do you split a large app into modules?

With `APIRouter`, which is FastAPI's equivalent of a Django app's `urls.py` plus views:

```python
from fastapi import APIRouter, FastAPI

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/{order_id}")
async def get_order(order_id: int):
    return {"order_id": order_id}

app = FastAPI()
app.include_router(router)
```

`prefix`, `tags`, `dependencies` and `responses` can all be declared once on the router rather than repeated per endpoint. A router-level `dependencies=[Depends(require_admin)]` is the idiomatic way to protect a whole group of routes.

### What is the request lifecycle?

1. The ASGI server accepts the connection and builds a `scope`.

1. Middleware runs outside-in (`CORSMiddleware`, then yours, and so on).

1. Routing matches a path to an endpoint.

1. Dependencies are resolved, in order, caching repeats within the request.

1. Request data is parsed and validated by Pydantic — failures short-circuit to a **422**.

1. The endpoint runs, on the event loop if `async def`, in a worker thread if plain `def`.

1. The return value is validated and serialised against the response model.

1. `yield` dependencies run their teardown.

1. Middleware unwinds inside-out.

1. `BackgroundTasks` run, after the response has been sent.

### How do you run startup and shutdown code?

Use the `lifespan` context manager. The older `@app.on_event("startup")` and `("shutdown")` decorators are deprecated:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open pools, warm caches, load models.
    app.state.pool = {"connected": True}
    yield
    # Shutdown: close everything you opened.
    app.state.pool.clear()

app = FastAPI(lifespan=lifespan)
```

Everything before `yield` runs once before the app serves traffic; everything after runs on graceful shutdown. Note this is *per worker process*, so with four Uvicorn workers it runs four times — a detail worth stating in an interview, because people put "run migrations" in there and get four concurrent migration attempts.

### What are FastAPI's weaknesses?

Answering this honestly reads as senior:

- **No batteries.** No ORM, admin, migrations, auth backend, template stack or email layer. You assemble them, and you own the integration.

- **Async is easy to misuse.** One blocking call inside `async def` stalls every concurrent request in that worker.

- **Pydantic validation has a cost.** For very large payloads, validation and serialisation can dominate the request; sometimes you need to bypass the response model.

- **Ecosystem is thinner than Django's.** Fewer batteries-included packages for things like admin panels, permission frameworks or CMS features.

- **Fast-moving.** The Pydantic v1 to v2 migration was disruptive, and idiomatic style has shifted (`on_event` to `lifespan`, bare defaults to `Annotated`).
