---
icon: material/check-decagram-outline
---

# Pydantic

Pydantic is the validation and serialisation layer FastAPI is built on. Its v2 core is written in Rust (`pydantic-core`), which is where most of FastAPI's reputation for speed actually comes from.

### What it does

A `BaseModel` is a class whose annotations are enforced at runtime. It parses and coerces input, raises structured errors, and serialises back out.

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    age: int = Field(ge=13, le=120)
    signed_up: datetime | None = None

user = UserCreate(username="alice", email="a@b.com", age="30")
print(user.age, type(user.age))     # 30 <class 'int'>
print(user.model_dump())
```

Note `age="30"` becomes the integer `30`. Pydantic is a *parsing* library by default, not a strict type checker — worth knowing, because it surprises people. Opt into strictness per field with `Field(strict=True)` or globally with `model_config = ConfigDict(strict=True)`.

### Pydantic v1 vs v2 — the migration cheat sheet

Reliably asked, because most real codebases have lived through it:

| v1 | v2 |
| --- | --- |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj()` | `.model_validate()` |
| `.parse_raw()` | `.model_validate_json()` |
| `.schema()` | `.model_json_schema()` |
| `@validator` | `@field_validator` (must be a `classmethod`) |
| `@root_validator` | `@model_validator(mode="before" \| "after")` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes = True` |
| `allow_population_by_field_name` | `populate_by_name` |
| `Optional[X]` implied optional | `X \| None` still needs `= None` to be optional |

That last row bites people: in v2, `x: int | None` is **required** and merely nullable. Only `x: int | None = None` is optional.

### Validators

```python
from pydantic import BaseModel, field_validator, model_validator

class Booking(BaseModel):
    nights: int
    guest: str
    promo_code: str | None = None

    @field_validator("guest")
    @classmethod
    def title_case(cls, value: str) -> str:
        return value.strip().title()

    @field_validator("nights")
    @classmethod
    def sane_stay(cls, value: int) -> int:
        if not 1 <= value <= 30:
            raise ValueError("stay must be between 1 and 30 nights")
        return value

    @model_validator(mode="after")
    def promo_needs_long_stay(self):
        if self.promo_code and self.nights < 3:
            raise ValueError("promo codes require at least 3 nights")
        return self

print(Booking(nights=5, guest="  alice smith ").guest)   # Alice Smith
```

- `field_validator` sees one field. `mode="before"` gets the raw input, `mode="after"` (default) gets the coerced value.

- `model_validator` sees the whole model, so it is where cross-field rules go.

- Raise `ValueError` (or `AssertionError`), not `HTTPException`. Pydantic converts it into the 422 detail structure for you.

### Reading from ORM objects

To build a response model from a SQLAlchemy row you need attribute access rather than dict access:

```python
from pydantic import BaseModel, ConfigDict

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str

class Row:                       # stands in for an ORM instance
    id = 1
    username = "alice"
    password_hash = "nope"

print(UserOut.model_validate(Row()).model_dump())
```

`password_hash` is not declared, so it is dropped. When you pass such an object straight out of a FastAPI endpoint with `response_model=UserOut`, this is exactly what happens.

### Separate models per direction

A near-universal convention, and the answer to "how do you stop the password hash leaking?":

```python
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):      # inbound: accepts a password
    password: str

class UserUpdate(BaseModel):     # inbound: everything optional for PATCH
    username: str | None = None
    email: str | None = None

class UserOut(UserBase):         # outbound: no password, exposes id
    id: int
```

For `PATCH`, pair `UserUpdate` with `model_dump(exclude_unset=True)` so a field the client did not send is left alone rather than overwritten with `None`:

```python
from pydantic import BaseModel

class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None

patch = UserUpdate(email="new@b.com")
print(patch.model_dump(exclude_unset=True))    # {'email': 'new@b.com'}
```

### Settings from the environment

`pydantic-settings` (a separate package in v2) gives typed, validated configuration — the FastAPI counterpart to Django's `settings.py`:

```python
# pip install pydantic-settings
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    database_url: str
    debug: bool = False
    max_connections: int = 10
```

Combine it with a cached dependency so the file is read once:

```python
from functools import lru_cache

@lru_cache
def get_settings() -> "Settings":
    return Settings()
```

The dependency stays overridable in tests while the `lru_cache` keeps it a singleton in production.

### Performance notes

- `model_dump()` then letting FastAPI re-serialise means paying twice. Returning a `dict` and setting `response_model` lets FastAPI do it once.

- For very large lists, `response_model` validation can dominate. Measure before reaching for `ORJSONResponse` or bypassing the model.

- `model_construct()` skips validation entirely. Only use it on data you already trust — it will happily build an invalid model.

- Reuse model classes; do not build them per request. Schema construction is the expensive part and it is cached on the class.
