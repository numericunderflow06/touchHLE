# TouchHLE Automated Research Pipeline

An automated debugging pipeline that uses Claude Code (Opus 4.5) to iteratively fix the screen truncation issue in touchHLE.

## Features

- **Model**: Claude Opus 4.5 via Claude Code v2.1.2
- **Persistent Memory**: Carries findings across sessions
- **Automatic Pass/Fail**: Uses `crash_monitor.sh capture` exit codes
- **Auto-Retry**: Re-prompts on failure with context
- **Session Timeout**: 30 minute limit per Claude session

## Directory Structure

```
automation_framework/
├── automation_runner.py    # Main automation script
├── run.sh / run.bat        # Runner scripts
├── prompts/
│   ├── initial.md          # Initial debugging prompt
│   ├── retry.md            # Retry prompt template
│   └── memory_update.md    # Memory update prompt
├── sessions/               # Session logs and outputs
│   └── session_YYYY-MM-DD_HH-MM-SS_NNN/
│       ├── prompt.md       # Full prompt sent to Claude
│       ├── output.log      # Claude's complete output
│       └── metadata.json   # Session metadata (exit code, timing)
└── PERSISTENT_MEMORY.md    # Cross-session memory file (accumulated findings)
```

## Session Logs Location

All session logs are stored in:
```
D:\touchHLE_src\automation_framework\sessions\
```

Each session creates a directory named `session_YYYY-MM-DD_HH-MM-SS_NNN` containing:
- **prompt.md**: The full prompt sent to Claude (includes memory context)
- **output.log**: Claude's complete response (created when session completes)
- **metadata.json**: Session metadata including exit code, output length, timestamp

## Usage

```bash
# Run the automation
cd D:/touchHLE_src/automation_framework
python automation_runner.py

# Or use the runner scripts:
./run.sh           # Linux/Mac
run.bat            # Windows

# Reset and start fresh:
./run.sh --reset
```

## How It Works

1. **Initial Test**: Runs `./crash_monitor.sh capture` to get baseline
2. **Claude Session**: Sends debugging prompt to Claude Code (Opus 4.5)
3. **Post-Session Test**: Checks if the issue is fixed
4. **Memory Update**: Extracts findings and saves to persistent memory
5. **Retry Loop**: If test fails, retries with updated context

## Exit Codes

- `0`: Success (test passed, < 15% black pixels)
- `1`: Failure (max retries reached)
- `130`: Interrupted by user

## Configuration

Edit `CONFIG` in `automation_runner.py`:

```python
CONFIG = {
    "model": "opus",                    # Claude model
    "session_timeout_seconds": 1800,    # 30 min per session
    "retry_delay_seconds": 10,          # Delay between retries
    "max_retries": 20,                  # Maximum retry attempts
    "pass_exit_code": 2,                # crash_monitor.sh PASS
    "fail_exit_code": 3,                # crash_monitor.sh FAIL
}
```

## Current Status

**Implementation**: Complete
**Testing**: Partially tested - Claude Code sessions run but take 10+ minutes with Opus model

### Known Issues

1. **Initial test returns exit code 1**: The `crash_monitor.sh capture` may need specific environment setup (e.g., game IPA, display server for graphical capture)

2. **Long session times**: Claude Opus 4.5 with complex prompts takes significant time to process

### Next Steps

- Consider reducing initial prompt complexity
- Add streaming output for real-time progress monitoring
- Add proper cleanup for interrupted sessions
