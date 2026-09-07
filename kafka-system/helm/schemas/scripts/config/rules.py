#!/usr/bin/env python3
"""Sync registry global config (rules).

reference:
https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-rule-reference.html

"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from common import (
    CONFIG_FILE,
    get_json,
    get_json_list,
    post_json,
    load_yaml,
    path_seg,
    put_json,
    require,
)

SKIP_CONFIG_SYNC = "SKIP_CONFIG_SYNC"

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

def list_global_rule(base: str) -> dict[RuleType, str]:
    types = get_json_list(f"{base}/admin/rules")
    rules: dict[RuleType, str] = {}
    for raw in types:
        rule_type = RuleType(raw)
        body = get_json(f"{base}/admin/rules/{path_seg(rule_type)}")
        cfg = body.get("config")
        if not cfg:
            raise ValueError(f"missing config for rule {rule_type.value}")
        rules[rule_type] = str(cfg)
    return rules

def create_global_rule(base: str, rule: RuleConfig) -> None:
    post_json(
        f"{base}/admin/rules",
        {
            "ruleType": rule.rule_type.value,
            "config": rule.config,
        },
    )

def update_global_rule(base: str, rule: RuleConfig) -> None:
    put_json(
        f"{base}/admin/rules/{path_seg(rule.rule_type.value)}",
        {"config": rule.config},
    )

def load_config() -> list[RuleConfig]:
    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

    data = load_yaml(CONFIG_FILE)
    rules = require(data, "globalRules", CONFIG_FILE)
    if not isinstance(rules, list):
        raise ValueError(f"'globalRules' must be a list in {CONFIG_FILE}")

    rule_configs: list[RuleConfig] = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ValueError(f"globalRules[{i}] must be an object in {CONFIG_FILE}")

        rule_type = require(rule, "ruleType", CONFIG_FILE)
        config = require(rule, "config", CONFIG_FILE)
        rule_config = RuleConfig(
            rule_type=RuleType(rule_type), 
            config=config,
        )
        rule_configs.append(rule_config)

    return rule_configs

def sync_config(base: str) -> None:
    if os.environ.get(SKIP_CONFIG_SYNC):
        print("[config] skipped config sync")
        return
    
    desired = load_config()
    existing = list_global_rule(base)
    
    created = 0
    updated = 0
    for rule in desired:
        current = existing.get(rule.rule_type)
        if current == rule.config:
            continue

        if current is None:
            create_global_rule(base, rule)
            created += 1
        else:
            update_global_rule(base, rule)
            updated += 1

    print(f"[config] listed={len(existing)} created={created} updated={updated}")
