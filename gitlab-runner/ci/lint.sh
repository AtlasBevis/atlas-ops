#!/bin/bash

set -euo pipefail
set +x

echo "===== LINT ====="
ruff check .
