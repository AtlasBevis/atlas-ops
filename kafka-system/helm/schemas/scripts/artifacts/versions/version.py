from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class VersionRef:
    version: str
    state: str = "ENABLED"
    description: str | None = None