"""Shared fixtures."""

from __future__ import annotations

import re
import sys
from typing import Callable

import pytest


@pytest.fixture
def argv(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Set `sys.argv` as if the CLI had been called with the given arguments."""

    def _set(*args: str) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", *args])

    return _set


@pytest.fixture
def ansi_re() -> re.Pattern[str]:
    return re.compile(r"\x1b\[[0-9;]*m")
