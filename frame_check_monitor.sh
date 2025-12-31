#!/bin/bash
# Frame check monitoring system for touchHLE game testing
# This is an EXTENSION to crash_monitor.sh for debugging screen truncation issues
#
# WORKFLOW:
#   1. ./frame_check_monitor.sh run   - Runs 3 clicks, waits 5s, captures frame
#   2. Claude Code analyzes the captured frame for truncation/black screen
#   3. If truncated: debug and fix, rebuild, rerun
#   4. If crash: check crash log instead
#
# EXIT CODES:
#   0 = Crash detected (check CRASH_FILE for details)
#   1 = Timeout or clean exit (no crash, no frame)
#   2 = Frame captured successfully (check FRAME_FILE)

# Import common variables from crash_monitor.sh
GAME_DIR="/d/touchHLE_src"
TOUCHHLE="/d/touchHLE_src/target/release/touchHLE.exe"
GAME_IPA="touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa"
LOG_FILE="/tmp/touchhle_game.log"
PID_FILE="/tmp/touchhle_game.pid"
STATUS_FILE="/tmp/touchhle_game.status"
CRASH_FILE="/tmp/touchhle_crash.txt"
INJECT_FILE="/d/touchHLE_src/inject.json"
RUN_COUNTER_FILE="/tmp/touchhle_run_counter"

# Frame check specific variables
REPLAY_3CLICKS_SCRIPT="/d/touchHLE_src/replay_3clicks.sh"
CAPTURE_DIR="/d/touchHLE_src/captures"
FRAME_STATUS_FILE="/tmp/touchhle_frame_status"
CAPTURED_FRAME_FILE="/tmp/touchhle_captured_frame.png"

# Get and increment run counter (same as crash_monitor.sh)
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

    export RUST_BACKTRACE=1
    # For frame-check mode, always enable both event-inject AND frame-capture
    # Set FORCE_COMPOSITION=true to test composition path vs fast path
    local EXTRA_ARGS=""
    if [ "${FORCE_COMPOSITION:-false}" = "true" ]; then
        EXTRA_ARGS="--force-composition"
        echo "Using --force-composition" >&2
    fi
    if [ "$USE_INJECT" = "true" ]; then
        $TOUCHHLE "$GAME_IPA" --event-inject="$INJECT_FILE" --frame-capture="$CAPTURE_DIR" $EXTRA_ARGS > "$LOG_FILE" 2>&1 &
    else
        $TOUCHHLE "$GAME_IPA" --frame-capture="$CAPTURE_DIR" $EXTRA_ARGS > "$LOG_FILE" 2>&1 &
    fi
    GAME_PID=$!
    echo $GAME_PID > "$PID_FILE"

    local count=$(get_run_count)
    increment_run_count
    echo "Game started with PID $GAME_PID (run #$count, RUST_BACKTRACE=1 enabled)" >&2
}

# Wait for frame capture or crash
wait_for_frame_or_crash() {
    local TIMEOUT=${1:-120}
    local START=$(date +%s)
    echo "Monitoring for frame capture or crash (timeout: ${TIMEOUT}s)..." >&2

    # Create capture directory if it doesn't exist
    mkdir -p "$CAPTURE_DIR"

    # Clear old captures
    rm -f "$CAPTURE_DIR"/frame_*.ppm "$CAPTURED_FRAME_FILE"

    while true; do
        local NOW=$(date +%s)
        local ELAPSED=$((NOW - START))

        if [ $ELAPSED -ge $TIMEOUT ]; then
            echo "TIMEOUT" > "$FRAME_STATUS_FILE"
            echo "TIMEOUT: No frame capture or crash in ${TIMEOUT}s" >&2
            force_kill_game
            return 1
        fi

        # Check for crash FIRST (priority over frame capture)
        if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
            echo "CRASHED" > "$FRAME_STATUS_FILE"
            force_kill_game
            grep -B 10 -A 40 "panicked at" "$LOG_FILE" > "$CRASH_FILE"
            echo "=== CRASH DETECTED (frame-check mode) ==="
            echo "Game crashed before frame capture completed!"
            echo ""
            grep -B 10 -A 40 "panicked at" "$LOG_FILE" | tail -55
            echo "=== END CRASH ==="
            return 0
        fi

        # Check for captured frame (PPM files in capture directory)
        local LATEST_FRAME=$(ls -t "$CAPTURE_DIR"/frame_*.ppm 2>/dev/null | head -1)
        if [ -n "$LATEST_FRAME" ] && [ -f "$LATEST_FRAME" ]; then
            echo "Frame captured: $LATEST_FRAME" >&2

            # Convert PPM to PNG for easier viewing/analysis
            if command -v convert &> /dev/null; then
                convert "$LATEST_FRAME" "$CAPTURED_FRAME_FILE"
                echo "Converted to PNG: $CAPTURED_FRAME_FILE" >&2
            elif command -v magick &> /dev/null; then
                magick "$LATEST_FRAME" "$CAPTURED_FRAME_FILE"
                echo "Converted to PNG: $CAPTURED_FRAME_FILE" >&2
            else
                # Fallback: just copy PPM (Claude can still read it)
                cp "$LATEST_FRAME" "${CAPTURED_FRAME_FILE%.png}.ppm"
                CAPTURED_FRAME_FILE="${CAPTURED_FRAME_FILE%.png}.ppm"
                echo "No ImageMagick found, using PPM: $CAPTURED_FRAME_FILE" >&2
            fi

            echo "FRAME_CAPTURED" > "$FRAME_STATUS_FILE"
            force_kill_game

            echo "=== FRAME CAPTURED ==="
            echo "Frame saved to: $CAPTURED_FRAME_FILE"
            echo ""
            echo "Claude Code should now analyze this frame to check for:"
            echo "  - Screen truncation (black area at bottom)"
            echo "  - Fullscreen issues"
            echo ""
            echo "Frame file: $CAPTURED_FRAME_FILE"
            echo "=== END FRAME CAPTURE ==="
            return 2
        fi

        # Check if game exited unexpectedly
        if [ -f "$PID_FILE" ]; then
            local PID=$(cat "$PID_FILE")
            if ! ps -p $PID > /dev/null 2>&1; then
                if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
                    echo "CRASHED" > "$FRAME_STATUS_FILE"
                    grep -B 10 -A 40 "panicked at" "$LOG_FILE" > "$CRASH_FILE"
                    echo "=== CRASH DETECTED ==="
                    grep -B 10 -A 40 "panicked at" "$LOG_FILE" | tail -55
                    echo "=== END CRASH ==="
                    return 0
                else
                    echo "EXITED" > "$FRAME_STATUS_FILE"
                    echo "Game exited without crash or frame capture" >&2
                    return 1
                fi
            fi
        fi
        sleep 0.5
    done
}

case "$1" in
    run)
        # Check run counter - odd runs don't work, so skip them
        RUN_COUNT=$(get_run_count)
        if [ $((RUN_COUNT % 2)) -eq 1 ]; then
            echo "=== Skipping odd run #$RUN_COUNT (touch injection quirk) ===" >&2
            increment_run_count
            start_game true
            sleep 1
            force_kill_game
            sleep 1
            echo "=== Restarting on even run ===" >&2
        fi

        echo "=== FRAME-CHECK MODE ===" >&2
        echo "This will replay 3 clicks, wait 5 seconds, then capture frame." >&2
        echo "Used to debug screen truncation / black screen issues." >&2
        echo "" >&2

        # Clear previous status
        rm -f "$FRAME_STATUS_FILE" "$CAPTURED_FRAME_FILE"

        start_game true
        "$REPLAY_3CLICKS_SCRIPT" &
        REPLAY_PID=$!

        echo "=== Waiting for frame capture or crash... ===" >&2
        wait_for_frame_or_crash ${2:-120}
        EXIT_CODE=$?
        kill $REPLAY_PID 2>/dev/null

        # Output status for Claude Code to parse
        echo ""
        echo "=== FRAME-CHECK RESULT ==="
        if [ -f "$FRAME_STATUS_FILE" ]; then
            STATUS=$(cat "$FRAME_STATUS_FILE")
            echo "STATUS: $STATUS"
            if [ "$STATUS" = "FRAME_CAPTURED" ]; then
                echo "FRAME_FILE: $CAPTURED_FRAME_FILE"
            elif [ "$STATUS" = "CRASHED" ]; then
                echo "CRASH_FILE: $CRASH_FILE"
            fi
        else
            echo "STATUS: UNKNOWN"
        fi
        echo "=== END RESULT ==="

        exit $EXIT_CODE
        ;;
    status)
        if [ ! -f "$FRAME_STATUS_FILE" ]; then
            echo "NOT_STARTED"
        else
            cat "$FRAME_STATUS_FILE"
        fi
        ;;
    frame-file)
        if [ -f "$CAPTURED_FRAME_FILE" ]; then
            echo "$CAPTURED_FRAME_FILE"
        elif [ -f "${CAPTURED_FRAME_FILE%.png}.ppm" ]; then
            echo "${CAPTURED_FRAME_FILE%.png}.ppm"
        else
            echo "No frame captured"
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
    *)
        echo "Usage: $0 {run|status|frame-file|crash|log|stop}"
        echo ""
        echo "  run [timeout]  - FRAME-CHECK: 3 clicks, wait 5s, capture frame"
        echo "  status         - Check frame-check status (FRAME_CAPTURED, CRASHED, etc.)"
        echo "  frame-file     - Get path to captured frame file"
        echo "  crash          - Show crash details (if crashed)"
        echo "  log            - Show recent log output"
        echo "  stop           - Stop the game"
        echo ""
        echo "EXIT CODES:"
        echo "  0 = Crash detected (check ./frame_check_monitor.sh crash)"
        echo "  1 = Timeout or clean exit"
        echo "  2 = Frame captured (check ./frame_check_monitor.sh frame-file)"
        ;;
esac
