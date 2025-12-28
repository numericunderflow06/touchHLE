#!/bin/bash
# Click recorder for touchHLE debugging
# Records mouse clicks with timestamps for replay

RECORD_FILE="/d/touchHLE_src/recorded_clicks.txt"
GAME_WINDOW="Dark Lord"

record_clicks() {
    echo "=== Click Recorder ===" >&2
    echo "Recording clicks. Press Ctrl+C to stop." >&2
    echo "Click inside the touchHLE window to record." >&2
    echo "" > "$RECORD_FILE"
    
    START_TIME=$(date +%s%3N)
    
    # Use xdotool to monitor clicks (via xinput on Windows/MSYS2)
    # For Windows, we'll use a different approach with PowerShell
    
    # Record format: timestamp_ms,x,y,action (down/up)
    echo "# Click recording started at $(date)" >> "$RECORD_FILE"
    echo "# Format: relative_time_ms,x,y,action" >> "$RECORD_FILE"
    
    while true; do
        # This will be replaced with actual recording logic
        read -p "Press Enter after each click (or 'q' to quit): " input
        if [ "$input" = "q" ]; then
            break
        fi
        CURRENT_TIME=$(date +%s%3N)
        RELATIVE_TIME=$((CURRENT_TIME - START_TIME))
        echo "Click recorded at ${RELATIVE_TIME}ms" >&2
    done
    
    echo "Recording saved to $RECORD_FILE" >&2
}

case "$1" in
    record)
        record_clicks
        ;;
    show)
        cat "$RECORD_FILE"
        ;;
    *)
        echo "Usage: $0 {record|show}"
        ;;
esac
