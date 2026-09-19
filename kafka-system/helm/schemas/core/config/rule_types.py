#!/usr/bin/env python3
"""Apicurio global rule types."""

from __future__ import annotations

from enum import Enum


class RuleType(str, Enum):
    VALIDITY = "VALIDITY"
    COMPATIBILITY = "COMPATIBILITY"
    INTEGRITY = "INTEGRITY"


RULE_CONFIGS: dict[RuleType, frozenset[str]] = {
    RuleType.VALIDITY: frozenset({
        "FULL",
        "SYNTAX_ONLY",
        "NONE",
    }),
    RuleType.COMPATIBILITY: frozenset({
        "FULL",
        "FULL_TRANSITIVE",
        "BACKWARD",
        "BACKWARD_TRANSITIVE",
        "FORWARD",
        "FORWARD_TRANSITIVE",
        "NONE",
    }),
    RuleType.INTEGRITY: frozenset({
        "FULL",
        "NO_DUPLICATES",
        "NO_CIRCULAR_REFERENCES",
        "REFS_EXIST",
        "ALL_REFS_MAPPED",
        "NONE",
    }),
}
