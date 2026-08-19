"""MkDocs hook: make links to other sites open in a new tab.

Applied at build time rather than with JavaScript, so it also works with JS
disabled and is visible in the generated HTML.

Only absolute ``http(s)://`` links are rewritten. Internal page links stay in the
same tab on purpose — sending those to a new tab would spawn a tab for every nav
click and break in-site navigation. That also leaves the glightbox image anchors
alone, since their hrefs are relative.

``rel="noopener noreferrer"`` is added alongside ``target="_blank"`` so the opened
page cannot reach back through ``window.opener``.
"""

import re

# An <a> tag that has an absolute http(s) href.
_ANCHOR = re.compile(r"<a\s(?P<attrs>[^>]*href=\"https?://[^\"]*\"[^>]*)>", re.IGNORECASE)

_HAS_TARGET = re.compile(r"\btarget\s*=", re.IGNORECASE)
_REL = re.compile(r"\brel\s*=\s*\"(?P<value>[^\"]*)\"", re.IGNORECASE)

_WANTED_REL = ("noopener", "noreferrer")


def _rewrite(match: re.Match) -> str:
    attrs = match.group("attrs")

    # Respect an explicit target that is already set.
    if _HAS_TARGET.search(attrs):
        return match.group(0)

    rel_match = _REL.search(attrs)
    if rel_match:
        tokens = rel_match.group("value").split()
        tokens += [t for t in _WANTED_REL if t not in tokens]
        attrs = f'{attrs[: rel_match.start()]}rel="{" ".join(tokens)}"{attrs[rel_match.end() :]}'
    else:
        attrs = f'{attrs} rel="{" ".join(_WANTED_REL)}"'

    return f'<a {attrs} target="_blank">'


def on_post_page(output: str, page, config) -> str:
    return _ANCHOR.sub(_rewrite, output)
