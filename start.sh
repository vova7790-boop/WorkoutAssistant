#!/data/data/com.termux/files/usr/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Virtual environment not found. Run ./setup.sh first."
    exit 1
fi
termux-wake-lock
echo "==> Wake lock acquired."

cd "$SCRIPT_DIR"
"$VENV_DIR/bin/python" -m bot.main

termux-wake-unlock
echo "==> Wake lock released."
