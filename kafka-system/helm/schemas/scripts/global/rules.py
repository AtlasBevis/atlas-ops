#!/usr/bin/env python3
"""Sync registry global config (rules).

reference:
https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-rule-reference.html

"""

from __future__ import annotations
from enum import Enum
import os

from dataclasses import dataclass

from common import (
    ROOT, 
    get_json, 
    load_yaml, 
    path_seg, 
    put_json, 
    require
)

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

def _get_global_rule(base: str, rule_type: RuleType) -> str | None:
    data = get_json(f"{base}/admin/rules/{path_seg(rule_type.value)}", allow_404=True)
    if not data:
        return None
    return data.get("config")


def sync_config(base: str) -> None:
    if os.environ.get("SKIP_CONFIG_SYNC"):
        print("[config] skipping config sync")
        return
    
    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

    data = load_yaml(CONFIG_FILE)
    rules = require(data, "globalRules", CONFIG_FILE)
    if not isinstance(rules, list):
        raise ValueError(f"'globalRules' must be a list in {CONFIG_FILE}")

    updated = 0
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ValueError(f"globalRules[{i}] must be an object in {CONFIG_FILE}")
        
        rule_type = require(rule, "ruleType", CONFIG_FILE)
        config = require(rule, "config", CONFIG_FILE)
        rule_config = RuleConfig(rule_type=RuleType(rule_type), config=config)
        current = _get_global_rule(base, rule_config.rule_type)
        if current == config:
            continue
        put_json(
            f"{base}/admin/rules/{path_seg(rule_config.rule_type.value)}",
            {"config": rule_config.config},
        )
        updated += 1
        print(f"[config] rule {rule_config.rule_type.value}={rule_config.config} (updated)")