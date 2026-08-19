---
icon: material/needle
---

# Dependency Injection

FastAPI's DI system is one of its most distinctive features and a reliable interview topic. A dependency is just a callable whose result FastAPI computes and passes in.

### The basics

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

def pagination(skip: int = 0, limit: int = 20) -> dict[str, int]:
    return {"skip": skip, "limit": min(limit, 100)}

@app.get("/items")
async def list_items(page: Annotated[dict, Depends(pagination)]):
    return page
```

The dependency's own parameters are analysed too, so `skip` and `limit` become documented query parameters on every endpoint that uses it. This is the key idea: dependencies compose *and* contribute to the OpenAPI schema.

`Annotated[dict, Depends(pagination)]` is today's recommended style over the older `page: dict = Depends(pagination)`, because the annotation carries the marker instead of the default value — which means the same dependency is reusable outside FastAPI and does not break non-default argument ordering.

### Setup and teardown with `yield`

Anything needing cleanup — a DB session, a file handle, a lock — uses a generator dependency. Code after `yield` runs once the response is finished.

```python
from typing import Annotated, Iterator
from fastapi import Depends, FastAPI

app = FastAPI()
events: list[str] = []

def unit_of_work() -> Iterator[str]:
    events.append("open")
    try:
        yield "session"
        events.append("commit")
    except Exception:
        events.append("rollback")
        raise
    finally:
        events.append("close")

@app.get("/work")
async def work(session: Annotated[str, Depends(unit_of_work)]):
    return {"session": session}
```

The `try`/`except`/`finally` shape matters: without it a failing request leaks the resource or commits a broken transaction.

### Sub-dependencies

Dependencies can depend on dependencies, and FastAPI resolves the graph:

```python
from typing import Annotated
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

def get_token(x_token: Annotated[str | None, Header()] = None) -> str:
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing X-Token")
    return x_token

def get_current_user(token: Annotated[str, Depends(get_token)]) -> dict:
    if token != "letmein":
        raise HTTPException(status_code=401, detail="Bad token")
    return {"username": "alice", "is_admin": True}

def require_admin(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin only")
    return user

@app.get("/admin")
async def admin_area(user: Annotated[dict, Depends(require_admin)]):
    return {"welcome": user["username"]}
```

### Caching within a request

By default a dependency used more than once in a single request is computed **once** and reused. This is why the chain above does not re-parse the token three times.

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()
calls: list[int] = []

def expensive() -> int:
    calls.append(1)
    return len(calls)

def a(v: Annotated[int, Depends(expensive)]) -> int: return v
def b(v: Annotated[int, Depends(expensive)]) -> int: return v

@app.get("/cached")
async def cached(x: Annotated[int, Depends(a)], y: Annotated[int, Depends(b)]):
    return {"x": x, "y": y, "times_called": len(calls)}
```

`expensive` runs once per request, so `x == y`. Opt out with `Depends(expensive, use_cache=False)` when you genuinely need a fresh value each time. The cache is per request, never across requests — a frequent misconception worth correcting out loud.

### Dependencies that return nothing

When you only want the side effect (an auth check, rate limiting, audit logging), attach it without binding a parameter:

```python
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException

def verify_key(x_api_key: str = Header()) -> None:
    if x_api_key != "secret":
        raise HTTPException(status_code=401, detail="Bad API key")

app = FastAPI()

# Whole-app
# app = FastAPI(dependencies=[Depends(verify_key)])

# Whole-router
router = APIRouter(prefix="/secure", dependencies=[Depends(verify_key)])

@router.get("/ping")
async def ping():
    return {"pong": True}

# Single endpoint
@app.get("/one", dependencies=[Depends(verify_key)])
async def one():
    return {"ok": True}

app.include_router(router)
```

Router-level `dependencies` is the idiomatic way to protect a group of routes — the FastAPI equivalent of a Django permission mixin applied across a view module.

### Classes as dependencies

A class with `__init__` is a callable, so it works directly — handy for parameterising:

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

class RateLimit:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute

    def __call__(self) -> dict[str, int]:
        return {"limit": self.per_minute}

strict = RateLimit(per_minute=10)

@app.get("/limited")
async def limited(limit: Annotated[dict, Depends(strict)]):
    return limit
```

### Overriding dependencies in tests

This is the payoff, and the thing to lead with if asked "why bother with DI?". `app.dependency_overrides` swaps any dependency for a stub with no monkey patching:

```python
from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

def get_settings() -> dict:
    return {"env": "production"}

@app.get("/env")
async def env(settings: Annotated[dict, Depends(get_settings)]):
    return settings

client = TestClient(app)
assert client.get("/env").json() == {"env": "production"}

app.dependency_overrides[get_settings] = lambda: {"env": "test"}
assert client.get("/env").json() == {"env": "test"}

app.dependency_overrides.clear()      # always clean up
assert client.get("/env").json() == {"env": "production"}
```

Because the override is keyed on the function object, the real database, the real HTTP client and the real clock can all be replaced from a fixture — no import-order games, no patch targets to get wrong.

### Design notes worth mentioning

- **Keep dependencies cheap.** They run on every request in the chain. Expensive singletons belong in `lifespan` on `app.state`, injected by a trivial dependency.

- **Dependencies are the seam for testing.** If something is hard to fake, it probably should have been a dependency.

- **They are not middleware.** Middleware wraps every request including 404s and static files, and cannot contribute to the schema. Dependencies are per route, typed, documented, and can short-circuit with a proper HTTP error.

- **Watch the graph depth.** A five-level chain resolved on every request is real overhead and hard to reason about; flatten it.
