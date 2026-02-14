#!/usr/bin/env bash
# Run from project root
set -e
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
. .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
