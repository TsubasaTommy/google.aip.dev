from __future__ import annotations

from aip_mcp.references import build_reference_graph


def test_aip131_references_aip121(corpus):
    aips, _ = corpus
    g = build_reference_graph(aips)
    out = g.outgoing.get(("general", 131), set())
    assert ("general", 121) in out


def test_incoming_includes_callers(corpus):
    aips, _ = corpus
    g = build_reference_graph(aips)
    inc = g.incoming.get(("general", 121), set())
    assert ("general", 131) in inc


def test_no_self_references(corpus):
    aips, _ = corpus
    g = build_reference_graph(aips)
    for src, targets in g.outgoing.items():
        assert src not in targets
