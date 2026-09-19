#!/usr/bin/env python3
"""GET global rules."""

from __future__ import annotations

from core.common import get_json, get_json_list, path_seg

from .rule_types import RuleType


def list_global_rules(base: str) -> dict[RuleType, str]:
    """GET /admin/rules then GET /admin/rules/{ruleType}."""
    types = get_json_list(f"{base}/admin/rules")
    rules: dict[RuleType, str] = {}
    for raw in types:
        rule_type = RuleType(raw)
        body = get_json(f"{base}/admin/rules/{path_seg(rule_type.value)}")
        cfg = body.get("config")
        if not cfg:
            raise ValueError(f"missing config for rule {rule_type.value}")
        rules[rule_type] = str(cfg)
    return rules
