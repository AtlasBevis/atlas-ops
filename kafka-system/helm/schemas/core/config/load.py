#!/usr/bin/env python3
"""Load global rules from configs/global_rules.yaml."""

from __future__ import annotations

from core.common import CONFIG_FILE, load_yaml, require

from .models import RuleConfig
from .rule_types import RuleType


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
        rule_configs.append(
            RuleConfig(
                rule_type=RuleType(rule_type),
                config=config,
            )
        )

    return rule_configs
