# touchHLE Build Setup Guide

This document describes how to reproduce the build environment for this modified version of touchHLE (with Avatar of War: The Dark Lord support).

---

## Current Environment Versions (December 2025)

### Core Tools

| Component | Version | Notes |
|-----------|---------|-------|
| **Rust** | 1.92.0 (ded5c06cf 2025-12-08) | `rustup update stable` |
| **Cargo** | 1.92.0 (344c4567c 2025-10-21) | Comes with Rust |
| **CMake** | 4.2.1 | CI uses 3.31.6, but newer works |
| **Git** | 2.49.0.windows.1 | Any recent version |
| **MSVC** | 14.29.30133 (VS 2019 Build Tools) | Visual Studio 2019 or 2022 |

### Operating System

| Component | Version |
|-----------|---------|
| **Windows** | 10.0.26100 (Windows 11) |
| **Shell** | MINGW64/Git Bash |

### Repository State

| Component | Version/Commit |
|-----------|----------------|
| **touchHLE fork** | `c5e0eff4` (v0.2.2-1022-gc5e0eff4) |
| **Base upstream** | touchHLE v0.2.2 |
| **Local commits** | 9 commits ahead of upstream |

### Git Submodules

| Submodule | Commit | Tag/Version |
|-----------|--------|-------------|
| **vendor/SDL** | `07d0f51fa292895443f563f0cbde4cb3802d87fa` | release-2.26.4 |
| **vendor/dynarmic** | `76aa4dd665085fb6ac10d4cd58e25466366d0799` | 76aa4dd6 |
| **vendor/openal-soft** | `23c8a35505fe6ab7a5c87754911a133b23ac75cf` | 1.22.2-234-g23c8a3550 |
| **vendor/stb** | `9f1776a36d2a3d63c52f705c3a84b372cfed4340` | 9f1776a |

### External Dependencies (NOT in Git)

| Component | Version | Download Size |
|-----------|---------|---------------|
| **Boost** | 1.87.0 | ~220 MB (zip) |

---

## Step-by-Step Build Instructions (Windows)

### Prerequisites

1. **Install Rust**: https://www.rust-lang.org/tools/install
   ```powershell
   # After install, verify:
   rustc --version   # Should show 1.92.0 or later
   cargo --version
   ```

2. **Install Visual Studio Build Tools** (or full Visual Studio):
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Select "Desktop development with C++" workload
   - Ensure MSVC v142 or v143 is installed

3. **Install CMake**: https://cmake.org/download/
   - Add to PATH during installation
   ```powershell
   cmake --version   # Should show 3.12 or later
   ```

4. **Install Git**: https://git-scm.com/download/win
   - Use Git Bash for the following commands

### Clone and Setup

```bash
# 1. Clone the repository
git clone https://github.com/numericunderflow06/touchHLE.git
cd touchHLE

# 2. Initialize git submodules (REQUIRED)
git submodule update --init

# 3. Verify submodules are checked out
ls vendor/dynarmic/src    # Should exist
ls vendor/SDL/src         # Should exist
ls vendor/openal-soft/al  # Should exist
ls vendor/stb             # Should have stb_image.h
```

### Download and Install Boost (CRITICAL)

Boost is NOT included in the repository and must be downloaded manually.

**Option A: Using the exact version I'm using (1.87.0)**

```bash
# Download Boost 1.87.0
curl -L -o boost_1_87_0.zip "https://archives.boost.io/release/1.87.0/source/boost_1_87_0.zip"

# Extract to vendor directory
# On Windows with 7-Zip:
7z x -ovendor boost_1_87_0.zip

# Rename to expected location
mv vendor/boost_1_87_0 vendor/boost

# Verify structure - this path MUST exist:
ls vendor/boost/boost/version.hpp
```

**Option B: Using CI version (1.81.0)**

```bash
# Download Boost 1.81.0 (smaller, used by CI)
curl -L -o boost_1_81_0.7z "https://archives.boost.io/release/1.81.0/source/boost_1_81_0.7z"

# Extract
7z x -ovendor boost_1_81_0.7z
mv vendor/boost_1_81_0 vendor/boost

# Verify
ls vendor/boost/boost/version.hpp
```

**Expected Boost directory structure:**
```
vendor/
  boost/
    boost/           <-- Headers go here
      algorithm/
      any.hpp
      version.hpp
      ...
    libs/            <-- Library sources (not all needed)
    ...
```

### Build

```bash
# From Developer Command Prompt or with MSVC in PATH:

# Debug build (faster compile, slower runtime)
cargo build

# Release build (slower compile, optimized runtime)
cargo build --release

# The executable will be at:
# Debug:   target/debug/touchHLE.exe
# Release: target/release/touchHLE.exe
```

### Verify Build

```bash
# Run with --help to verify it works
./target/release/touchHLE.exe --help

# Run the app picker
./target/release/touchHLE.exe
```

---

## Runtime Requirements

These directories must be present alongside the executable (or in working directory):

| Directory | Contents | In Git? |
|-----------|----------|---------|
| `touchHLE_dylibs/` | libgcc_s.1.dylib, libstdc++.6.0.9.dylib, libz.1.2.3.dylib | Yes |
| `touchHLE_fonts/` | Liberation*.ttf, NotoSansJP*.otf | Yes |
| `touchHLE_apps/` | Your .ipa files | No (user-provided) |
| `touchHLE_sandbox/` | Save data (created automatically) | No |

---

## Troubleshooting

### "Could not find Boost" error
```
Could not find Boost. Download it from https://www.boost.org/users/download/
and put it at vendor/boost
```
**Solution:** Follow the Boost installation steps above. Ensure `vendor/boost/boost/version.hpp` exists.

### CMake not found
```
error: failed to run custom build command for `touchHLE_dynarmic_wrapper`
```
**Solution:** Install CMake and ensure it's in PATH, or set the `CMAKE` environment variable:
```bash
export CMAKE="/path/to/cmake"
cargo build --release
```

### CMake 4.x compatibility error
```
CMake Error at externals/robin-map/CMakeLists.txt:1 (cmake_minimum_required):
  Compatibility with CMake < 3.5 has been removed from CMake.
```
**Solution:** CMake 4.x removed support for older cmake_minimum_required versions. Set this environment variable:
```bash
export CMAKE_POLICY_VERSION_MINIMUM=3.5
cargo build --release
```

### MSVC linker errors
**Solution:** Run from "Developer Command Prompt for VS 2019/2022" or ensure `cl.exe` is in PATH.

### Submodule directories empty
```bash
# If vendor/dynarmic is empty:
git submodule update --init --recursive
```

---

## Development Scripts

These helper scripts are used for debugging but are NOT required for building:

| Script | Purpose |
|--------|---------|
| `build_monitor.sh` | Background build with status monitoring |
| `crash_monitor.sh` | Run game and capture crash details |
| `auto_replay.sh` | Automated click replay for testing |

Usage:
```bash
# Build with monitoring
./build_monitor.sh start && ./build_monitor.sh wait

# Test with crash capture
./crash_monitor.sh run
```

---

## Differences from Upstream touchHLE

This fork includes modifications to support "Avatar of War: The Dark Lord":

- Objective-C blocks runtime support
- GCD (Grand Central Dispatch) stubs
- NSOperationQueue implementation
- Additional framework stubs (MapKit, Security, CoreAudio, CFNetwork, AddressBook)
- SQLite stubs
- Various bug fixes for serialization and UTF-8 handling

See `CLAUDE.md` for detailed modification history.

---

## Quick Reference

```bash
# Full setup from scratch (copy-paste ready):
git clone https://github.com/numericunderflow06/touchHLE.git
cd touchHLE
git submodule update --init
curl -L -o boost.zip "https://archives.boost.io/release/1.87.0/source/boost_1_87_0.zip"
7z x -ovendor boost.zip && mv vendor/boost_1_87_0 vendor/boost
cargo build --release
./target/release/touchHLE.exe --help
```

---

## Version History

| Date | Change |
|------|--------|
| 2025-12-28 | Initial SETUP.md created |
