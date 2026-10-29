"""Build Iceberg ``CALL system.*`` statements; ACTIONS keeps the recommended order."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from lakehouse.utils.string import parse_namespace, quote


# sales.orders -> 'sales.orders'
# 'event_date' -> ''event_date''
def _sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _table(catalog: str, table: str) -> str:
    """('lakehouse-uat', 'raw.credit-bureau.orders')
    -> '`lakehouse-uat`.`raw`.`credit-bureau`.`orders`' (SQL string).

    Iceberg parse ``table =>`` như SQL identifier: phần có ``-`` phải backtick, và
    nếu thiếu catalog nó thử phần đầu (``raw``) làm catalog trước -> WARN
    ``Failed to load catalog: raw`` cho mỗi CALL. Nhận cả tên đã quote sẵn.
    """
    return _sql_str(quote([catalog, *parse_namespace(table)]))


def _map_literal(options: dict[str, Any]) -> str:
    pairs = ", ".join(
        f"{_sql_str(str(k))}, {_sql_str(str(v))}" for k, v in options.items()
    )
    return f"map({pairs})"


def _timestamp_hours_ago(hours: int) -> str:
    ts = datetime.now(timezone.utc) - timedelta(hours=hours)
    return f"TIMESTAMP {_sql_str(ts.strftime('%Y-%m-%d %H:%M:%S'))}"


def _timestamp_days_ago(days: int) -> str:
    return _timestamp_hours_ago(days * 24)


def rewrite_data_files(catalog: str, table: str, cfg: dict) -> str:
    args = [
        f"table => {_table(catalog, table)}",
        f"strategy => {_sql_str(cfg.get('strategy', 'binpack'))}",
    ]
    if cfg.get("sort_order"):
        args.append(f"sort_order => {_sql_str(cfg['sort_order'])}")
    if cfg.get("where"):
        args.append(f"where => {_sql_str(cfg['where'])}")
    if cfg.get("options"):
        args.append(f"options => {_map_literal(cfg['options'])}")
    return f"CALL `{catalog}`.system.rewrite_data_files({', '.join(args)})"


def rewrite_position_delete_files(catalog: str, table: str, cfg: dict) -> str:
    args = [f"table => {_table(catalog, table)}"]
    if cfg.get("options"):
        args.append(f"options => {_map_literal(cfg['options'])}")
    if cfg.get("where"):
        args.append(f"where => {_sql_str(cfg['where'])}")
    return f"CALL `{catalog}`.system.rewrite_position_delete_files({', '.join(args)})"


def rewrite_manifests(catalog: str, table: str, cfg: dict) -> str:
    return f"CALL `{catalog}`.system.rewrite_manifests(table => {_table(catalog, table)})"


def expire_snapshots(catalog: str, table: str, cfg: dict) -> str:
    # older_than_hours (nếu có) ưu tiên hơn older_than_days: table CDC commit dày,
    # giữ theo ngày vẫn còn hàng nghìn snapshot.
    if cfg.get("older_than_hours") is not None:
        older_than = _timestamp_hours_ago(int(cfg["older_than_hours"]))
    else:
        older_than = _timestamp_days_ago(int(cfg.get("older_than_days", 7)))
    args = [
        f"table => {_table(catalog, table)}",
        f"older_than => {older_than}",
        f"retain_last => {int(cfg.get('retain_last', 1))}",
    ]
    # Xóa file song song (mặc định Iceberg xóa tuần tự trên driver -> rất chậm
    # khi expire hàng chục nghìn snapshot lần đầu).
    if cfg.get("max_concurrent_deletes"):
        args.append(f"max_concurrent_deletes => {int(cfg['max_concurrent_deletes'])}")
    return f"CALL `{catalog}`.system.expire_snapshots({', '.join(args)})"


def remove_orphan_files(catalog: str, table: str, cfg: dict) -> str:
    # prefix_listing: list file qua Iceberg FileIO (S3FileIO + vended credentials)
    return (
        f"CALL `{catalog}`.system.remove_orphan_files("
        f"table => {_table(catalog, table)}, "
        f"older_than => {_timestamp_days_ago(int(cfg.get('older_than_days', 3)))}, "
        f"dry_run => {str(bool(cfg.get('dry_run', False))).lower()}, "
        f"prefix_listing => {str(bool(cfg.get('prefix_listing', True))).lower()})"
    )


ACTIONS: dict[str, Callable[[str, str, dict], str]] = {
    "rewrite_data_files": rewrite_data_files,
    "rewrite_position_delete_files": rewrite_position_delete_files,
    "rewrite_manifests": rewrite_manifests,
    "expire_snapshots": expire_snapshots,
    "remove_orphan_files": remove_orphan_files,
}
