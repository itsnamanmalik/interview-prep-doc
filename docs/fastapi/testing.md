---
icon: material/test-tube
---

# Testing

### `TestClient` basics

`TestClient` wraps `httpx` and drives the ASGI app in-process — no server, no network, no port:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

It is synchronous even against `async def` endpoints — it runs its own event loop internally. `pip install "fastapi[standard]"` or `httpx` is required.

### Lifespan does not run unless you ask

A frequent bug: `TestClient(app)` used directly does **not** execute `lifespan`, so anything set up there (`app.state.pool`) is missing. Use it as a context manager:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.testclient import TestClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = True
    yield
    app.state.ready = False

app = FastAPI(lifespan=lifespan)

@app.get("/ready")
async def ready():
    return {"ready": getattr(app.state, "ready", False)}

def test_without_lifespan():
    assert TestClient(app).get("/ready").json() == {"ready": False}

def test_with_lifespan():
    with TestClient(app) as client:          # startup runs here
        assert client.get("/ready").json() == {"ready": True}
```

### Overriding dependencies

The main reason DI is worth the ceremony — swap the database, the clock or the payment gateway with no patching:

```python
from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

def get_db() -> str:
    return "production-db"

@app.get("/where")
async def where(db: Annotated[str, Depends(get_db)]):
    return {"db": db}

def test_override():
    app.dependency_overrides[get_db] = lambda: "test-db"
    try:
        assert TestClient(app).get("/where").json() == {"db": "test-db"}
    finally:
        app.dependency_overrides.clear()     # leaking this poisons later tests
```

In pytest, make the cleanup automatic:

```python
import pytest

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    app.dependency_overrides[get_db] = lambda: "test-db"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

### Testing async code directly

When you need to await application code (a repository, a service) rather than go through HTTP, use `httpx.AsyncClient` with an ASGI transport:

```python
# pip install pytest-asyncio httpx
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/where")
    assert response.status_code == 200
```

Set `asyncio_mode = "auto"` in your pytest config to avoid decorating every test.

### Database strategy

Three approaches, in increasing order of fidelity:

1. **Override the session dependency with SQLite in-memory.** Fastest, but SQLite differs from Postgres on JSON, arrays, `ON CONFLICT` and constraint timing — green tests can hide real breakage.

2. **A real Postgres per test run** (docker-compose or `testcontainers`), each test wrapped in a transaction that is rolled back afterwards. The usual sweet spot.

3. **Migrate a fresh schema per session** with `alembic upgrade head`, which also proves your migrations actually apply.

Rollback-per-test in outline:

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/test")
    connection = await engine.connect()
    transaction = await connection.begin()
    maker = async_sessionmaker(bind=connection, expire_on_commit=False)
    async with maker() as s:
        yield s
    await transaction.rollback()        # undo everything the test did
    await connection.close()
    await engine.dispose()
```

Binding the sessionmaker to an open connection rather than the engine is what makes the outer rollback able to discard the test's commits.

### Testing validation and errors

Assert on the 422 shape, not just the status — it is part of your API contract:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI()

class Item(BaseModel):
    name: str = Field(min_length=2)
    qty: int = Field(ge=1)

@app.post("/items")
async def create(item: Item):
    return item

def test_validation_error():
    response = TestClient(app).post("/items", json={"name": "x", "qty": 0})
    assert response.status_code == 422
    locations = {tuple(e["loc"]) for e in response.json()["detail"]}
    assert ("body", "name") in locations
    assert ("body", "qty") in locations
```

### Testing WebSockets and background tasks

```python
from fastapi import BackgroundTasks, FastAPI, WebSocket
from fastapi.testclient import TestClient

app = FastAPI()
log: list[str] = []

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("hello")

@app.post("/task")
async def make_task(tasks: BackgroundTasks):
    tasks.add_task(log.append, "ran")
    return {"queued": True}

def test_websocket():
    with TestClient(app).websocket_connect("/ws") as ws_client:
        assert ws_client.receive_text() == "hello"

def test_background_task_runs():
    TestClient(app).post("/task")
    assert log == ["ran"]          # TestClient waits for tasks to finish
```

That last behaviour is a useful detail: `TestClient` runs background tasks before returning, so they are synchronously assertable — unlike production, where they race with the response.

### Mocking outbound HTTP

Do not hit third parties in tests. `respx` intercepts `httpx`:

```python
# pip install respx
import httpx, respx

@respx.mock
def test_outbound():
    respx.get("https://api.example.com/rate").mock(
        return_value=httpx.Response(200, json={"rate": 1.5})
    )
    assert httpx.get("https://api.example.com/rate").json()["rate"] == 1.5
```

### Comparison with Django testing

| | Django | FastAPI |
| --- | --- | --- |
| Client | `django.test.Client` | `TestClient` (httpx) |
| Test database | Created and torn down automatically | You wire it up |
| Fixtures | Fixture files, factories | pytest fixtures, `factory_boy` |
| Faking collaborators | `unittest.mock.patch` | `dependency_overrides` (no patching) |
| Transaction rollback | `TestCase` wraps each test | Manual connection-bound fixture |
| Email assertions | `mail.outbox` | Override the mail dependency |
