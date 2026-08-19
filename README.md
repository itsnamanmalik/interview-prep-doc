# Senior Dev Interview Handbook (MkDocs)

MkDocs Material port of the **Senior Dev Interview Handbook** Superhuman Doc
([source](https://docs.superhuman.com/d/Senior-Dev-Interview-Handbook_dtUhpLKUpJy),
43 pages, owned by Naman Malik).

## Quick start

Dependencies are managed with [uv](https://docs.astral.sh/uv/) and pinned in `uv.lock`.

```bash
uv sync                  # create .venv from the lockfile
uv run mkdocs serve      # live-reload dev server on http://127.0.0.1:8000
uv run mkdocs build      # static site into site/
```

## Layout

```
mkdocs.yml                 site config + full nav
pyproject.toml / uv.lock   pinned dependencies
docs/
  index.md                 landing page
  assets/                  stylesheets and images
  python/                  Python (14 pages + section index)
  dsa/                     Data structures & algorithms (4 + index)
  backend-django/          Django (6 + index)
  fastapi/                 FastAPI (12 + index)
  database/                Database (9 + index)
  system-design/           System design (4 + index)
  devops/                  DevOps (3 + index)
  ai-llm-engineering/      AI/LLM engineering (14 + index)
```

75 pages in total. Within the ported sections, the section and page order mirrors
the source document's page tree; Monkey Patching, FastAPI and AI/LLM Engineering
were written for this site.

## Porting status

All 43 source pages are complete, with all 66 of the source document's hyperlinks
intact, including the YouTube video behind every "Watch Video" button. A further
31 pages (Monkey Patching, Pandas, PySpark, FastAPI, AI/LLM Engineering) were
written for this site
and are marked as such in `PORTING_STATUS.md`.

Content came from three routes: the Superhuman Docs MCP server (28 pages, until
its weekly request quota ran out), the doc's PDF export text layer (the remaining
15 pages, plus the images and tables MCP dropped), and the PDF's `/Link`
annotations read with `pypdf` (every URL, which neither of the other two exposed).

Both source diagrams — the CAP theorem Venn diagram and the Kubernetes
architecture diagram — are recreated as hand-authored SVG, so they need no
external requests and work offline.

Every image is click-to-zoom via [mkdocs-glightbox](https://github.com/blueswen/mkdocs-glightbox),
which bundles its own JS/CSS inside the package — so the lightbox adds no
external requests either.

Links to other sites open in a new tab, with `rel="noopener noreferrer"`. This is
done at build time by [hooks/open_in_new_tab.py](hooks/open_in_new_tab.py) rather
than with JavaScript, so it works with JS disabled. Internal page links are left
alone deliberately — retargeting those would spawn a tab on every nav click.

See [PORTING_STATUS.md](PORTING_STATUS.md) for the page-by-page breakdown, how
the links were verified, and which source typos were kept deliberately.
