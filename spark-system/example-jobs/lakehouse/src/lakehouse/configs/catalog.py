"""Catalog config (Lakekeeper / Iceberg REST), dùng chung mọi job."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lakehouse.utils.setting import CONFIG_DIR, load_yaml


@dataclass
class CatalogConfig:
    name: str
    uri: str
    warehouse: str
    credential: str = ""
    oauth2_server_uri: str = ""
    scope: str = ""
    extra_spark_conf: dict[str, str] = field(default_factory=dict)


def load_catalog(path: str | Path = CONFIG_DIR / "catalog.yaml") -> CatalogConfig:
    return CatalogConfig(**load_yaml(path)["catalog"])
