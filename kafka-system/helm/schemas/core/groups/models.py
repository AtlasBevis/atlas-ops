#!/usr/bin/env python3
"""Group model."""

from __future__ import annotations

import re
from dataclasses import dataclass

GROUP_ID_RE = re.compile(r"^.{1,512}$")
RESERVED_GROUP_IDS = frozenset({"default"})


@dataclass(frozen=True, slots=True)
class Group:
    group_id: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.group_id, str):
            raise ValueError(f"groupId must be a string, got {type(self.group_id).__name__}")

        if not GROUP_ID_RE.fullmatch(self.group_id):
            raise ValueError(
                f"Invalid groupId '{self.group_id}': must be 1-512 characters"
            )

        if self.group_id in RESERVED_GROUP_IDS:
            raise ValueError(f"groupId '{self.group_id}' is reserved")

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError(
                f"description for groupId '{self.group_id}' must be a string or omitted"
            )
