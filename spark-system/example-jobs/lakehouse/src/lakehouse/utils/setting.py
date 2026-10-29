"""Helper đọc config: CONFIG_DIR, load YAML + ${ENV} / ${ENV:-default}, deep_merge."""

from __future__ import annotations

import copy
import os
import re
from pathlib import Path
from typing import Any

import yaml

# Image set LAKEHOUSE_CONFIG_DIR=/opt/app/config; local mặc định ``configs``.
CONFIG_DIR = Path(os.environ.get("LAKEHOUSE_CONFIG_DIR", "configs"))

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):

        def repl(m: re.Match) -> str:
            name, default = m.group(1), m.group(2)
            if name in os.environ:
                return os.environ[name]
            if default is not None:
                return default
            raise KeyError(f"Environment variable {name} is not set")

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_yaml(path: str | Path) -> dict[str, Any]:
    return _expand_env(yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})


def deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
