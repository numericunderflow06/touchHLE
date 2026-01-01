#!/bin/bash
# Build monitor script for touchHLE development
# Usage:
#   ./build_monitor.sh start   - Start a build in background
#   ./build_monitor.sh status  - Check if build is running/complete
#   ./build_monitor.sh output  - Get build output
#   ./build_monitor.sh wait    - Wait for build to complete (blocks)

BUILD_DIR="/d/touchHLE_src"
BUILD_LOG="$BUILD_DIR/build_output.log"
BUILD_PID_FILE="$BUILD_DIR/.build_pid"
BUILD_STATUS_FILE="$BUILD_DIR/.build_status"

cd "$BUILD_DIR"

case "$1" in
    start)
        # Kill any existing build
        if [ -f "$BUILD_PID_FILE" ]; then
            OLD_PID=$(cat "$BUILD_PID_FILE")
            kill $OLD_PID 2>/dev/null
        fi

        # Clear previous status
        rm -f "$BUILD_STATUS_FILE"
        echo "RUNNING" > "$BUILD_STATUS_FILE"

        # Start build in background
        export PATH="/c/Users/cs06t/.cargo/bin:$PATH"
        (
            cargo build --release -j 2 > "$BUILD_LOG" 2>&1
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 0 ]; then
                echo "SUCCESS" > "$BUILD_STATUS_FILE"
                # Reset run counter on successful build
                echo "0" > /tmp/touchhle_run_counter
            else
                echo "FAILED:$EXIT_CODE" > "$BUILD_STATUS_FILE"
            fi
        ) &

        echo $! > "$BUILD_PID_FILE"
        echo "Build started with PID $(cat $BUILD_PID_FILE)"
        ;;

    status)
        if [ ! -f "$BUILD_STATUS_FILE" ]; then
            echo "NO_BUILD"
            exit 0
        fi

        STATUS=$(cat "$BUILD_STATUS_FILE")

        if [ "$STATUS" = "RUNNING" ]; then
            # Check if process is still running
            if [ -f "$BUILD_PID_FILE" ]; then
                PID=$(cat "$BUILD_PID_FILE")
                if ps -p $PID > /dev/null 2>&1; then
                    echo "RUNNING"
                else
                    # Process ended but status not updated yet
                    echo "CHECKING"
                fi
            else
                echo "RUNNING"
            fi
        else
            echo "$STATUS"
        fi
        ;;

    output)
        if [ -f "$BUILD_LOG" ]; then
            cat "$BUILD_LOG"
        else
            echo "No build output available"
        fi
        ;;

    tail)
        if [ -f "$BUILD_LOG" ]; then
            tail -50 "$BUILD_LOG"
        else
            echo "No build output available"
        fi
        ;;

    wait)
        echo "Waiting for build to complete..."
        while true; do
            if [ -f "$BUILD_STATUS_FILE" ]; then
                STATUS=$(cat "$BUILD_STATUS_FILE")
                if [ "$STATUS" != "RUNNING" ]; then
                    echo "Build finished: $STATUS"
                    break
                fi
            fi
            sleep 2
        done
        ;;

    *)
        echo "Usage: $0 {start|status|output|tail|wait}"
        exit 1
        ;;
esac
