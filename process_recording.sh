#!/bin/bash
# Process recorded events into a replay script

INPUT="/d/touchHLE_src/recorded_events.json"
OUTPUT="/d/touchHLE_src/replay_sequence.sh"

echo "#!/bin/bash" > "$OUTPUT"
echo "# Auto-generated replay sequence" >> "$OUTPUT"
echo "# Recorded on $(date)" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo 'INJECT_FILE="/d/touchHLE_src/inject.json"' >> "$OUTPUT"
echo '> "$INJECT_FILE"' >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "echo 'Starting replay sequence...'" >> "$OUTPUT"
echo "sleep 5  # Wait for game to load" >> "$OUTPUT"
echo "" >> "$OUTPUT"

PREV_TS=0
CLICK_NUM=0

# Extract touch_down events
grep '"type":"touch_down"' "$INPUT" | while read line; do
    TS=$(echo "$line" | grep -o '"ts":[0-9]*' | cut -d: -f2)
    X=$(echo "$line" | grep -o '"x":[0-9.]*' | cut -d: -f2)
    Y=$(echo "$line" | grep -o '"y":[0-9.]*' | cut -d: -f2)
    
    CLICK_NUM=$((CLICK_NUM + 1))
    
    if [ $PREV_TS -ne 0 ]; then
        DELAY_MS=$((TS - PREV_TS))
        DELAY_S=$(echo "scale=3; $DELAY_MS / 1000" | bc)
        echo "sleep $DELAY_S" >> "$OUTPUT"
    fi
    
    echo "echo 'Click $CLICK_NUM: ($X, $Y)'" >> "$OUTPUT"
    echo "echo '{\"type\":\"tap\",\"x\":$X,\"y\":$Y}' >> \"\$INJECT_FILE\"" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    
    PREV_TS=$TS
done

echo "echo 'Replay complete.'" >> "$OUTPUT"
chmod +x "$OUTPUT"
echo "Created $OUTPUT"
