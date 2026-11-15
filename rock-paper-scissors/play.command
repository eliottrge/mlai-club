#!/bin/bash
# Mac/Linux launcher. Installs any missing libraries into your Python (needs internet the first time).
cd "$(dirname "$0")"

# Find Python: prefer 3.11/3.12/3.10 (TensorFlow-compatible), then plain python3/python.
PY=""
for c in python3.11 python3.12 python3.10 python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
    echo "Python was not found. Install Python 3.11 from https://www.python.org/downloads/"
    echo "then run this file again."
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi

# Install the libraries only if something is missing.
if ! "$PY" -c "import tensorflow, tf_keras, cv2, numpy" >/dev/null 2>&1; then
    echo "Installing libraries into this Python. This can take a few minutes..."
    if ! "$PY" -m pip install -r requirements.txt; then
        echo
        echo "Setup failed. Check your internet connection. TensorFlow needs Python 3.10, 3.11 or 3.12;"
        echo "if you have a newer Python, install Python 3.11 and try again."
        read -n 1 -s -r -p "Press any key to close..."
        exit 1
    fi
    echo "Setup complete."
fi

"$PY" rps_game.py "$@" || read -n 1 -s -r -p "Press any key to close..."
