"""SparkApplication entrypoint: local:///opt/spark/jobs/maintenance.py [--tables ...] [--dry-run]."""

from __future__ import annotations

from lakehouse.maintenance.main import main

if __name__ == "__main__":
    raise SystemExit(main())
