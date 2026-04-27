from __future__ import annotations


def test_loads_a_substantial_corpus(corpus):
    aips, scopes = corpus
    assert len(aips) > 100
    scope_codes = {s.code for s in scopes}
    assert {"general", "cloud", "auth"}.issubset(scope_codes)


def test_aip131_general_metadata(corpus):
    aips, _ = corpus
    aip131 = next((a for a in aips if a.scope == "general" and a.id == 131), None)
    assert aip131 is not None
    assert aip131.state == "approved"
    assert "Standard methods: Get" in aip131.title
    assert aip131.category == "operations"
    assert aip131.body_markdown.startswith("# Standard methods: Get")


def test_aip001_general_meta_state(corpus):
    aips, _ = corpus
    aip1 = next((a for a in aips if a.scope == "general" and a.id == 1), None)
    assert aip1 is not None
    assert aip1.category == "meta"
    assert "AIP Purpose" in aip1.title


def test_unique_keys(corpus):
    aips, _ = corpus
    keys = [(a.scope, a.id) for a in aips]
    assert len(keys) == len(set(keys))


def test_general_scope_categories(corpus):
    _, scopes = corpus
    general = next(s for s in scopes if s.code == "general")
    codes = {c.code for c in general.categories}
    assert {"meta", "resource-design", "operations"}.issubset(codes)


def test_no_aip_loaded_from_pages(corpus):
    aips, _ = corpus
    for a in aips:
        assert a.path.startswith("aip/"), a.path
