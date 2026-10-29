"""Maintenance job: tạo SparkSession, chọn table, chạy procedure song song, tổng kết."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType

from lakehouse.configs.catalog import CatalogConfig
from lakehouse.configs.maintenance import MaintenanceConfig
from lakehouse.maintenance.procedures import ACTIONS
from lakehouse.spark.session import get_or_create_session
from lakehouse.utils.string import parse_namespace, quote
from lakehouse.utils.tables import list_tables

log = logging.getLogger(__name__)

_MAX_LOGGED_ROWS = 20

# Iceberg báo commit bị writer khác chen ngang (validation/commit failed).
_CONFLICT_MARKERS = (
    "ValidationException",
    "CommitFailedException",
    "Cannot commit",
    "found new delete",
    "Found new conflicting",
    "Missing required files to delete",
)


def _qualified(catalog: str, table: str) -> str:
    return quote([catalog, *parse_namespace(table)])


def _column_names(schema: StructType, prefix: str = "") -> set[str]:
    """Tên mọi cột, kể cả field lồng nhau: {'_cdc', '_cdc.ts', ...}."""
    names: set[str] = set()
    for f in schema.fields:
        name = f"{prefix}{f.name}"
        names.add(name)
        if isinstance(f.dataType, StructType):
            names |= _column_names(f.dataType, f"{name}.")
    return names


@dataclass
class TableResult:
    table: str
    succeeded: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    seconds: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.failed


def _is_commit_conflict(exc: Exception) -> bool:
    """Xung đột commit với writer khác (vd silver MERGE) -> thử lại được."""
    msg = str(exc)
    return any(m in msg for m in _CONFLICT_MARKERS)


def _call_with_conflict_retry(
    spark: SparkSession, table: str, name: str, sql: str, cfg: dict
) -> list[dict]:
    """Chạy ``sql``; nếu xung đột commit thì chờ rồi thử lại (plan lại trên snapshot mới).

    ``retry_attempts`` / ``retry_wait_seconds`` trong config của action; lỗi khác raise ngay.
    """
    attempts = max(int(cfg.get("retry_attempts", 0)), 0) + 1
    wait = int(cfg.get("retry_wait_seconds", 120))
    for attempt in range(1, attempts + 1):
        log.info("%s: %s%s", table, name, f" (attempt {attempt})" if attempt > 1 else "")
        try:
            return [r.asDict() for r in spark.sql(sql).collect()]
        except Exception as exc:
            if attempt == attempts or not _is_commit_conflict(exc):
                raise
            log.warning(
                "%s: %s commit conflict, retry sau %ds: %s",
                table, name, wait, str(exc).splitlines()[0],
            )
            time.sleep(wait)
    raise AssertionError("unreachable")


def run_table_maintenance(
    spark: SparkSession, catalog: str, table: str, settings: dict, dry_run: bool = False
) -> TableResult:
    """Chạy các procedure đã enable theo thứ tự ACTIONS.

    ``dry_run=True`` (CLI): chỉ log câu CALL, không thực thi.
    ``remove_orphan_files.dry_run`` trong YAML: vẫn CALL Iceberg nhưng chỉ liệt kê
    file orphan (không xóa) — khác với CLI dry-run.
    """
    result = TableResult(table)
    start = time.monotonic()
    for name, build_sql in ACTIONS.items():
        cfg = dict(settings.get(name) or {})

        if not cfg.get("enabled", False):
            continue

        sql = build_sql(catalog, table, cfg)

        if dry_run:
            log.info("[dry-run] %s", sql)
            result.succeeded.append(name)
            continue

        try:
            rows = _call_with_conflict_retry(spark, table, name, sql, cfg)
            shown = rows if len(rows) <= _MAX_LOGGED_ROWS else rows[:_MAX_LOGGED_ROWS]
            log.info(
                "%s: %s -> %d row(s) %s%s",
                table,
                name,
                len(rows),
                shown,
                " ..." if len(rows) > len(shown) else "",
            )
            result.succeeded.append(name)
        except Exception as exc:  # keep going with the next action / table
            log.exception("%s: %s failed", table, name)
            result.failed[name] = str(exc).splitlines()[0]

    result.seconds = time.monotonic() - start
    return result


def run_job(
    catalog_cfg: CatalogConfig,
    cfg: MaintenanceConfig,
    tables: list[str] | None = None,
    dry_run: bool = False,
) -> list[TableResult]:
    """Tạo SparkSession, chạy maintenance cho ``tables`` (mặc định: mọi table được chọn)."""
    spark = get_or_create_session(catalog_cfg, app_name="lakehouse-maintenance")
    catalog = catalog_cfg.name
    try:
        tables = tables or [
            t for t in list_tables(spark, catalog) if cfg.is_selected(t)
        ]
        log.info("Running maintenance on %d tables", len(tables))

        def run_one(table: str) -> TableResult:
            columns = None
            if cfg.needs_columns(table):
                try:
                    columns = _column_names(
                        spark.table(_qualified(catalog, table)).schema
                    )
                except Exception as exc:  # table lỗi load -> để procedure tự báo lỗi
                    log.warning("%s: không đọc được schema: %s", table, exc)
            return run_table_maintenance(
                spark, catalog, table, cfg.table_settings(table, columns), dry_run
            )

        with ThreadPoolExecutor(max_workers=max(cfg.parallelism, 1)) as pool:
            results = list(pool.map(run_one, tables))
    finally:
        spark.stop()

    failed = [r for r in results if not r.ok]
    for r in results:
        log.info(
            "%-60s %-6s %6.1fs %s",
            r.table,
            "OK" if r.ok else "FAILED",
            r.seconds,
            r.failed or "",
        )
    log.info("Done: %d ok, %d failed", len(results) - len(failed), len(failed))
    return results
