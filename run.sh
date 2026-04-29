#!/bin/bash
set -e
cd "$(dirname "$0")"
exec python -m bot.main
