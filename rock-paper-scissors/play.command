#!/bin/bash
# Mac/Linux launcher. First run installs everything automatically (needs internet).
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    PY=""
    for c in python3.11 python3.12 python3.10 python3; do
        if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
    done
    if [ -z "$PY" ]; then
        echo "Python was not found. Install Python 3.11 from https://www.python.org/downloads/"
        echo "then run this file again."
        read -n 1 -s -r -p "Press any key to close..."
        exit 1
    fi
    echo "First-time setup: installing libraries. This can take a few minutes..."
    if ! { "$PY" -m venv .venv && .venv/bin/python -m pip install --upgrade pip \
           && .venv/bin/python -m pip install -r requirements.txt; }; then
        echo "Setup failed. Check your internet connection and try again."
        rm -rf .venv
        read -n 1 -s -r -p "Press any key to close..."
        exit 1
    fi
    echo "Setup complete."
fi

.venv/bin/python rps_game.py "$@" || read -n 1 -s -r -p "Press any key to close..."
