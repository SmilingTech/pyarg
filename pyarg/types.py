from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Structures.
@dataclass
class PyArgOutput:
    arguments: dict[str, Any]
    command: str | None = field(default=None)
    entrypoint_output: Any | None = field(default=None)
