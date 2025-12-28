#!/bin/bash
# Auto-replay script for Avatar of War debugging
# Automatically injects clicks to reach the crash point

INJECT_FILE="/d/touchHLE_src/inject.json"

# Clear the inject file
> "$INJECT_FILE"

echo "Starting auto-replay sequence to reach crash point..." >&2
echo "The sequence will:" >&2
echo "  1. Wait for game to load (8s)" >&2
echo "  2. Click through menus to trigger crash" >&2
echo "" >&2

# Wait for game to initialize
sleep 8

# Click sequence from AUTOMATION_ARCHITECTURE.md
# Click 1: Start button at (117, 162)
echo '{"type":"tap","x":117,"y":162}' >> "$INJECT_FILE"
echo "Click 1: Tap at (117, 162) - Start button" >&2
sleep 8.5

# Click 2: Menu option at (80, 164)
echo '{"type":"tap","x":80,"y":164}' >> "$INJECT_FILE"
echo "Click 2: Tap at (80, 164) - Menu option" >&2
sleep 7.5

# Click 3: Another option at (29, 107)
echo '{"type":"tap","x":29,"y":107}' >> "$INJECT_FILE"
echo "Click 3: Tap at (29, 107) - Another option" >&2
sleep 3.5

# Click 4: This triggers the crash at (101, 255)
echo '{"type":"tap","x":101,"y":255}' >> "$INJECT_FILE"
echo "Click 4: Tap at (101, 255) - CRASH TRIGGER" >&2

echo "" >&2
echo "Replay sequence complete. Waiting for crash..." >&2
