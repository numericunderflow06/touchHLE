#!/bin/bash
# TouchHLE Automated Research Pipeline Runner
#
# Usage: ./run.sh [--reset]
#   --reset: Clear persistent memory and start fresh

cd "$(dirname "$0")"

# Handle reset flag
if [[ "$1" == "--reset" ]]; then
    echo "Resetting persistent memory..."
    rm -f PERSISTENT_MEMORY.md
    rm -rf sessions/*
    echo "Reset complete."
fi

echo "========================================"
echo "  TouchHLE Automation Pipeline"
echo "========================================"
echo ""
echo "Configuration:"
echo "  - Model: Claude Opus 4.5"
echo "  - Claude Code: v2.1.2"
echo "  - Working Dir: D:/touchHLE_src"
echo "  - Max Retries: 20"
echo ""
echo "Press Ctrl+C to stop at any time."
echo ""

# Run the Python automation runner
python automation_runner.py

exit_code=$?
echo ""
echo "Pipeline exited with code: $exit_code"
exit $exit_code
