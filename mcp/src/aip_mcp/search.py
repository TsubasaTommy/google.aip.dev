from __future__ import annotations

import re
from typing import Iterable

from rank_bm25 import BM25Okapi

from .models import Aip

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class BM25Index:
    def __init__(self, aips: Iterable[Aip]):
        self.aips: list[Aip] = list(aips)
        docs = [_tokenize(f"{a.title}\n{a.body_markdown}") for a in self.aips]
        self._bm25 = BM25Okapi(docs) if docs else None

    def search(
        self,
        query: str,
        top_k: int = 10,
        scope: str | None = None,
    ) -> list[tuple[Aip, float]]:
        if self._bm25 is None:
            return []
        toks = _tokenize(query)
        if not toks:
            return []
        scores = self._bm25.get_scores(toks)
        ranked: list[tuple[Aip, float]] = [
            (a, float(s)) for a, s in zip(self.aips, scores) if s > 0
        ]
        if scope:
            ranked = [(a, s) for a, s in ranked if a.scope == scope]
        ranked.sort(key=lambda x: -x[1])
        return ranked[:top_k]
