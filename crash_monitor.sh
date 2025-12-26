#!/bin/bash
# Crash monitoring system for touchHLE game testing
# Usage:
#   ./crash_monitor.sh run     - Start game and BLOCK until crash (returns crash info immediately)
#   ./crash_monitor.sh start   - Start game in background only
#   ./crash_monitor.sh status  - Check if game is running or crashed
#   ./crash_monitor.sh crash   - Get crash details if crashed
#   ./crash_monitor.sh stop    - Stop the game

GAME_DIR="/d/touchHLE_nightly"
TOUCHHLE="/d/touchHLE_src/target/release/touchHLE.exe"
GAME_IPA="touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa"
LOG_FILE="/tmp/touchhle_game.log"
PID_FILE="/tmp/touchhle_game.pid"
STATUS_FILE="/tmp/touchhle_game.status"
CRASH_FILE="/tmp/touchhle_crash.txt"

start_game() {
    # Kill any existing game
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        kill $OLD_PID 2>/dev/null
        sleep 1
    fi

    # Clear previous files
    rm -f "$LOG_FILE" "$CRASH_FILE" "$STATUS_FILE"
    echo "RUNNING" > "$STATUS_FILE"

    cd "$GAME_DIR"

    # Start game in background, capturing all output
    $TOUCHHLE "$GAME_IPA" > "$LOG_FILE" 2>&1 &
    GAME_PID=$!
    echo $GAME_PID > "$PID_FILE"

    echo "Game started with PID $GAME_PID" >&2
}

wait_for_crash() {
    local TIMEOUT=${1:-600}  # Default 10 minutes
    local START=$(date +%s)
    local LAST_SIZE=0

    echo "Monitoring for crash (timeout: ${TIMEOUT}s)..." >&2

    while true; do
        local NOW=$(date +%s)
        local ELAPSED=$((NOW - START))

        if [ $ELAPSED -ge $TIMEOUT ]; then
            echo "TIMEOUT: No crash detected in ${TIMEOUT}s" >&2
            return 1
        fi

        # Check if process is still running
        if [ -f "$PID_FILE" ]; then
            local PID=$(cat "$PID_FILE")
            if ! ps -p $PID > /dev/null 2>&1; then
                # Process ended
                if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
                    echo "CRASHED" > "$STATUS_FILE"
                    grep -B 5 -A 35 "panicked at" "$LOG_FILE" | tail -45
                    return 0
                else
                    echo "Game exited without crash" >&2
                    return 1
                fi
            fi
        fi

        # Check for crash in log while running
        if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
            echo "CRASHED" > "$STATUS_FILE"
            # Kill the process if still running
            if [ -f "$PID_FILE" ]; then
                kill $(cat "$PID_FILE") 2>/dev/null
            fi
            grep -B 5 -A 35 "panicked at" "$LOG_FILE" | tail -45
            return 0
        fi

        sleep 1
    done
}

case "$1" in
    run)
        # START GAME AND BLOCK UNTIL CRASH - This is the main command to use
        start_game
        echo "=== Game running. Click buttons to trigger crash. Waiting... ===" >&2
        wait_for_crash ${2:-600}
        ;;

    start)
        start_game
        echo "Game started. Use 'crash_monitor.sh status' to check, or 'crash_monitor.sh wait' to block until crash."
        ;;

    wait)
        # Just wait for crash (game should already be running)
        wait_for_crash ${2:-600}
        ;;

    status)
        if [ ! -f "$STATUS_FILE" ]; then
            echo "NOT_STARTED"
            exit 0
        fi

        STATUS=$(cat "$STATUS_FILE")
        echo "$STATUS"

        if [ "$STATUS" = "RUNNING" ]; then
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                if ps -p $PID > /dev/null 2>&1; then
                    echo "Game running (PID: $PID)"
                else
                    echo "Game process ended"
                fi
            fi
        fi
        ;;

    crash)
        if [ -f "$LOG_FILE" ] && grep -q "panicked at" "$LOG_FILE"; then
            grep -B 5 -A 35 "panicked at" "$LOG_FILE" | tail -45
        else
            echo "No crash detected"
        fi
        ;;

    log)
        if [ -f "$LOG_FILE" ]; then
            tail -100 "$LOG_FILE"
        else
            echo "No log file"
        fi
        ;;

    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            kill $PID 2>/dev/null
            rm -f "$PID_FILE"
            echo "Game stopped"
        else
            echo "No game running"
        fi
        ;;

    *)
        echo "Usage: $0 {run|start|wait|status|crash|log|stop}"
        echo ""
        echo "  run [timeout]  - Start game and BLOCK until crash detected (recommended)"
        echo "  start          - Start game in background"
        echo "  wait [timeout] - Block until crash (if game already running)"
        echo "  status         - Check game status"
        echo "  crash          - Show crash details"
        echo "  log            - Show recent log output"
        echo "  stop           - Stop the game"
        exit 1
        ;;
esac
