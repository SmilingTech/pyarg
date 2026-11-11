"""Shared fixtures."""

from __future__ import annotations

import sys
from typing import Callable

import pytest


@pytest.fixture
def argv(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Set `sys.argv` as if the CLI had been called with the given arguments."""

    def _set(*args: str) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", *args])

    return _set
