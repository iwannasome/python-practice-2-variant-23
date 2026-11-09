#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -n "${PYTHON:-}" ]; then
    exec "$PYTHON" -m practice2 "$@"
fi
exec .venv/bin/python -m practice2 "$@"
