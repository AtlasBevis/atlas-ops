#!/usr/bin/env python3
"""Sync registry global config (rules)."""

from __future__ import annotations

import os

from .create import create_global_rule, update_global_rule
from .list import list_global_rules
from .load import load_config

_SKIP_CONFIG_SYNC = "SKIP_CONFIG_SYNC"


def sync_config(base: str) -> None:
    if os.environ.get(_SKIP_CONFIG_SYNC):
        print("[config] skipped config sync")
        return

    desired = load_config()
    existing = list_global_rules(base)

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
