from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    code: str
    title: str


@dataclass(frozen=True)
class Scope:
    code: str
    title: str
    order: int
    categories: tuple[Category, ...]


@dataclass
class Aip:
    id: int
    scope: str
    state: str
    title: str
    created: str | None
    updated: str | None
    category: str | None
    order: int | None
    body_markdown: str
    path: str
