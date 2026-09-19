#!/usr/bin/env python3
"""POST / PUT global rules."""

from __future__ import annotations

from core.common import path_seg, post_json, put_json

from .models import RuleConfig


def create_global_rule(base: str, rule: RuleConfig) -> None:
    """POST /admin/rules"""
    post_json(
        f"{base}/admin/rules",
        {
            "ruleType": rule.rule_type.value,
            "config": rule.config,
        },
    )


def update_global_rule(base: str, rule: RuleConfig) -> None:
    """PUT /admin/rules/{ruleType}"""
    put_json(
        f"{base}/admin/rules/{path_seg(rule.rule_type.value)}",
        {"config": rule.config},
    )
