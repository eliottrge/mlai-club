#!/bin/bash
# Mac/Linux launcher. Installs any missing libraries into a compatible Python (needs internet the first time).
# TensorFlow only works with Python 3.10, 3.11 or 3.12, so newer/older Pythons are skipped.
cd "$(dirname "$0")"

PY=""
for c in python3.11 python3.12 python3.10 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && \
       "$c" -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)" >/dev/null 2>&1; then
        PY="$c"; break
    fi
done
if [ -z "$PY" ]; then
    echo "No compatible Python (3.10 - 3.12) found."
    echo "Install Python 3.11 from https://www.python.org/downloads/release/python-3119/ then run this file again."
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi
echo "Using $PY"

# Install the libraries only if something is missing.
if ! "$PY" -c "import tensorflow, tf_keras, cv2, numpy" >/dev/null 2>&1; then
    echo "Installing libraries. This can take a few minutes..."
    if ! "$PY" -m pip install --no-warn-script-location -r requirements.txt; then
        echo
        echo "Setup failed. Check your internet connection and try again."
        read -n 1 -s -r -p "Press any key to close..."
        exit 1
    fi
    echo "Setup complete."
fi

"$PY" rps_game.py "$@" || read -n 1 -s -r -p "Press any key to close..."
