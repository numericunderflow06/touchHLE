#!/bin/bash
# 3-click replay sequence for frame capture debugging
# This script executes only 3 clicks, waits 5 seconds, then requests frame capture
# Used to debug screen truncation / black screen issues

INJECT_FILE="/d/touchHLE_src/inject.json"
> "$INJECT_FILE"

echo "Starting 3-click replay sequence for frame capture..."
sleep 8  # Wait for game to fully load

# Click 1: (109, 157) - Start button
echo 'Click 1: (109, 157)'
echo '{"type":"tap","x":109,"y":157}' >> "$INJECT_FILE"
sleep 5.757  # Exact delay from recording

# Click 2: (81, 166)
echo 'Click 2: (81, 166)'
echo '{"type":"tap","x":81,"y":166}' >> "$INJECT_FILE"
sleep 6.408

# Click 3: (35, 111)
echo 'Click 3: (35, 111)'
echo '{"type":"tap","x":35,"y":111}' >> "$INJECT_FILE"

echo "3 clicks complete. Waiting 5 seconds before capture..."
sleep 5

# Request frame capture
echo 'Requesting frame capture...'
echo '{"type":"capture"}' >> "$INJECT_FILE"

echo "Frame capture requested. Script complete."
