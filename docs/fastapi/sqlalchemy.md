---
icon: material/database-cog
---

# SQLAlchemy

FastAPI ships no ORM, so SQLAlchemy 2.x is the usual choice. The interview interest is in the async engine, session lifecycle and the N+1 problem.

### Declarative models (2.x style)

```python
from datetime import datetime
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    books: Mapped[list["Book"]] = relationship(back_populates="author")

class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    created: Mapped[datetime] = mapped_column(server_default=func.now())
    author: Mapped[Author] = relationship(back_populates="books")
```

`Mapped[...]` and `mapped_column` are the 2.x annotation-driven style — nullability comes from the annotation (`Mapped[str | None]`), so it no longer has to be repeated in the column.

### Async engine and session

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,      # drop dead connections instead of erroring
    echo=False,
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep attributes readable after commit
)
```

Two settings worth being able to justify:

- **`expire_on_commit=False`.** By default SQLAlchemy expires instances on commit, so touching an attribute afterwards triggers a lazy reload — which raises in async code. Turning it off is near-mandatory in FastAPI.

- **`pool_pre_ping=True`.** Cheap `SELECT 1` before handing out a pooled connection, which avoids the classic "server closed the connection unexpectedly" after an idle period.

The driver prefix matters: `postgresql+asyncpg` for async, `postgresql+psycopg2` for sync. Mixing an async engine with a sync driver is a common setup error.

### Session as a dependency

One session per request, committed on success, rolled back on failure, always closed:

```python
from typing import Annotated, AsyncIterator
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

SessionDep = Annotated[AsyncSession, Depends(get_session)]

@app.get("/books/{book_id}")
async def read_book(book_id: int, session: SessionDep):
    book = await session.get(Book, book_id)
    return {"id": book.id, "title": book.title}
```

Aliasing the annotation as `SessionDep` keeps signatures readable once you have thirty endpoints.

### Querying with `select()`

2.x uses `select()` uniformly; `Query` is legacy.

```python
from sqlalchemy import select

async def examples(session: AsyncSession):
    # One row or None
    result = await session.execute(select(Book).where(Book.id == 1))
    book = result.scalar_one_or_none()

    # Many rows
    result = await session.execute(select(Book).order_by(Book.created.desc()).limit(20))
    books = result.scalars().all()

    # Join
    result = await session.execute(
        select(Book.title, Author.name).join(Author).where(Author.name == "Ada")
    )
    rows = result.all()

    return book, books, rows
```

`.scalars()` unwraps single-entity rows so you get `Book` objects rather than one-tuples — a small thing people trip on.

### The N+1 problem

The highest-value thing to be able to explain. Lazy loading issues one query per parent:

```python
async def n_plus_one(session: AsyncSession) -> None:
    # 1 query for books, then 1 more per book to load .author -> N+1
    result = await session.execute(select(Book).limit(100))
    for book in result.scalars():
        print(book.author.name)
```

In async SQLAlchemy this does not merely run slowly — it raises `MissingGreenlet`, because the implicit lazy load would need to do blocking I/O outside an await. That error is effectively a built-in N+1 detector.

Fix it by loading eagerly:

```python
from sqlalchemy.orm import joinedload, selectinload

async def eager_loading(session: AsyncSession) -> None:
    # One JOIN. Best for many-to-one.
    await session.execute(select(Book).options(joinedload(Book.author)))

    # Two queries: parents, then children with WHERE id IN (...).
    # Best for one-to-many, avoids row multiplication.
    await session.execute(select(Author).options(selectinload(Author.books)))
```

The Django parallel is exact: `joinedload` ≈ `select_related`, `selectinload` ≈ `prefetch_related`.

You can also make the default safe by declaring `relationship(lazy="raise")`, which turns any accidental lazy load into a loud error at development time.

### Transactions

```python
async def transfer(session: AsyncSession, amount: int) -> None:
    async with session.begin():          # commits on exit, rolls back on exception
        ...

async def with_savepoint(session: AsyncSession) -> None:
    async with session.begin_nested():   # SAVEPOINT
        ...
```

Do not mix `session.begin()` with a dependency that also commits — you will get "a transaction is already begun". Pick one place to own the transaction boundary, usually the dependency.

### Things to watch

- **No lazy attribute access after the session closes.** The session ends with the request, so load everything you need, or convert to a Pydantic model before returning.

- **Pool sizing.** `pool_size × worker_count` must stay under the database's `max_connections`. Four workers at `pool_size=10, max_overflow=20` can demand 120 connections.

- **`await` every I/O call.** `session.get`, `session.execute`, `session.commit`, `session.flush` are all awaitables in async mode.

- **`session.get` vs `select`.** `get` checks the identity map first and can skip the query entirely for a primary-key lookup.

- **Bulk work.** Prefer `insert()`/`update()` statements over looping ORM objects when writing thousands of rows.
