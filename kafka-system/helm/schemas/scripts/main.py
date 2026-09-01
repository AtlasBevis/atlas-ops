#!/usr/bin/env python3
"""CI:
Register schema
"""

from __future__ import annotations

import os
import sys

from artifact import sync_artifacts
from config import sync_config
from domain_layout import validate_and_scaffold_groups
from group import sync_groups


def get_registry_url() -> str:
    url = (os.environ.get("REGISTRY_URL") or "").strip()
    if not url:
        raise SystemExit("ERROR: REGISTRY_URL is required")
    return url.rstrip("/")


def main() -> int:
    url = get_registry_url()
    print(f">>> Registry: {url}")

    sync_config(url)
    errs = validate_and_scaffold_groups(scaffold=False)
    if errs:
        raise SystemExit(f"domain validation failed: {errs[0]}")
    groups = sync_groups(url)
    sync_artifacts(url, groups)
    print("Done.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
