#!/bin/bash
# Crash monitoring system for touchHLE game testing
# Usage:
#   ./crash_monitor.sh run     - Start game and BLOCK until crash (returns crash info immediately)
#   ./crash_monitor.sh start   - Start game in background only
#   ./crash_monitor.sh status  - Check if game is running or crashed
#   ./crash_monitor.sh crash   - Get crash details if crashed
#   ./crash_monitor.sh stop    - Stop the game

GAME_DIR="/d/touchHLE_src"
TOUCHHLE="/d/touchHLE_src/target/release/touchHLE.exe"
GAME_IPA="touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa"
LOG_FILE="/tmp/touchhle_game.log"
PID_FILE="/tmp/touchhle_game.pid"
STATUS_FILE="/tmp/touchhle_game.status"
CRASH_FILE="/tmp/touchhle_crash.txt"

force_kill_game() {
    # Force kill using taskkill on Windows (dismisses crash dialogs)
    if [ -f "$PID_FILE" ]; then
        local PID=$(cat "$PID_FILE")
        taskkill //F //PID $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        sleep 0.5
    fi
    # Also kill any touchHLE processes by name as backup
    taskkill //F //IM touchHLE.exe 2>/dev/null || true
}

start_game() {
    # Kill any existing game
    force_kill_game
    sleep 1

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

    echo "Monitoring for crash (timeout: ${TIMEOUT}s)..." >&2

    while true; do
        local NOW=$(date +%s)
        local ELAPSED=$((NOW - START))

        if [ $ELAPSED -ge $TIMEOUT ]; then
            echo "TIMEOUT: No crash detected in ${TIMEOUT}s" >&2
            return 1
        fi

        # Check for crash in log FIRST (before checking if process ended)
        if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
            echo "CRASHED" > "$STATUS_FILE"
            
            # Force kill the process immediately to dismiss any crash dialogs
            force_kill_game
            
            # Save crash details to file
            grep -B 10 -A 40 "panicked at" "$LOG_FILE" > "$CRASH_FILE"
            
            # Output crash info to STDOUT (so it's captured by caller)
            echo "=== CRASH DETECTED ==="
            grep -B 10 -A 40 "panicked at" "$LOG_FILE" | tail -55
            echo "=== END CRASH ==="
            return 0
        fi

        # Check if process ended without crash
        if [ -f "$PID_FILE" ]; then
            local PID=$(cat "$PID_FILE")
            if ! ps -p $PID > /dev/null 2>&1; then
                # Process ended - check one more time for crash
                if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
                    echo "CRASHED" > "$STATUS_FILE"
                    grep -B 10 -A 40 "panicked at" "$LOG_FILE" > "$CRASH_FILE"
                    echo "=== CRASH DETECTED ==="
                    grep -B 10 -A 40 "panicked at" "$LOG_FILE" | tail -55
                    echo "=== END CRASH ==="
                    return 0
                else
                    echo "Game exited without crash" >&2
                    return 1
                fi
            fi
        fi

        sleep 0.5
    done
}

case "$1" in
    run)
        # START GAME AND BLOCK UNTIL CRASH - This is the main command to use
        start_game
        echo "=== Game running. Interact with game to trigger crash. Waiting... ===" >&2
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
        if [ -f "$CRASH_FILE" ]; then
            cat "$CRASH_FILE"
        elif [ -f "$LOG_FILE" ] && grep -q "panicked at" "$LOG_FILE"; then
            grep -B 10 -A 40 "panicked at" "$LOG_FILE" | tail -55
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
        force_kill_game
        rm -f "$PID_FILE"
        echo "Game stopped"
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
