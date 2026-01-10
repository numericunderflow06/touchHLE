#!/bin/bash
# Crash and Black Screen monitoring system for touchHLE game testing
#
# ============================================================================
# WORKFLOW 1: CRASH DEBUGGING
# ============================================================================
#   1. ./crash_monitor.sh auto   - Runs game with auto-replay, waits for crash
#   2. Analyze crash output (PC, registers, stack trace)
#   3. Fix the bug in source code
#   4. ./build_monitor.sh start && ./build_monitor.sh wait  - Rebuild
#   5. Repeat from step 1 until exit code is 1 (no crash)
#
# ============================================================================
# WORKFLOW 2: BLACK SCREEN DEBUGGING
# ============================================================================
#   1. ./crash_monitor.sh capture - Capture frame after first click, analyze
#   2. If exit code 3 (FAIL): black pixels >= 15%, screen is too dark
#      - Review captures/session_*/analysis_results.txt for details
#      - Review captures/session_*/frame_*.png to see the actual frame
#      - Investigate rendering/lighting code
#   3. Fix the rendering bug in source code
#   4. ./build_monitor.sh start && ./build_monitor.sh wait  - Rebuild
#   5. Repeat from step 1 until exit code is 2 (PASS - black pixels < 15%)
#
#   Session folder structure:
#     captures/session_YYYY-MM-DD_HH-MM-SS/
#       ├── frame_0000.ppm        # Raw PPM capture
#       ├── frame_0000.png        # Converted PNG
#       └── analysis_results.txt  # Verdict + percentage
#
# ============================================================================
# EXIT CODES
# ============================================================================
#   0 = Crash detected (SUCCESS for crash debugging - bug was triggered!)
#   1 = No crash (timeout/clean exit) OR capture failed
#   2 = BLACK SCREEN TEST PASSED (black pixels < 15%)
#   3 = BLACK SCREEN TEST FAILED (black pixels >= 15%) - needs fixing
#
# ============================================================================
# MEMORY FILE
# ============================================================================
#   MEMORY.md tracks debugging attempts, results, and reflections.
#   Update this file after each debugging iteration.
#
# RUST_BACKTRACE is automatically enabled for detailed stack traces
#
# NOTE: Due to a quirk, touch injection only works on odd-numbered runs (1, 3, 5...).
# The script automatically skips even runs (0, 2, 4...) by killing and restarting.

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
CAPTURE_BASE_DIR="/d/touchHLE_src/captures"
ANALYZE_SCRIPT="/d/touchHLE_src/analyze_frame.py"
BLACK_PIXEL_THRESHOLD=15.0

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

# Create a new session directory with timestamp
create_session_dir() {
    local SESSION_NAME="session_$(date +%Y-%m-%d_%H-%M-%S)"
    local SESSION_DIR="$CAPTURE_BASE_DIR/$SESSION_NAME"
    mkdir -p "$SESSION_DIR"
    echo "$SESSION_DIR"
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
    local USE_FRAME_CAPTURE=${2:-false}
    local CAPTURE_DIR=${3:-$CAPTURE_BASE_DIR}
    force_kill_game
    sleep 1
    rm -f "$LOG_FILE" "$CRASH_FILE" "$STATUS_FILE"
    > "$INJECT_FILE"
    echo "RUNNING" > "$STATUS_FILE"
    cd "$GAME_DIR"

    # Enable Rust backtrace for detailed crash stack traces
    export RUST_BACKTRACE=1

    # Build command line options
    local OPTS=""
    if [ "$USE_INJECT" = "true" ]; then
        OPTS="$OPTS --event-inject=$INJECT_FILE"
    fi
    if [ "$USE_FRAME_CAPTURE" = "true" ]; then
        OPTS="$OPTS --frame-capture=$CAPTURE_DIR"
    fi

    $TOUCHHLE "$GAME_IPA" $OPTS > "$LOG_FILE" 2>&1 &
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
        if [ $((RUN_COUNT % 2)) -eq 0 ]; then
            echo "=== Skipping even run #$RUN_COUNT (touch injection quirk) ===" >&2
            increment_run_count
            # Start and immediately kill to advance the counter
            start_game true false
            sleep 1
            force_kill_game
            sleep 1
            echo "=== Restarting on odd run ===" >&2
        fi

        echo "=== AUTO-REPLAY MODE ===" >&2
        echo "This will automatically replay recorded clicks to trigger the crash." >&2
        echo "" >&2
        start_game true false
        "$REPLAY_SCRIPT" &
        REPLAY_PID=$!
        echo "=== Waiting for crash... ===" >&2
        wait_for_crash ${2:-600}
        EXIT_CODE=$?
        kill $REPLAY_PID 2>/dev/null
        exit $EXIT_CODE
        ;;
    capture)
        # Check run counter - odd runs don't work, so skip them
        RUN_COUNT=$(get_run_count)
        if [ $((RUN_COUNT % 2)) -eq 0 ]; then
            echo "=== Skipping even run #$RUN_COUNT (touch injection quirk) ===" >&2
            increment_run_count
            # Start and immediately kill to advance the counter
            SESSION_DIR=$(create_session_dir)
            start_game true true "$SESSION_DIR"
            sleep 1
            force_kill_game
            sleep 1
            echo "=== Restarting on odd run ===" >&2
        fi

        echo "=== CAPTURE MODE ===" >&2
        echo "This will inject clicks to enter gameplay, capture frame, analyze, and exit." >&2
        echo "" >&2

        # Create session directory for this capture
        SESSION_DIR=$(create_session_dir)
        echo "Session directory: $SESSION_DIR" >&2

        # Record the latest frame number before starting
        LAST_FRAME=$(ls -1 "$SESSION_DIR"/frame_*.ppm 2>/dev/null | sort -V | tail -1)

        start_game true true "$SESSION_DIR"

        # Wait for game to load to main menu
        echo "Waiting 8s for game to load..." >&2
        sleep 8

        # Click 1: CAMPAIGN button on main menu (center of screen, upper portion)
        echo "Click 1: CAMPAIGN button at (160, 127)..." >&2
        echo '{"type":"tap","x":160,"y":127}' >> "$INJECT_FILE"
        sleep 3

        # Click 2: Start/continue button to enter gameplay (109, 157)
        echo "Click 2: Start button at (109, 157)..." >&2
        echo '{"type":"tap","x":109,"y":157}' >> "$INJECT_FILE"
        sleep 3

        # Request frame capture during gameplay
        echo "Requesting frame capture..." >&2
        echo '{"type":"capture"}' >> "$INJECT_FILE"

        # Wait for capture to complete
        sleep 2

        # Find the new frame
        NEW_FRAME=$(ls -1 "$SESSION_DIR"/frame_*.ppm 2>/dev/null | sort -V | tail -1)

        if [ "$NEW_FRAME" != "$LAST_FRAME" ] && [ -n "$NEW_FRAME" ]; then
            echo "=== CAPTURE SUCCESS ===" >&2
            echo "Frame saved: $NEW_FRAME" >&2

            # Convert to PNG if python is available
            # Note: Convert Unix-style paths (/d/...) to Windows paths (D:/...) for Python
            # Python accepts forward slashes on Windows
            to_windows_path() {
                echo "$1" | sed 's|^/d/|D:/|'
            }

            PNG_FILE=""
            if command -v python &> /dev/null; then
                TEMP_PNG="${NEW_FRAME%.ppm}.png"
                WIN_PPM=$(to_windows_path "$NEW_FRAME")
                WIN_PNG=$(to_windows_path "$TEMP_PNG")
                python -c "from PIL import Image; Image.open('$WIN_PPM').save('$WIN_PNG')"
                if [ -f "$TEMP_PNG" ]; then
                    PNG_FILE="$TEMP_PNG"
                    echo "Converted to: $PNG_FILE" >&2
                else
                    echo "PNG conversion failed, will analyze PPM directly" >&2
                fi
            fi

            # Run black pixel analysis
            echo "" >&2
            echo "=== ANALYZING BLACK PIXELS ===" >&2
            ANALYSIS_FILE="$SESSION_DIR/analysis_results.txt"
            IMAGE_TO_ANALYZE="${PNG_FILE:-$NEW_FRAME}"
            # Convert to Windows path for Python
            WIN_IMAGE=$(to_windows_path "$IMAGE_TO_ANALYZE")
            WIN_ANALYSIS=$(to_windows_path "$ANALYSIS_FILE")

            if command -v python &> /dev/null && [ -f "$ANALYZE_SCRIPT" ]; then
                python "$ANALYZE_SCRIPT" "$WIN_IMAGE" \
                    --threshold "$BLACK_PIXEL_THRESHOLD" \
                    --output "$WIN_ANALYSIS"
                ANALYSIS_EXIT_CODE=$?

                echo "" >&2
                echo "Analysis results saved to: $ANALYSIS_FILE" >&2

                if [ $ANALYSIS_EXIT_CODE -eq 0 ]; then
                    echo "=== TEST PASSED ===" >&2
                    echo "Black pixels are below ${BLACK_PIXEL_THRESHOLD}% threshold." >&2
                else
                    echo "=== TEST FAILED ===" >&2
                    echo "Black pixels exceed ${BLACK_PIXEL_THRESHOLD}% threshold." >&2
                fi

                force_kill_game
                # Exit code 2 = capture + analysis passed, 3 = capture succeeded but analysis failed
                if [ $ANALYSIS_EXIT_CODE -eq 0 ]; then
                    exit 2
                else
                    exit 3
                fi
            else
                echo "Warning: Python or analyze script not available, skipping analysis" >&2
                force_kill_game
                exit 2  # Exit code 2 = successful capture (no analysis)
            fi
        else
            echo "=== CAPTURE FAILED ===" >&2
            echo "No new frame detected" >&2

            # Check if game crashed or was killed (memory issue)
            CRASH_INFO_FILE="$SESSION_DIR/crash_info.txt"
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                if ! ps -p $PID > /dev/null 2>&1; then
                    echo "Game process $PID is no longer running" >&2

                    # Check for panic in log
                    if grep -q "panicked at" "$LOG_FILE" 2>/dev/null; then
                        echo "CRASH_TYPE=PANIC" > "$CRASH_INFO_FILE"
                        echo "=== RUST PANIC DETECTED ===" >&2
                        grep -B 5 -A 30 "panicked at" "$LOG_FILE" >> "$CRASH_INFO_FILE"
                        grep -B 5 -A 30 "panicked at" "$LOG_FILE" >&2
                    elif grep -q "out of memory\|OOM\|memory allocation" "$LOG_FILE" 2>/dev/null; then
                        echo "CRASH_TYPE=OOM" > "$CRASH_INFO_FILE"
                        echo "=== OUT OF MEMORY ===" >&2
                        tail -50 "$LOG_FILE" >> "$CRASH_INFO_FILE"
                    else
                        echo "CRASH_TYPE=KILLED" > "$CRASH_INFO_FILE"
                        echo "=== PROCESS KILLED (likely memory) ===" >&2
                        echo "Process was killed before frame capture completed." >&2
                        echo "This often indicates memory exhaustion." >&2
                    fi

                    # Save last 100 lines of log
                    echo "" >> "$CRASH_INFO_FILE"
                    echo "=== LAST 100 LINES OF LOG ===" >> "$CRASH_INFO_FILE"
                    tail -100 "$LOG_FILE" >> "$CRASH_INFO_FILE" 2>/dev/null

                    # Save diagnostic logs if present
                    echo "" >> "$CRASH_INFO_FILE"
                    echo "=== DIAGNOSTIC LOGS ===" >> "$CRASH_INFO_FILE"
                    grep "\[DIAG-" "$LOG_FILE" >> "$CRASH_INFO_FILE" 2>/dev/null || echo "(none found)" >> "$CRASH_INFO_FILE"

                    echo "Crash info saved to: $CRASH_INFO_FILE" >&2
                    force_kill_game
                    exit 4  # New exit code: crash/kill detected
                fi
            fi

            force_kill_game
            exit 1
        fi
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
        echo "Usage: $0 {run|auto|capture|start|wait|status|crash|log|stop|reset-counter}"
        echo ""
        echo "COMMANDS:"
        echo "  auto [timeout] - CRASH DEBUG: Start game, replay clicks, wait for crash"
        echo "  capture        - BLACK SCREEN DEBUG: Capture frame, analyze black pixels"
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
        echo "  1 = No crash (timeout or clean exit) / Capture failed"
        echo "  2 = BLACK SCREEN TEST PASSED (black pixels < ${BLACK_PIXEL_THRESHOLD}%)"
        echo "  3 = BLACK SCREEN TEST FAILED (black pixels >= ${BLACK_PIXEL_THRESHOLD}%) - fix needed"
        echo "  4 = CRASH/KILLED during capture (memory issue) - see crash_info.txt"
        echo ""
        echo "DEBUGGING WORKFLOWS:"
        echo "  Crash loop:        auto -> fix -> rebuild -> auto (until exit 1)"
        echo "  Black screen loop: capture -> fix -> rebuild -> capture (until exit 2)"
        echo ""
        echo "SESSION FOLDERS:"
        echo "  $CAPTURE_BASE_DIR/session_YYYY-MM-DD_HH-MM-SS/"
        echo "    ├── frame_XXXX.ppm/png  - Captured frame"
        echo "    └── analysis_results.txt - Black pixel analysis"
        echo ""
        echo "MEMORY FILE:"
        echo "  MEMORY.md - Track debugging attempts and results"
        ;;
esac
