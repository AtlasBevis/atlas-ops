"""Config của job maintenance: chọn table, parallelism, defaults + override theo glob."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lakehouse.utils.setting import CONFIG_DIR, deep_merge, load_yaml


@dataclass
class MaintenanceConfig:
    include: list[str]
    exclude: list[str]
    parallelism: int
    defaults: dict[str, Any]
    overrides: list[dict[str, Any]]

    def is_selected(self, table: str) -> bool:
        return any(fnmatch.fnmatch(table, p) for p in self.include) and not any(
            fnmatch.fnmatch(table, p) for p in self.exclude
        )

    def needs_columns(self, table: str) -> bool:
        """Có override nào khớp ``table`` mà cần kiểm tra ``has_columns`` không."""
        return any(
            o.get("has_columns") and fnmatch.fnmatch(table, o["match"])
            for o in self.overrides
        )

    def table_settings(
        self, table: str, columns: set[str] | None = None
    ) -> dict[str, Any]:
        """Defaults merged with every override whose `match` glob fits `table`.

        Override có ``has_columns`` chỉ áp dụng khi table có đủ các cột đó
        (``columns``: tên cột dạng ``a.b`` cho field lồng nhau). Vd ``raw.*`` có
        table không có ``_cdc.ts`` -> bỏ override, dùng defaults thay vì lỗi
        FIELD_NOT_FOUND ở ``where``.
        """
        settings = self.defaults
        for override in self.overrides:
            if not fnmatch.fnmatch(table, override["match"]):
                continue
            required = override.get("has_columns") or []
            if required and not set(required) <= (columns or set()):
                continue
            settings = deep_merge(
                settings,
                {k: v for k, v in override.items() if k not in ("match", "has_columns")},
            )
        return settings


def load_maintenance_config(
    path: str | Path = CONFIG_DIR / "maintenance.yaml",
) -> MaintenanceConfig:
    raw = load_yaml(path)
    selection = raw.get("selection", {})
    return MaintenanceConfig(
        include=selection.get("include", ["*"]),
        exclude=selection.get("exclude", []),
        parallelism=int(raw.get("parallelism", 1)),
        defaults=raw.get("defaults", {}),
        overrides=raw.get("overrides", []),
    )
