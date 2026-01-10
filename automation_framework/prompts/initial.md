# TouchHLE Screen Truncation Debugging Task

You are debugging a screen truncation issue in the touchHLE iOS emulator running "Avatar of War: The Dark Lord".

## Problem Summary

The game renders with the bottom ~1/3 of the screen completely black. The target is to reduce black pixels to below 15%. Current state is ~42% black pixels.

## Your Workflow

**IMPORTANT**: Use the monitor scripts for all operations. They handle async notifications automatically.

### 1. Understand the Current State

First, read the key documentation:
- `MEMORY.md` - Contains debugging history and what has been tried
- `CLAUDE.md` - Contains project info and workflow instructions
- Check `captures/` for recent frame captures

### 2. Investigation and Fix Cycle

```bash
# Test current state (runs automatically, ~20 seconds)
./crash_monitor.sh capture

# If exit code 3 (FAIL):
# 1. Read the captured PNG: captures/session_*/frame_*.png
# 2. Check analysis_results.txt for black pixel percentage
# 3. Investigate the issue
# 4. Make a fix

# Build (blocks until complete)
./build_monitor.sh start && ./build_monitor.sh wait

# Test again
./crash_monitor.sh capture
```

### 3. Key Insights from Previous Sessions

- **Root cause identified**: Frustum clipping in glFrustumf
- The ground content EXISTS but is being clipped out of view
- Adjusting frustum parameters has shown improvement
- File to modify: `src/gles/gles1_on_gl2.rs`

### 4. Documentation

After each significant finding or fix attempt, update `MEMORY.md` with:
- What you tried
- The result (black pixel percentage)
- Analysis and next steps

## Success Criteria

The test passes (exit code 2) when black pixels are below 15%.

## Important Notes

1. The monitors handle all async waiting - just run the commands and they block until complete
2. Touch injection only works on ODD-numbered runs - the scripts handle this automatically
3. ALWAYS use `./crash_monitor.sh capture` for testing, NEVER run touchHLE directly
4. Read the captured frame visually to understand what's rendering

Start by reading MEMORY.md and CLAUDE.md, then run a capture test to see the current state.
