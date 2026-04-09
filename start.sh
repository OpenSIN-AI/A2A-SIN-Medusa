#!/usr/bin/env bash
# Start Medusa in NATS daemon mode
# Usage: ./start.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export NATS_URL="${NATS_URL:-nats://92.5.60.87:4222}"
export PYTHONPATH="$SCRIPT_DIR/../../OpenSIN-Neural-Bus/sdk/python:$PYTHONPATH"
exec python3 "$SCRIPT_DIR/src/medusa.py" --listen
