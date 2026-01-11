# Automation Framework Findings

**Date**: 2026-01-11
**Purpose**: Document key findings about the automation framework's capabilities and gaps

---

## 1. Diagnostic Logging System

### Documentation Location
- Primary: `dev-docs/debugging.md`
- Implementation: `src/log.rs`

### Available Logging Macros

| Macro | Always Prints | Use Case |
|-------|---------------|----------|
| `log!()` | Yes | Errors, warnings, important events |
| `log_dbg!()` | Only if module enabled | Verbose debugging output |
| `log_once!()` | Once per session | Per-frame spam prevention |
| `echo!()` | Yes | General touchHLE output |

### Module-Level Debug Logging

To enable `log_dbg!()` for a module, add it to `src/log.rs:96-100`:

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::frameworks::opengles::gles_guest",
    "touchHLE::frameworks::opengles::eagl",
    "touchHLE::frameworks::core_animation::composition",
    // Add modules here to enable log_dbg!() output
];
```

### Recommended Modules for Debugging

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::abi` | Guest-to-host ABI calls |
| `touchHLE::dyld` | Dynamic linking operations |
| `touchHLE::mem` | Memory allocations/deallocations |
| `touchHLE::frameworks::opengles::gles_guest` | OpenGL ES API calls |
| `touchHLE::frameworks::opengles::eagl` | EAGL context operations |
| `touchHLE::frameworks::core_animation::composition` | Layer compositing |

### Output Destinations

| Destination | Platform | Notes |
|-------------|----------|-------|
| stderr | All | Console output |
| `touchHLE_log.txt` | All | User data directory |
| logcat | Android | Via SDL2 |
| `/tmp/touchhle_game.log` | Automation | Captured by crash_monitor.sh |

### Diagnostic Prefix Convention

The automation framework uses `[DIAG-*]` prefixes for hypothesis testing:

| Prefix | Hypothesis | Location |
|--------|------------|----------|
| `[DIAG-H1]` | decodeBytesForKey | ns_keyed_unarchiver.rs |
| `[DIAG-H2]` | Missing NSCoder keys | ns_keyed_unarchiver.rs |
| `[DIAG-H3]` | File loading via Foundation | ns_bundle.rs, ns_data.rs |
| `[DIAG-DEV]` | Device model queries | ui_device.rs, ui_screen.rs |

Filter in logs: `grep "\[DIAG-" /tmp/touchhle_game.log`

---

## 2. Git History Mining

### Current Scope: LOCAL ONLY

The automation framework currently only mines:
- Local git log in this repository
- Commit messages and code changes
- NO external sources are searched

### Configured Remotes

```
origin    https://github.com/numericunderflow06/touchHLE.git  (fork)
upstream  https://github.com/touchHLE/touchHLE.git           (official)
```

### Search Strategy Status (from STRATEGY_MEMORY.json)

| Strategy | Times Tried | Notes |
|----------|-------------|-------|
| `github_issues_search` | 0 | Never executed |
| `opengl_forums` | 0 | Never executed |
| `touchhle_upstream` | 0 | Never executed |

### Gap: External Sources Not Used

The automation framework has prompts that mention searching:
- Upstream touchHLE issues/PRs
- GitHub issues generally
- OpenGL/graphics forums
- Stack Overflow

**BUT** none of these have actually been executed (`times_tried: 0` for all).

### Potential External Sources

| Source | URL | Potential Value |
|--------|-----|-----------------|
| Upstream Issues | github.com/touchHLE/touchHLE/issues | Similar game bugs |
| Upstream PRs | github.com/touchHLE/touchHLE/pulls | Related fixes |
| OpenGL Forums | opengl.org/discussion_boards | ES 1.1 translation tips |
| Stack Overflow | stackoverflow.com/questions/tagged/opengl-es | Common rendering issues |
| PPSSPP | github.com/hrydgard/ppsspp | Reference GL implementation |
| Dolphin | github.com/dolphin-emu/dolphin | Reference GL implementation |

---

## 3. Other Debugging Tools

### Command-Line Flags

| Flag | Purpose |
|------|---------|
| `--dump=linking-info` | Dump classes, selectors, lazy symbols |
| `--dump-file=PATH` | Output file for dump (default: DUMP.txt) |
| `--gdb=HOST:PORT` | Start GDB remote debugging server |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `RUST_BACKTRACE=1` | Detailed panic stack traces |
| `CMAKE_POLICY_VERSION_MINIMUM=3.5` | CMake 4.x compatibility |

### External Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| apitrace | OpenGL call tracing | Invaluable for GL issues |
| Ghidra | Binary reverse engineering | For understanding game code |
| GDB (ARM) | Remote debugging | Connect via --gdb flag |

### Debug Functions (`src/debug.rs`)

Functions for dumping image/pixel data to files:
- Raw pixel data can be written to `.data` files
- GIMP can read raw pixel data

---

## 4. Recommendations

### Immediate Opportunities

1. **Enable upstream searching**: Actually execute the planned searches
2. **Check upstream PRs**: Look for glMaterial, viewport, rendering fixes
3. **Search OpenGL forums**: ES 1.1 to GL 2.1 translation issues

### Diagnostic Improvements

1. **Add DIAG-LIBC prefix**: For C stdlib file operations (fopen, fread)
2. **Enable more modules**: Add `touchHLE::libc::stdio` to ENABLED_MODULES
3. **Use --dump=linking-info**: Check what APIs the game requests

### Infrastructure Improvements

1. **Implement GitHub data fetcher**: Collect issues/PRs from upstream
2. **Create search execution system**: Actually run the planned searches
3. **Track search results**: Store useful findings for future reference
