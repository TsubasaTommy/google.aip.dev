from __future__ import annotations

from pathlib import Path

import pytest

from aip_mcp.loader import load_corpus

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def corpus():
    return load_corpus(REPO_ROOT)
