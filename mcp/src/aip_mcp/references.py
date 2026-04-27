from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from .models import Aip

_INLINE_RE = re.compile(r"\[AIP-(\d+)\]\[[^\]]*\]")
_LINKDEF_RE = re.compile(
    r"^\[aip-(\d+)\]:\s*\.?/?(\d{1,4})?\.?md?",
    re.MULTILINE,
)
_LINKDEF_STRICT_RE = re.compile(
    r"^\[aip-(\d+)\]:\s*\./(\d{4})\.md(?:#\S*)?\s*$",
    re.MULTILINE,
)


Key = tuple[str, int]


@dataclass
class ReferenceGraph:
    outgoing: dict[Key, set[Key]] = field(default_factory=lambda: defaultdict(set))
    incoming: dict[Key, set[Key]] = field(default_factory=lambda: defaultdict(set))


def _resolve_scope(target_id: int, source_scope: str, keys: set[Key]) -> str | None:
    if (source_scope, target_id) in keys:
        return source_scope
    if ("general", target_id) in keys:
        return "general"
    candidates = [s for (s, i) in keys if i == target_id]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _extract_targets(body: str) -> set[int]:
    targets: set[int] = set()
    for m in _INLINE_RE.finditer(body):
        targets.add(int(m.group(1)))
    for m in _LINKDEF_STRICT_RE.finditer(body):
        targets.add(int(m.group(2)))
    return targets


def build_reference_graph(aips: Iterable[Aip]) -> ReferenceGraph:
    aips = list(aips)
    keys: set[Key] = {(a.scope, a.id) for a in aips}
    graph = ReferenceGraph()
    for a in aips:
        src: Key = (a.scope, a.id)
        for tid in _extract_targets(a.body_markdown):
            tscope = _resolve_scope(tid, a.scope, keys)
            if tscope is None:
                continue
            tgt: Key = (tscope, tid)
            if tgt == src:
                continue
            graph.outgoing[src].add(tgt)
            graph.incoming[tgt].add(src)
    return graph
