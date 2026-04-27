from __future__ import annotations

from aip_mcp.search import BM25Index


def test_search_finds_get_method_aip(corpus):
    aips, _ = corpus
    index = BM25Index(aips)
    hits = index.search("standard get method resource", top_k=5)
    ids = [(a.scope, a.id) for a, _ in hits]
    assert ("general", 131) in ids


def test_search_respects_scope(corpus):
    aips, _ = corpus
    index = BM25Index(aips)
    hits = index.search("authentication", scope="auth", top_k=10)
    assert hits, "expected at least one hit in auth scope"
    for a, _ in hits:
        assert a.scope == "auth"


def test_empty_query_returns_empty(corpus):
    aips, _ = corpus
    index = BM25Index(aips)
    assert index.search("", top_k=5) == []
    assert index.search("   ", top_k=5) == []
