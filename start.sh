#!/usr/bin/env bash
# Varaxis Lens: set up on first run, then open the app in your browser.
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "First run: setting up (takes a minute)…"
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
exec .venv/bin/streamlit run app.py
