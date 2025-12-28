#!/bin/bash
# Auto-generated replay sequence - with longer delays for game transitions

INJECT_FILE="/d/touchHLE_src/inject.json"
> "$INJECT_FILE"

echo "Starting replay sequence (with extended delays)..."
sleep 8  # Wait for game to fully load

# Click 1: (118, 160) - Start button
echo 'Click 1: (118, 160)'
echo '{"type":"tap","x":118,"y":160}' >> "$INJECT_FILE"
sleep 10  # Wait for menu transition

# Click 2: (79, 162) 
echo 'Click 2: (79, 162)'
echo '{"type":"tap","x":79,"y":162}' >> "$INJECT_FILE"
sleep 12  # Extended wait for next screen to load

# Click 3: (31, 103)
echo 'Click 3: (31, 103)'
echo '{"type":"tap","x":31,"y":103}' >> "$INJECT_FILE"
sleep 6

# Click 4: (87, 255)
echo 'Click 4: (87, 255)'
echo '{"type":"tap","x":87,"y":255}' >> "$INJECT_FILE"
sleep 6

# Click 5-11: (172, 288) - multiple clicks
for i in 5 6 7 8 9 10 11; do
    echo "Click $i: (172, 288)"
    echo '{"type":"tap","x":172,"y":288}' >> "$INJECT_FILE"
    sleep 3
done

# Click 12: (29, 15) - near top
echo 'Click 12: (29, 15)'
echo '{"type":"tap","x":29,"y":15}' >> "$INJECT_FILE"
sleep 2

# Click 13: (184, 74) - CRASH TRIGGER
echo 'Click 13: (184, 74) - CRASH TRIGGER'
echo '{"type":"tap","x":184,"y":74}' >> "$INJECT_FILE"

echo "Replay complete. Crash should occur shortly..."
