---
icon: material/source-branch
---

# Alembic

Alembic is SQLAlchemy's migration tool — the thing you have to add because FastAPI has no equivalent of `makemigrations` / `migrate`.

### Mental model

A migration is a Python module with `upgrade()` and `downgrade()`. Alembic keeps a **directed graph** of them, each with a `revision` id and a `down_revision` pointer, and records the applied head in an `alembic_version` table in your database.

Unlike Django, Alembic does not track model state itself. It diffs your `MetaData` against the live database when you autogenerate, which is why the setup step of pointing it at your models matters.

### Getting started

```bash
pip install alembic
alembic init -t async migrations     # -t async for an async engine
```

That creates:

```
migrations/
  env.py            # how Alembic connects and runs migrations
  script.py.mako    # template for new revision files
  versions/         # the migration modules
alembic.ini
```

### Wiring `env.py` to your models

The two things to change — read config from the environment rather than hardcoding a URL, and set `target_metadata` so autogenerate can see your tables:

```python
# migrations/env.py (the parts that matter)
import os
from alembic import context
from myapp.models import Base          # your DeclarativeBase

config = context.config
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

target_metadata = Base.metadata
```

Your models must actually be *imported* for `Base.metadata` to be populated. A model in a module nobody imports is invisible to autogenerate, and its table silently never gets created — a classic first-day-with-Alembic bug.

### Everyday commands

```bash
# Create a revision by diffing models against the DB
alembic revision --autogenerate -m "add books table"

# Create an empty revision (data migrations, raw SQL)
alembic revision -m "backfill slugs"

# Apply everything outstanding
alembic upgrade head

# Move one step at a time
alembic upgrade +1
alembic downgrade -1

# Where am I / what exists
alembic current
alembic history --verbose
alembic heads

# Emit SQL instead of executing it, for review or a DBA
alembic upgrade head --sql > migration.sql
```

### What a revision looks like

```python
"""add books table

Revision ID: a1b2c3d4e5f6
Revises: 0f9e8d7c6b5a
"""
import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "0f9e8d7c6b5a"

def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("authors.id"), nullable=False),
    )
    op.create_index("ix_books_title", "books", ["title"])

def downgrade() -> None:
    op.drop_index("ix_books_title", table_name="books")
    op.drop_table("books")
```

### What autogenerate misses

Worth naming, because "I always review the generated file" is the answer interviewers want:

- Table or column **renames** — it sees a drop and an add, which destroys data. Rewrite as `op.alter_column(..., new_column_name=...)`.

- **Server defaults** and constraint changes, unless you enable `compare_server_default=True`.

- **Type changes** are detected inconsistently; `compare_type=True` helps but is not complete.

- **Indexes on expressions**, partial indexes, `CHECK` constraints and most database-specific DDL.

- **Data.** Autogenerate only writes schema; backfills are always hand-written.

### Adding a NOT NULL column to a populated table

The migration that fails in staging and teaches everyone this lesson. It cannot be done in one step:

```python
def upgrade() -> None:
    # 1. Add it nullable
    op.add_column("books", sa.Column("slug", sa.String(200), nullable=True))

    # 2. Backfill
    op.execute("UPDATE books SET slug = lower(replace(title, ' ', '-')) WHERE slug IS NULL")

    # 3. Now tighten it
    op.alter_column("books", "slug", nullable=False)
```

On a large table under load, `ALTER TABLE` also takes locks — mention `CREATE INDEX CONCURRENTLY` (Postgres) and that it cannot run inside a transaction, so it needs its own migration with the transaction disabled.

### Multiple heads

Two developers branching from the same revision produces two heads. `alembic upgrade head` then fails, ambiguously:

```bash
alembic heads                          # see them
alembic merge -m "merge heads" <rev1> <rev2>
alembic upgrade head
```

Prevent it in CI by asserting there is exactly one head.

### Running migrations in deployment

Do **not** run migrations from FastAPI's `lifespan`. With four Uvicorn workers that is four processes racing to migrate the same database. Run them as a separate step before the new version starts serving — an init container, a release phase, or a one-off job.

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For zero-downtime deploys, keep migrations **backwards compatible** with the currently running code: add columns before writing to them, deploy the code, and only drop the old column in a later release. Old and new versions overlap during a rolling deploy, so any single migration must be safe for both.

### Alembic vs Django migrations

| | Django | Alembic |
| --- | --- | --- |
| Detection | Compares against stored migration state | Diffs models against the live database |
| Autogenerate quality | High; handles renames interactively | Lower; always review the output |
| Dependency model | Linear per app, with cross-app dependencies | Free-form graph, explicit `down_revision` |
| Data migrations | `RunPython` | `op.execute` or a plain empty revision |
| Setup | Zero — built in | You wire up `env.py` and `target_metadata` |
