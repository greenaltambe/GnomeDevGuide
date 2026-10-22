#!/bin/sh
# Build build/GnomeDevGuide.html and .pdf from chapters/*.md
# Needs: python3 -m venv .venv && .venv/bin/pip install markdown weasyprint pygments
set -e
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
[ -x "$PY" ] || PY=/tmp/docvenv/bin/python
exec "$PY" tools/make.py
