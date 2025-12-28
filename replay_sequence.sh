#!/bin/bash
# Auto-generated replay sequence from recorded_events.json
# Generated with exact time intervals from user recording

INJECT_FILE="/d/touchHLE_src/inject.json"
> "$INJECT_FILE"

echo "Starting replay sequence (exact timing from recording)..."
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
sleep 3.128

# Click 4: (98, 260)
echo 'Click 4: (98, 260)'
echo '{"type":"tap","x":98,"y":260}' >> "$INJECT_FILE"
sleep 5.256

# Click 5: (168, 292)
echo 'Click 5: (168, 292)'
echo '{"type":"tap","x":168,"y":292}' >> "$INJECT_FILE"
sleep 2.094

# Click 6: (172, 287)
echo 'Click 6: (172, 287)'
echo '{"type":"tap","x":172,"y":287}' >> "$INJECT_FILE"
sleep 2.180

# Click 7: (170, 283)
echo 'Click 7: (170, 283)'
echo '{"type":"tap","x":170,"y":283}' >> "$INJECT_FILE"
sleep 2.045

# Click 8: (170, 283)
echo 'Click 8: (170, 283)'
echo '{"type":"tap","x":170,"y":283}' >> "$INJECT_FILE"
sleep 1.764

# Click 9: (29, 10)
echo 'Click 9: (29, 10)'
echo '{"type":"tap","x":29,"y":10}' >> "$INJECT_FILE"
sleep 1.634

# Click 10: (204, 70)
echo 'Click 10: (204, 70)'
echo '{"type":"tap","x":204,"y":70}' >> "$INJECT_FILE"
sleep 1.116

# Click 11: (178, 281)
echo 'Click 11: (178, 281)'
echo '{"type":"tap","x":178,"y":281}' >> "$INJECT_FILE"
sleep 2.103

# Click 12: (174, 281)
echo 'Click 12: (174, 281)'
echo '{"type":"tap","x":174,"y":281}' >> "$INJECT_FILE"
sleep 2.335

# Click 13: (170, 272)
echo 'Click 13: (170, 272)'
echo '{"type":"tap","x":170,"y":272}' >> "$INJECT_FILE"
sleep 2.199

# Click 14: (172, 277)
echo 'Click 14: (172, 277)'
echo '{"type":"tap","x":172,"y":277}' >> "$INJECT_FILE"
sleep 39.968  # Long wait from recording

# Click 15: (167, 290) - Final click
echo 'Click 15: (167, 290) - FINAL'
echo '{"type":"tap","x":167,"y":290}' >> "$INJECT_FILE"

echo "Replay complete. Waiting for result..."
