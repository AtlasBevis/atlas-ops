#!/usr/bin/env python3
"""Global rule config model."""

from __future__ import annotations

from dataclasses import dataclass

from .rule_types import RULE_CONFIGS, RuleType


@dataclass(frozen=True, slots=True)
class RuleConfig:
    rule_type: RuleType
    config: str

    def __post_init__(self) -> None:
        if self.config not in RULE_CONFIGS[self.rule_type]:
            allowed = ", ".join(RULE_CONFIGS[self.rule_type])
            raise ValueError(
                f"Invalid config '{self.config}' "
                f"for rule type '{self.rule_type.value}'. "
                f"Allowed values: {allowed}"
            )
