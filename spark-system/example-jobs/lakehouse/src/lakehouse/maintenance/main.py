"""CLI của job maintenance: `maintenance.py [--tables ...] [--dry-run]`.

Config luôn lấy từ ``$LAKEHOUSE_CONFIG_DIR`` (image: ``/opt/app/config``,
local: ``configs``): ``catalog.yaml`` + ``maintenance.yaml``.
"""

from __future__ import annotations

import argparse
import logging

from lakehouse.configs.catalog import load_catalog
from lakehouse.configs.maintenance import load_maintenance_config
from lakehouse.maintenance.job import run_job


def _parse_tables(raw: list[str] | None) -> list[str]:
    """`--tables a b` hoặc `--tables a,b,c` / `a, b` → list tên bảng."""
    if not raw:
        return []
    out: list[str] = []
    for item in raw:
        out.extend(t.strip() for t in item.replace(",", " ").split() if t.strip())
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tables", nargs="*", help="run these tables")
    p.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show query CALL, không thực thi",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s"
    )

    args = parse_args(argv)
    results = run_job(
        load_catalog(),
        load_maintenance_config(),
        _parse_tables(args.tables),
        args.dry_run,
    )
    return 1 if any(not r.ok for r in results) else 0
