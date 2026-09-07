#!/usr/bin/env python3
"""CI:
Register schema
API Spec: https://www.apicur.io/registry/docs/apicurio-registry/3.1.x/assets-attachments/registry-rest-api.htm
author: Truong Thanh Binh
"""

from __future__ import annotations

import os
import sys

from config import sync_config
from groups import sync_groups

REGISTRY_URL = "REGISTRY_URL"

def get_registry_url() -> str:
    url = (os.environ.get(REGISTRY_URL) or "").strip()
    if not url:
        raise SystemExit("ERROR: REGISTRY_URL is required")
    return url.rstrip("/")


def main() -> int:
    url = get_registry_url()
    print(f">>> Registry: {url}")

    # Sync config
    sync_config(url)

    # Sync groups
    groups = sync_groups(url)
    
    print("Done.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
