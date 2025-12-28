#!/bin/bash
# Crash monitoring system for touchHLE game testing
#
# WORKFLOW FOR DEBUGGING:
#   1. ./crash_monitor.sh auto   - Runs game with auto-replay, waits for crash
#   2. Analyze crash output (PC, registers, stack trace)
#   3. Fix the bug in source code
#   4. ./build_monitor.sh start && ./build_monitor.sh wait  - Rebuild
#   5. Repeat from step 1
#
# EXIT CODES:
#   0 = Crash detected and captured (SUCCESS - we triggered the bug!)
#   1 = Game exited without crash or timeout (need to investigate)
#
# RUST_BACKTRACE is automatically enabled for detailed stack traces
#
# NOTE: Due to a quirk, touch injection only works on even-numbered runs.
# The script automatically skips odd runs by killing and restarting.

GAME_DIR="/d/touchHLE_src"
TOUCHHLE="/d/touchHLE_src/target/release/touchHLE.exe"
GAME_IPA="touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa"
LOG_FILE="/tmp/touchhle_game.log"
PID_FILE="/tmp/touchhle_game.pid"
STATUS_FILE="/tmp/touchhle_game.status"
CRASH_FILE="/tmp/touchhle_crash.txt"
INJECT_FILE="/d/touchHLE_src/inject.json"
REPLAY_SCRIPT="/d/touchHLE_src/replay_sequence.sh"
RUN_COUNTER_FILE="/tmp/touchhle_run_counter"

# Get and increment run counter
get_run_count() {
    if [ -f "$RUN_COUNTER_FILE" ]; then
        cat "$RUN_COUNTER_FILE"
    else
        echo "0"
    fi
}

increment_run_count() {
    local count=$(get_run_count)
    echo $((count + 1)) > "$RUN_COUNTER_FILE"
}

reset_run_count() {
    echo "0" > "$RUN_COUNTER_FILE"
}

force_kill_game() {
    if [ -f "$PID_FILE" ]; then
        local PID=$(cat "$PID_FILE")
        taskkill //F //PID $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        sleep 0.5
    fi
    taskkill //F //IM touchHLE.exe 2>/dev/null || true
}

start_game() {
    local USE_INJECT=${1:-false}
    force_kill_game
    sleep 1
    rm -f "$LOG_FILE" "$CRASH_FILE" "$STATUS_FILE"
    > "$INJECT_FILE"
    echo "RUNNING" > "$STATUS_FILE"
    cd "$GAME_DIR"

    # Enable Rust backtrace for detailed crash stack traces
    export RUST_BACKTRACE=1
    if [ "$USE_INJECT" = "true" ]; then
        $TOUCHHLE "$GAME_IPA" --event-inject="$INJECT_FILE" > "$LOG_FILE" 2>&1 &
    else
        $TOUCHHLE "$GAME_IPA" > "$LOG_FILE" 2>&1 &
    fi
    GAME_PID=$!
    echo $GAME_PID > "$PID_FILE"

    local count=$(get_run_count)
    increment_run_count
    echo "Game started with PID $GAME_PID (run #$count, RUST_BACKTRACE=1 enabled)" >&2
}

wait_for_crash() {
    local TIMEOUT=${1:-600}
    local START=$(date +%s)
    echo "Monitoring for crash (timeout: ${TIMEOUT}s)..." >&2

    while true; do
        local NOW=$(date +%s)
        local ELAPSED=$((NOW - START))

        if [ $ELAPSED -ge $TIMEOUT ]; then
            echo "TIMEOUT: No crash detected in ${TIMEOUT}s" >&2
            return 1
        fi

        if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
            echo "CRASHED" > "$STATUS_FILE"
            force_kill_game
            grep -B 10 -A 40 "panicked at" "$LOG_FILE" > "$CRASH_FILE"
            echo "=== CRASH DETECTED ==="
            echo "Auto-replay successfully triggered the crash!"
            echo ""
            grep -B 10 -A 40 "panicked at" "$LOG_FILE" | tail -55
            echo "=== END CRASH ==="
            echo ""
            echo "Next steps:"
            echo "  1. Analyze the crash (PC: 0x108da8, null pointer access)"
            echo "  2. Fix the bug in the source code"
            echo "  3. Rebuild: ./build_monitor.sh start && ./build_monitor.sh wait"
            echo "  4. Test again: ./crash_monitor.sh auto"
            return 0  # Exit 0 = crash successfully triggered
        fi

        if [ -f "$PID_FILE" ]; then
            local PID=$(cat "$PID_FILE")
            if ! ps -p $PID > /dev/null 2>&1; then
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
        start_game false
        echo "=== Game running (manual play). Waiting for crash... ===" >&2
        wait_for_crash ${2:-600}
        ;;
    auto)
        # Check run counter - odd runs don't work, so skip them
        RUN_COUNT=$(get_run_count)
        if [ $((RUN_COUNT % 2)) -eq 1 ]; then
            echo "=== Skipping odd run #$RUN_COUNT (touch injection quirk) ===" >&2
            increment_run_count
            # Start and immediately kill to advance the counter
            start_game true
            sleep 1
            force_kill_game
            sleep 1
            echo "=== Restarting on even run ===" >&2
        fi

        echo "=== AUTO-REPLAY MODE ===" >&2
        echo "This will automatically replay recorded clicks to trigger the crash." >&2
        echo "" >&2
        start_game true
        "$REPLAY_SCRIPT" &
        REPLAY_PID=$!
        echo "=== Waiting for crash... ===" >&2
        wait_for_crash ${2:-600}
        EXIT_CODE=$?
        kill $REPLAY_PID 2>/dev/null
        exit $EXIT_CODE
        ;;
    start)
        start_game false
        echo "Game started. Use './crash_monitor.sh wait' to block until crash."
        ;;
    wait)
        wait_for_crash ${2:-600}
        ;;
    status)
        if [ ! -f "$STATUS_FILE" ]; then
            echo "NOT_STARTED"
        else
            cat "$STATUS_FILE"
        fi
        ;;
    crash)
        if [ -f "$CRASH_FILE" ]; then
            cat "$CRASH_FILE"
        else
            echo "No crash detected"
        fi
        ;;
    log)
        [ -f "$LOG_FILE" ] && tail -100 "$LOG_FILE" || echo "No log file"
        ;;
    stop)
        force_kill_game
        rm -f "$PID_FILE"
        echo "Game stopped"
        ;;
    reset-counter)
        reset_run_count
        echo "Run counter reset to 0"
        ;;
    *)
        echo "Usage: $0 {run|auto|start|wait|status|crash|log|stop|reset-counter}"
        echo ""
        echo "  auto [timeout] - AUTO-REPLAY: Start game, replay clicks, wait for crash"
        echo "  run [timeout]  - Start game for manual play, wait for crash"
        echo "  start          - Start game in background"
        echo "  wait [timeout] - Wait for crash (game already running)"
        echo "  status         - Check game status"
        echo "  crash          - Show crash details"
        echo "  log            - Show recent log output"
        echo "  stop           - Stop the game"
        echo "  reset-counter  - Reset the run counter to 0"
        echo ""
        echo "EXIT CODES:"
        echo "  0 = Crash detected (success - bug was triggered)"
        echo "  1 = No crash (timeout or clean exit)"
        ;;
esac
