#!/usr/bin/env python3
"""Sync registry global config (rules) from core/config/global_rules.yaml."""

from __future__ import annotations
import os

from common import ROOT, get_json, load_yaml, path_seg, put_json, require

CONFIG_FILE = ROOT / "core" / "config" / "global_rules.yaml"

def _get_global_rule(base: str, rule_type: str) -> str | None:
    data = get_json(f"{base}/admin/rules/{path_seg(rule_type)}", allow_404=True)
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
        current = _get_global_rule(base, str(rule_type))
        if current == config:
            continue
        put_json(
            f"{base}/admin/rules/{path_seg(str(rule_type))}",
            {"config": config},
        )
        updated += 1
        print(f"[config] rule {rule_type}={config} (updated)")