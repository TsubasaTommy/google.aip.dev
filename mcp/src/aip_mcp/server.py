from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .loader import load_corpus
from .models import Aip
from .references import ReferenceGraph, build_reference_graph
from .search import BM25Index


def _default_repo_root() -> Path:
    env = os.environ.get("AIP_REPO")
    if env:
        return Path(env).expanduser().resolve()
    # mcp/src/aip_mcp/server.py -> parents: aip_mcp, src, mcp, repo
    return Path(__file__).resolve().parents[3]


class _State:
    def __init__(self) -> None:
        self.repo_root: Path = _default_repo_root()
        self.aips_by_key: dict[tuple[str, int], Aip] = {}
        self.scopes_by_code: dict = {}
        self.search: BM25Index | None = None
        self.refs: ReferenceGraph | None = None

    def reload(self) -> dict:
        aips, scopes = load_corpus(self.repo_root)
        self.aips_by_key = {(a.scope, a.id): a for a in aips}
        self.scopes_by_code = {s.code: s for s in scopes}
        self.search = BM25Index(aips)
        self.refs = build_reference_graph(aips)
        return {"aips": len(aips), "scopes": len(scopes)}

    def resolve(self, aip_id: int, scope: str | None) -> Aip:
        if scope:
            a = self.aips_by_key.get((scope, aip_id))
            if a is None:
                raise ValueError(f"AIP {aip_id} not found in scope {scope!r}")
            return a
        matches = [a for a in self.aips_by_key.values() if a.id == aip_id]
        if not matches:
            raise ValueError(f"AIP {aip_id} not found in any scope")
        if len(matches) > 1:
            scopes = sorted(m.scope for m in matches)
            raise ValueError(
                f"AIP {aip_id} exists in multiple scopes ({scopes}); "
                "specify the scope explicitly."
            )
        return matches[0]


_state = _State()
mcp = FastMCP("aip")


def _aip_summary(a: Aip) -> dict:
    return {
        "id": a.id,
        "scope": a.scope,
        "state": a.state,
        "title": a.title,
        "category": a.category,
        "order": a.order,
        "created": a.created,
        "updated": a.updated,
        "path": a.path,
        "uri": f"aip://{a.scope}/{a.id}",
    }


@mcp.resource("aip://index", mime_type="application/json")
def index_resource() -> str:
    """JSON list of every loaded AIP's metadata (no body)."""
    items = [_aip_summary(a) for a in _state.aips_by_key.values()]
    items.sort(key=lambda x: (x["scope"], x["id"]))
    return json.dumps(items, ensure_ascii=False, indent=2)


@mcp.resource("aip://scopes", mime_type="application/json")
def scopes_resource() -> str:
    """JSON list of scope definitions with their categories."""
    items = []
    for s in sorted(_state.scopes_by_code.values(), key=lambda x: (x.order, x.code)):
        items.append(
            {
                "code": s.code,
                "title": s.title,
                "order": s.order,
                "categories": [asdict(c) for c in s.categories],
            }
        )
    return json.dumps(items, ensure_ascii=False, indent=2)


@mcp.resource("aip://{scope}/{aip_id}", mime_type="text/markdown")
def aip_resource(scope: str, aip_id: str) -> str:
    """Raw markdown (with frontmatter) of one AIP."""
    a = _state.aips_by_key.get((scope, int(aip_id)))
    if a is None:
        raise ValueError(f"AIP {aip_id} not found in scope {scope!r}")
    return (_state.repo_root / a.path).read_text(encoding="utf-8")


@mcp.tool()
def list_aips(
    scope: str | None = None,
    category: str | None = None,
    state: str | None = None,
) -> list[dict]:
    """List AIPs filtered by scope, category, or approval state.

    Returns metadata only — fetch the ``aip://{scope}/{id}`` resource
    or call ``get_aip`` for the full body.
    """
    out: list[dict] = []
    for a in _state.aips_by_key.values():
        if scope and a.scope != scope:
            continue
        if category and a.category != category:
            continue
        if state and a.state != state:
            continue
        out.append(_aip_summary(a))
    out.sort(key=lambda x: (x["scope"], x["id"]))
    return out


@mcp.tool()
def get_aip(aip_id: int, scope: str | None = None) -> dict:
    """Return one AIP including its full markdown body.

    If ``scope`` is omitted and the id exists in multiple scopes,
    raises an error listing the candidate scopes.
    """
    a = _state.resolve(aip_id, scope)
    summary = _aip_summary(a)
    summary["body_markdown"] = a.body_markdown
    return summary


@mcp.tool()
def search_aips(
    query: str,
    scope: str | None = None,
    top_k: int = 10,
) -> list[dict]:
    """BM25 full-text search over titles + bodies."""
    assert _state.search is not None
    results = _state.search.search(query, top_k=top_k, scope=scope)
    return [
        {
            "id": a.id,
            "scope": a.scope,
            "title": a.title,
            "score": round(score, 4),
            "uri": f"aip://{a.scope}/{a.id}",
        }
        for a, score in results
    ]


@mcp.tool()
def get_related_aips(aip_id: int, scope: str | None = None) -> dict:
    """Return outgoing and incoming AIP cross-references."""
    a = _state.resolve(aip_id, scope)
    assert _state.refs is not None
    src = (a.scope, a.id)

    def _expand(keys: set[tuple[str, int]]) -> list[dict]:
        rows = []
        for sc, i in sorted(keys):
            target = _state.aips_by_key.get((sc, i))
            rows.append(
                {
                    "id": i,
                    "scope": sc,
                    "title": target.title if target else None,
                    "uri": f"aip://{sc}/{i}",
                }
            )
        return rows

    return {
        "source": {"id": a.id, "scope": a.scope, "title": a.title},
        "outgoing": _expand(_state.refs.outgoing.get(src, set())),
        "incoming": _expand(_state.refs.incoming.get(src, set())),
    }


@mcp.tool()
def reload_corpus() -> dict:
    """Re-read every AIP file from disk. Useful after editing markdown."""
    return _state.reload()


def main() -> None:
    _state.reload()
    mcp.run()


if __name__ == "__main__":
    main()
