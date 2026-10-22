#!/usr/bin/env bash
set -euo pipefail
set +x

echo "===== LINT ====="

ruff check "${CI_PROJECT_DIR:-.}"