# TouchHLE Debugging Memory

## Quick Reference

- **Problem**: Screen truncation - bottom ~40% of screen is black
- **Current**: 42.22% black pixels
- **Target**: < 15% black pixels
- **Test**: `./crash_monitor.sh capture` (exit 2 = PASS, exit 3 = FAIL)

---

## Latest Sessions (newest first)

### Session: research_2026-01-10_14-13 (Manual) - BREAKTHROUGH
**Date**: 2026-01-10 | **Result**: DIAGNOSTIC SUCCESS (42.22% black)
**Key Finding**: PNG textures NOT loaded via Foundation APIs - game likely uses C stdlib (fopen/fread)
**Diagnostics**: H1 REFUTED (0 decodeBytesForKey calls), H3 PARTIALLY REFUTED (.def loaded, .png not)
**See**: Detailed notes in Historical Details section below

---

### Session: research_2026-01-10_13-43-50
**Date**: 2026-01-10 | **Result**: BUILD FAILED (exit -1)
**Issue**: Third consecutive infrastructure failure
**See**: `automation_framework/sessions/research_2026-01-10_13-43-50/`

---

### Session: research_2026-01-10_13-16-02
**Date**: 2026-01-10 | **Result**: INFRASTRUCTURE FAILURE
**Issue**: Build monitor returned stale status
**See**: `automation_framework/sessions/research_2026-01-10_13-16-02/`

---

### Session: research_2026-01-10_12-35-40
**Date**: 2026-01-10 | **Result**: BUILD FAILED (linker error 0xc0000142)
**Attempted**: Add decodeBytesForKey + diagnostic logging
**See**: `automation_framework/sessions/research_2026-01-10_12-35-40/`

---

### Session: 2026-01-01_19-39-58
**Date**: 2026-01-01 | **Result**: 42.22% black (improved from 63.71%)
**Key Finding**: GL state is correct - issue is missing geometry, not rendering bug

---

### Session: 2026-01-01_18-48-47 - glMaterial Fix
**Date**: 2026-01-01 | **Result**: 63.71% black (improved from 97.74%)
**Fix Applied**: `glMaterialfv` accept GL_FRONT/GL_BACK face parameters
**Key Finding**: Lighting restored, revealed separate screen truncation issue

---

### Session: 2026-01-01_18-31-39 - Initial
**Date**: 2026-01-01 | **Result**: 97.74% black
**Key Finding**: UI renders correctly, 3D scene nearly black - lighting issue

---

## Progress Summary

| Date | Change | Black % | Delta |
|------|--------|---------|-------|
| 2026-01-01 | Initial capture | 97.74% | - |
| 2026-01-01 | glMaterial fix | 63.71% | -34% |
| 2026-01-01 | GL state investigation | 42.22% | -21% |
| 2026-01-10 | Diagnostic logging added | 42.22% | confirmed |

---

## Current Understanding

**What we know**:
1. GL rendering state is correct (viewport, projection, depth buffer all verified)
2. The black area represents **missing geometry** not a rendering bug
3. Game loads `.Image.def` files via NSData but NOT `.png` textures
4. Device model queries return correct values (320x480, iOS "3.0")

**Leading hypothesis**: Game uses C stdlib (fopen/fread) for PNG loading

**Next investigation**: Add [DIAG-LIBC] logging to trace fopen/fread calls

---

## Active Diagnostic Prefixes

| Prefix | Purpose | Status |
|--------|---------|--------|
| [DIAG-H1] | decodeBytesForKey calls | REFUTED (0 calls) |
| [DIAG-H2] | Missing NSCoder keys | UI-only keys |
| [DIAG-H3] | File loading via NSData | .def YES, .png NO |
| [DIAG-DEV] | Device/screen queries | CORRECT |

---

## Historical Details

### Breakthrough Session: 2026-01-10_14-13

**Infrastructure fixes applied**:
- Fixed research_runner.py to use Git Bash path (not WSL bash)
- Fixed packed struct reference error in ui_screen.rs

**Diagnostic results**:
- [DIAG-H1] = 0 calls (decodeBytesForKey never used)
- [DIAG-H2] = 9 warnings (UIView, UITag, etc. - all UI keys)
- [DIAG-H3] = 178 file ops (.Image.def loaded, .png NOT loaded)
- [DIAG-DEV] = 2718 calls (UIScreen=320x480, UIDevice="3.0")

**Critical discovery**: Background1/2/3.Image.def files (150-260 bytes) are loaded, but Background1/2/3.png (217-256KB) are NOT loaded through NSData.

---

### GL State Investigation: 2026-01-01

**Verified correct**:
- glViewport(0, 0, 320, 480) - full screen
- No glScissor active
- Renderbuffer: 320x480
- glFrustum aspect ratio: 0.667 (matches 320/480)
- Depth buffer: 320x480, GL_DEPTH_COMPONENT24_OES

**Conclusion**: Black area is missing geometry, not rendering bug.

---

*For detailed per-session outputs, see: `automation_framework/sessions/`*
