#!/bin/bash
# General task monitor - runs any command and provides instant status checks
# Usage:
#   ./task_monitor.sh run "command here"  - Run command in background
#   ./task_monitor.sh status              - Instant status check (non-blocking)
#   ./task_monitor.sh output              - Get output so far
#   ./task_monitor.sh wait                - Block until complete

TASK_LOG="/tmp/task_monitor.log"
TASK_PID="/tmp/task_monitor.pid"
TASK_STATUS="/tmp/task_monitor.status"
TASK_CMD="/tmp/task_monitor.cmd"

case "$1" in
    run)
        shift
        CMD="$*"

        # Kill previous task if running
        [ -f "$TASK_PID" ] && kill $(cat "$TASK_PID") 2>/dev/null

        # Clear files
        echo "RUNNING" > "$TASK_STATUS"
        echo "$CMD" > "$TASK_CMD"
        > "$TASK_LOG"

        # Run in background
        (
            eval "$CMD" > "$TASK_LOG" 2>&1
            EC=$?
            if [ $EC -eq 0 ]; then
                echo "SUCCESS" > "$TASK_STATUS"
            else
                echo "FAILED:$EC" > "$TASK_STATUS"
            fi
        ) &

        echo $! > "$TASK_PID"
        echo "Task started (PID: $!): $CMD"
        ;;

    status)
        if [ ! -f "$TASK_STATUS" ]; then
            echo "NO_TASK"
        else
            cat "$TASK_STATUS"
        fi
        ;;

    output)
        [ -f "$TASK_LOG" ] && cat "$TASK_LOG" || echo "No output"
        ;;

    tail)
        [ -f "$TASK_LOG" ] && tail -30 "$TASK_LOG" || echo "No output"
        ;;

    wait)
        while [ "$(cat "$TASK_STATUS" 2>/dev/null)" = "RUNNING" ]; do
            sleep 1
        done
        cat "$TASK_STATUS"
        ;;

    *)
        echo "Usage: $0 {run|status|output|tail|wait} [command]"
        ;;
esac
