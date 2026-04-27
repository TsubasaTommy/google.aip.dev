from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import Aip, Category, Scope

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_AIP_FILENAME_RE = re.compile(r"^(\d{4})\.md$")
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _parse_aip(file_path: Path, repo_root: Path, scope_code: str) -> Aip | None:
    text = file_path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]

    aip_id = fm.get("id")
    if aip_id is None:
        fn = _AIP_FILENAME_RE.match(file_path.name)
        if not fn:
            return None
        aip_id = int(fn.group(1))

    title_match = _TITLE_RE.search(body)
    title = title_match.group(1).strip() if title_match else f"AIP-{aip_id}"

    placement = fm.get("placement") or {}

    return Aip(
        id=int(aip_id),
        scope=scope_code,
        state=str(fm.get("state", "unknown")),
        title=title,
        created=str(fm["created"]) if fm.get("created") else None,
        updated=str(fm["updated"]) if fm.get("updated") else None,
        category=placement.get("category"),
        order=placement.get("order"),
        body_markdown=body,
        path=str(file_path.relative_to(repo_root)),
    )


def _parse_scope(scope_yaml: Path) -> Scope:
    data = yaml.safe_load(scope_yaml.read_text(encoding="utf-8")) or {}
    cats: list[Category] = []
    for c in data.get("categories", []) or []:
        if isinstance(c, dict):
            code = str(c.get("code", "")).strip()
            if not code:
                continue
            title = c.get("title") or code.replace("-", " ").title()
            cats.append(Category(code=code, title=str(title)))
        elif isinstance(c, str):
            cats.append(Category(code=c, title=c.replace("-", " ").title()))
    return Scope(
        code=scope_yaml.parent.name,
        title=str(data.get("title", scope_yaml.parent.name)),
        order=int(data.get("order", 0)),
        categories=tuple(cats),
    )


def load_corpus(repo_root: Path) -> tuple[list[Aip], list[Scope]]:
    """Load every AIP markdown file and scope.yaml under ``aip/``.

    The unique key for an AIP is ``(scope, id)`` — number spaces may overlap
    across scopes, so callers must not assume id alone is unique.
    """
    aip_dir = repo_root / "aip"
    if not aip_dir.is_dir():
        raise FileNotFoundError(f"AIP directory not found at {aip_dir}")

    scopes: list[Scope] = []
    aips: list[Aip] = []
    for scope_dir in sorted(p for p in aip_dir.iterdir() if p.is_dir()):
        scope_yaml = scope_dir / "scope.yaml"
        if scope_yaml.exists():
            scopes.append(_parse_scope(scope_yaml))
        for md in sorted(scope_dir.glob("*.md")):
            if not _AIP_FILENAME_RE.match(md.name):
                continue
            aip = _parse_aip(md, repo_root, scope_dir.name)
            if aip is not None:
                aips.append(aip)
    return aips, scopes
