#!/bin/sh

# ============================================================
# JARVIS SERVER SUPERVISOR
# ============================================================

BASE_DIR="/volume1/_Shared/Jarvis"
SERVER="$BASE_DIR/server.py"
RESTART_FLAG="$BASE_DIR/restart.flag"
LOG="$BASE_DIR/jarvis_supervisor.log"

# Give DSM a sensible PATH.
PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export PATH

# Find Python 3 automatically.
PYTHON=$(command -v python3)

cd "$BASE_DIR" || exit 1

echo "========================================" >> "$LOG"
echo "Jarvis supervisor started: $(date)" >> "$LOG"
echo "========================================" >> "$LOG"
echo "Python detected: $PYTHON" >> "$LOG"
echo "Server: $SERVER" >> "$LOG"
echo "" >> "$LOG"

# Make sure Python was found.
if [ -z "$PYTHON" ]; then

    echo "ERROR: python3 could not be found." >> "$LOG"
    exit 1

fi

while true
do

    echo "Starting Jarvis: $(date)" >> "$LOG"

    "$PYTHON" "$SERVER" >> "$LOG" 2>&1

    EXIT_CODE=$?

    echo "Jarvis exited with code $EXIT_CODE: $(date)" >> "$LOG"

    # If the restart flag exists, consume it
    # and restart immediately.

    if [ -f "$RESTART_FLAG" ]; then

        rm -f "$RESTART_FLAG"

        echo "Restart requested. Restarting Jarvis..." >> "$LOG"

        sleep 1

        continue

    fi

    # If Jarvis stops unexpectedly, restart it.

    echo "Jarvis stopped unexpectedly." >> "$LOG"
    echo "Restarting in 3 seconds..." >> "$LOG"

    sleep 3

done