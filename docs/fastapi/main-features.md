---
icon: material/star-outline
---

# Main Features

### 1. Type hints drive everything

One annotation does the work of parsing, validating, documenting and type-checking. There is no separate serialiser class, no schema file and no docstring format to keep in sync.

```python
from datetime import date
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Booking(BaseModel):
    guest: str
    check_in: date
    nights: int

@app.post("/bookings")
async def create(booking: Booking) -> dict[str, str]:
    return {"guest": booking.guest, "check_in": booking.check_in.isoformat()}
```

`check_in` arrives as the JSON string `"2026-03-01"` and reaches your function as a real `date`. Send `"not-a-date"` and the client gets a 422 with a field-level error before your code runs.

### 2. Automatic request validation with clear errors

Validation failures produce a structured 422 that names the exact location of each problem — far more useful to an API consumer than a generic 400:

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "nights"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "three"
    }
  ]
}
```

### 3. Interactive documentation for free

An OpenAPI 3 schema at `/openapi.json`, Swagger UI at `/docs`, ReDoc at `/redoc`. Because it is real OpenAPI, you also get client-SDK generation, contract testing and API gateway import with no extra effort.

### 4. Dependency injection

A first-class DI system built on ordinary callables. It handles shared resources, per-request setup and teardown, authentication, and is overridable in tests.

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

### 5. Native async, with a sync escape hatch

`async def` endpoints run on the event loop, so one worker can hold thousands of connections that are mostly waiting on I/O. Plain `def` endpoints are not a mistake — FastAPI runs them in a thread pool so blocking libraries stay usable.

### 6. Response shaping and filtering

The response model is a security control, not just documentation: fields absent from it are stripped, so internal columns cannot leak by accident.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserOut(BaseModel):
    id: int
    email: str

@app.get("/me", response_model=UserOut, response_model_exclude_none=True)
async def me():
    # password_hash is silently dropped: it is not on UserOut.
    return {"id": 1, "email": "a@b.com", "password_hash": "secret"}
```

### 7. Background tasks

Run work *after* the response is sent, without a broker:

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_audit(user_id: int, action: str) -> None:
    with open("/tmp/audit.log", "a") as f:
        f.write(f"{user_id} {action}\n")

@app.post("/publish")
async def publish(user_id: int, tasks: BackgroundTasks):
    tasks.add_task(write_audit, user_id, "publish")
    return {"queued": True}
```

Suitable for cheap, best-effort work only — see [Background Tasks & Email](background-tasks-and-email.md) for why anything important belongs in a real queue.

### 8. WebSockets and streaming

Inherited from Starlette, so real-time endpoints sit beside HTTP ones with no extra layer (Django needs Channels plus a channel layer for the equivalent):

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        await websocket.send_text(f"echo: {message}")
```

### 9. Middleware and CORS

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 10. Security utilities

OAuth2 password flow, bearer tokens, API keys, HTTP Basic and scope checking ship as dependencies that also register themselves in the OpenAPI schema, so `/docs` gains a working **Authorize** button.

### 11. Modularity with `APIRouter`

Group routes with a shared prefix, tags and dependencies, then mount them — the building block for a large codebase.

### 12. Standards-based, not bespoke

OpenAPI, JSON Schema, OAuth2 and ASGI are all open specs. Nothing about the wire format is FastAPI-specific, so tooling from the wider ecosystem works against your API.

### Summary table

| Feature | What it gives you |
| --- | --- |
| Type-hint driven | Validation, docs and editor support from one declaration |
| Pydantic validation | Structured 422s with per-field detail |
| OpenAPI + Swagger/ReDoc | Live docs and SDK generation for free |
| Dependency injection | Shared resources, teardown, auth, test overrides |
| ASGI + async | High concurrency for I/O-bound workloads |
| Response models | Serialisation *and* field filtering |
| Background tasks | Post-response work with no broker |
| WebSockets | Real-time endpoints without extra infrastructure |
| `APIRouter` | Modular routing for large apps |
