# TouchHLE Debugging Memory

## Quick Reference

- **Problem**: Screen truncation - bottom ~40% of screen is black
- **Current**: 22.39% black pixels with landscape mode (down from 42.22%)
- **Target**: < 15% black pixels
- **Test**: `./crash_monitor.sh capture` (exit 2 = PASS, exit 3 = FAIL)

---

## Latest Sessions (newest first)

### Session: manual_2026-02-02 - MAJOR BREAKTHROUGH
**Date**: 2026-02-02 | **Result**: SIGNIFICANT IMPROVEMENT (42.22% → 22.39% black)
**Key Discoveries**:
1. **ROOT CAUSE IDENTIFIED**: Game uses 90° rotation in modelview matrix
   - ModelView shows rotation: X→Y, Y→-X transformation
   - Camera position: (-320, 240, 415)
   - Game designed for LANDSCAPE orientation internally
2. **FIX**: Running with `--landscape-left` option reduces black pixels by ~50%
   - Portrait mode: 42.22% black
   - Landscape mode: 22.39% black
3. **Configuration**: Added to touchHLE_options.txt:
   ```
   cde.AvatarOfWarTDL: --landscape-left
   ```

**Technical Analysis**:
- Frustum parameters: left=-0.192450, right=0.192450, bottom=-0.288675, top=0.288675
- Aspect ratio: 0.6667 (correct for 320x480 portrait internally)
- The game renders internally at 320x480 then rotates via modelview
- TouchHLE's landscape mode rotates the final presentation to match

**Remaining Issues**:
- 22.39% black still exceeds 15% target
- Click coordinates in crash_monitor.sh need adjustment for landscape
- May need further investigation if gameplay shows different black percentage than menu

**Files Modified**:
- `touchHLE_options.txt` - Added landscape-left for this game
- `src/frameworks/opengles/gles_guest.rs` - Added DIAG-FRUSTUM and modelview logging

---

### Session: multiagent_2026-01-21_13-16-50 - Code Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1, 50.55% black baseline)
**Code Approach**: Verification-first strategy - proposed testing existing renderbuffer fix (FIXME at eagl.rs:228) before adding new code. Zero code changes in Phase 1.
**Key Finding**: 15th consecutive build failure. Code pipeline led debate with documentation-grounded hypotheses (Apple EAGL + CALayer docs). H1 (renderbuffer FIXME fix) remains highest-confidence target.
**Debate Outcome**: Fast consensus (2 turns). Error's `[DIAG-E12-PROJ]` projection query added to Phase 1. Verification-first principle adopted. Media Picker Controller random suggestion dismissed.

### Session: multiagent_2026-01-21_13-16-50 - Error Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1, 50.55% black baseline)
**Error Approach**: Three novel diagnostics - projection matrix state query `[DIAG-E12-PROJ]`, vertex region+Y correlation `[DIAG-E9-YCORR]`, and setFrame mutation logging `[DIAG-E10-SETFRAME]`.
**Key Finding**: Successfully modified consensus to include projection query in Phase 1 (not Phase 2). Argued that Y=320 capping may originate from projection, not just renderbuffer.
**Debate Contribution**: Accepted Code's verification-first philosophy. Contributed `[DIAG-E12-PROJ]` as highest-ROI diagnostic. ns_array random suggestion dismissed.

---

### Session: multiagent_2026-01-21_12-08-34 - Code Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1, 50.55% black baseline)
**Code Approach**: FIXME-driven renderbuffer dimension fix - identified explicit FIXME comment at eagl.rs:228 acknowledging code uses wrong dimension source. Fix: use `msg![env; drawable bounds]` instead of `window.size_unrotated_scalehacked()` per Apple EAGL documentation.
**Key Finding**: MOST DEFINITIVE EVIDENCE YET - FIXME comment explicitly states code is wrong. Combined with Apple documentation (renderbuffer must match layer bounds), this is highest-confidence fix across all 14 sessions.
**Debate Outcome**: Code pipeline led debate with consensus proposal in Turn 1. Fast agreement (2 turns). H2 (renderbuffer FIXME) is HIGHEST PRIORITY for next successful build.
**Hypotheses**: H1 (vertex sampling regression) INCONCLUSIVE, H2 (renderbuffer FIXME) INCONCLUSIVE (highest confidence), H3 (fullscreen layer checks) INCONCLUSIVE

### Session: multiagent_2026-01-21_12-08-34 - Error Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1, 50.55% black baseline)
**Error Approach**: Three runtime hypotheses targeting novel angles: H1 (splash vs gameplay scene transitions via draw call counts), H2 (vertex data memory source classification - STACK/HEAP/MMAP), H3 (projection state correlation with draw calls).
**Key Finding**: BUILD FAILED blocked all hypothesis testing. Error pipeline correctly conceded to Code's FIXME-based approach given documented evidence (FIXME comment + Apple EAGL docs) had higher confidence than runtime observation.
**Diagnostic Output**: None captured (build failed before test execution). [DIAG-E1] (vertex memory regions) and [DIAG-E2] (per-frame summary) implemented but untested.
**Debate Contribution**: Accepted Code's FIXME fix as primary. Contributed [DIAG-EAGL-DIM] refinement to verify layer vs window dimensions before fix. Contributed [DIAG-E2] validation logging for Phase 2. Random NSDate suggestion dismissed as irrelevant to coordinate geometry.
**Lesson Learned**: Concede to documented evidence (FIXME comments, API docs) when higher confidence than runtime observation alone.

---

### Session: multiagent_2026-01-21_11-17-26 - Code Pipeline
**Date**: 2026-01-21 | **Result**: FAIL (50.55% black - regression)
**Code Approach**: CFDictionary method crash prevention - implemented 3 methods (description, copyWithZone:, mutableCopyWithZone:) in _touchHLE_NSMutableDictionary_non_retaining to replace todo!() panics.
**Key Finding**: Zero [DIAG-DICT-*] log entries - CFDictionary methods are NOT called during game execution. These were defensive fixes for crash prevention but NOT the root cause.
**Debate Outcome**: Phased consensus adopted (verify first, then code fixes). Code pipeline proposed, Error pipeline accepted.
**Critical Issue**: ALL diagnostic logging returns "(None captured)" - infrastructure gap persists across 13+ sessions.

### Session: multiagent_2026-01-21_11-17-26 - Error Pipeline
**Date**: 2026-01-21 | **Result**: FAIL (50.55% black - regression)
**Error Approach**: Verification-first strategy - proposed running `./crash_monitor.sh capture` to verify if existing fixes worked BEFORE adding new code. Three hypotheses: H1 (verify fix via Y=480 coords), H2 (menu vs gameplay rendering), H3 (capture timing).
**Key Finding**: REGRESSION detected - black pixels increased from 42.22% to 50.55%. Context analysis over-interpreted Y=480.0 log snippets as "fix working" but actual test proved this wrong. Capture timing (H3) REFUTED as cause - touch injection and frame capture work correctly.
**Diagnostic Output**: All [DIAG-*] show "(None captured)" - infrastructure gap persists across 14 sessions.
**Debate Contribution**: Verification-first principle adopted as Phase 1 of consensus. Error pipeline accepted Code's CFDictionary crash-prevention fixes as Phase 2 backup. Mach semaphore random suggestion dismissed as LOW relevance.
**Lesson Learned**: Don't over-trust log snippets - always run actual test to verify.

---

### Session: multiagent_2026-01-21_10-19-09 - Error Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: GL query function instrumentation with [DIAG-H1-QUERY] for glGetIntegerv, glGetFloatv, glGetBooleanv, glGetPointerv. GLES1-on-GL2 capability instrumentation with [DIAG-H2-CAP] for Enable/Disable/ClientState plus pre-panic WARNING logging.
**Key Finding**: Build failure (13th consecutive) blocked all hypothesis testing. Prioritized GL query functions as likely crash point based on evidence: crash after glGetString(GL_EXTENSIONS), zero [DIAG-H1-GLCALL] entries means crash before those 9 instrumented functions.
**Diagnostic Output**: None captured (build failed before test execution)
**Debate Contribution**: Accepted Code's consensus proposal in Turn 2. Contributed GL query diagnostics as Phase 1B. Memory hypothesis (H3) self-deprioritized based on >1MB stack space evidence.
**Hypotheses**: H1 (GL Query Parameter) HIGHEST, H2 (GL Capability) HIGH, H3 (Memory) LOW/DEFERRED - all INCONCLUSIVE

---

### Session: multiagent_2026-01-21_10-19-09 - Code Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Novel crash-on-call bug investigation - identified 4 API violations by comparing touchHLE against Apple/POSIX docs: (1) CFDictionary copyDescription todo!() violates Apple "never returns NULL", (2) CFDictionary capacity assertion rejects valid usage, (3) CGContextClipToRect todo!() blocks standard clipping, (4) mmap offset assertion rejects valid POSIX usage.
**Key Finding**: Build failure (13th consecutive) blocked all testing. All 4 areas (CFDictionary, CGContext, mmap offset) were NOVEL - never investigated in 12+ prior sessions. Documentation comparison identified clear API violations.
**Debate Outcome**: Fast consensus (Turn 1) by proposing combined Phase 1A (Code fixes) + Phase 1B (Error GL diagnostics). Code pipeline led with consensus proposal.
**Files Modified**: `src/frameworks/core_foundation/cf_dictionary.rs` (copyDescription + capacity), `src/frameworks/core_graphics/cg_context.rs` (ClipToRect), `src/libc/mmap.rs` (offset)

---

### Session: multiagent_2026-01-21_09-32-22 - Code Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Verification-first strategy - test existing fixes (d_type, NSScanner) + novel mmap investigation for PNG loading
**Key Finding**: Build failure (12th consecutive) blocked all hypothesis testing. Error pipeline identified game may now CRASH during GL init (after glGetString), not screen truncation. UIView.frame=320x480 confirmed correct - dimension issue is elsewhere.
**Debate Outcome**: Fast consensus (Turn 1) - Code accepted crash-first priority, contributed regression analysis + [DIAG-MMAP] logging; Error contributed [DIAG-H1-GLCALL] GL tracing + [DIAG-H2-STACK] SP monitoring
**Files Modified**: `src/frameworks/opengles/gles_guest.rs` ([DIAG-H1-GLCALL]), `src/environment.rs` ([DIAG-H2-STACK]), `src/libc/mmap.rs` ([DIAG-MMAP])

### Session: multiagent_2026-01-21_09-32-22 - Error Pipeline
**Date**: 2026-01-21 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Crash diagnosis with GL function tracing - identified potential problem type change (crash during GL init vs screen truncation). Added [DIAG-H1-GLCALL] to 9 GL functions and [DIAG-H2-STACK] for panic handler SP monitoring.
**Key Finding**: Build failure (12th consecutive) blocked testing. CRITICAL INSIGHT: Game may be CRASHING (PC=0x00108dcc, SP=0xfffffd88 after glGetString) rather than just showing screen truncation. Prior diagnostics ([DIAG-C1]/[DIAG-C3]) were NEVER TRIGGERED because crash occurs before directory enumeration.
**Diagnostic Output**: None captured (build failed before test execution)
**Debate Contribution**: Crash-first priority accepted by both pipelines in Turn 2; error pipeline reframed the investigation from truncation to potential crash; contributed [DIAG-H1-GLCALL] for 9 GL functions and [DIAG-H2-STACK] for panic handler
**Hypotheses**: H1 (Unimplemented GL function) HIGH priority, H2 (Stack overflow) MEDIUM priority, H3 (Threading/context) DEFERRED

---

### Session: multiagent_2026-01-20_21-13-09 - Code Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: IMPLEMENTED d_type fix in dirent.rs - returns DT_DIR=4 for directories, DT_REG=8 for files instead of DT_UNKNOWN=0
**Key Finding**: Build failure (11th consecutive) blocked testing. The d_type fix is IMPLEMENTED and logically correct per POSIX/BSD spec. First session to actually implement fix (prior sessions only added logging).
**Debate Outcome**: Consensus in 2 turns - Code contributed d_type fix (PHASE 1A - PRIMARY); Error contributed [DIAG-ERR-FRAME], [DIAG-ERR-ORIENT], [DIAG-ERR-VPTR] diagnostics (PHASE 1B)
**Files Modified**: `src/libc/dirent.rs` (d_type fix), `src/frameworks/uikit/ui_device.rs`, `src/frameworks/uikit/ui_view.rs`, `src/frameworks/opengles/gles_guest.rs`

### Session: multiagent_2026-01-20_21-13-09 - Error Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Three novel diagnostic targets - UIView.frame (distinct from bounds), UIDevice.orientation, glVertexPointer
**Key Finding**: Build failure (11th in multi-agent pipeline) blocked testing. All diagnostics implemented but untested.
**Diagnostic Output**: None captured (build failed before test execution)
**Debate Contribution**: Accepted d_type fix as primary; provided dimension diagnostics for Phase 2 analysis if d_type doesn't resolve issue

---

### Session: multiagent_2026-01-20_12-58-40 - Code Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Investigate dirent d_type implementation gap - touchHLE returns d_type=0 (DT_UNKNOWN) instead of proper values (DT_DIR=4, DT_REG=8) per POSIX/BSD spec
**Key Finding**: Build failure (10th consecutive) blocked all hypothesis testing. NOVEL hypothesis: dirent never investigated in 9+ sessions. If game discovers assets via directory enumeration and filters by d_type, returning 0 would cause files to be skipped.
**Debate Outcome**: Consensus in 2 turns - Code contributed [DIAG-C1/C2/C3] dirent logging; Error contributed [DIAG-E1/E2/E3] dimension tracing. Both approaches accepted as complementary (dirent = file discovery, dimensions = coordinate calculation).
**Added**: `src/libc/dirent.rs` - [DIAG-C1] opendir, [DIAG-C2] readdir with d_type, [DIAG-C3] closedir

### Session: multiagent_2026-01-20_12-58-40 - Error Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Dimension-source tracing with [DIAG-E1] for UIView.bounds (GL-related views) and [DIAG-E3] for UIScreen.applicationFrame
**Key Finding**: Build failure (10th in multi-agent pipeline) blocked all hypothesis testing. Key insight from prior sessions: game does NOT use GL projection helpers (zero glOrthof/glMatrixMode calls), so 320 value must enter from iOS dimension APIs.
**Diagnostic Output**: None captured (build failed before test execution)
**Debate Contribution**: Accepted Code pipeline's dirent d_type hypothesis as complementary; provided fallback plan (CALayer.bounds if Phase 1 fails)

---

### Session: multiagent_2026-01-20_12-26-52 - Code Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Implement NSScanner `scanDouble:` method (mirrors scanFloat: pattern with f64) - confirmed API gap per Apple documentation (available since iOS 2.0)
**Key Finding**: Build failure (9th consecutive) prevented hypothesis testing. scanDouble: implementation complete but untested. All 3 hypotheses remain INCONCLUSIVE.
**Debate Outcome**: Consensus in 2 turns - Code contributed scanDouble: implementation (Phase 1A - PRIMARY); Error contributed [DIAG-ERR1-ORTHOF] glOrthof logging (Phase 1B)
**Implemented**: `src/frameworks/foundation/ns_scanner.rs:383-465` - scanDouble: with [DIAG-SCANDOUBLE] logging

### Session: multiagent_2026-01-20_12-26-52 - Error Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Minimal-first matrix logging with [DIAG-ERR1-ORTHOF] for glOrthof projection parameters to check if top=320 instead of 480
**Key Finding**: Build failure (9th in multi-agent pipeline) prevented hypothesis testing. All 3 hypotheses (projection matrix, view dimensions, parsing) remain INCONCLUSIVE.
**Diagnostic Output**: None captured (build failed before test execution)
**Debate Contribution**: Enhanced Phase 1B by adding glOrthox/glOrthof logging; accepted scanDouble: as complementary code fix

---

### Session: multiagent_2026-01-20_11-59-06 - Code Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Implement missing NSScanner methods (scanLocation getter, setScanLocation: setter) per Apple documentation - first session to implement MISSING methods rather than just add diagnostics
**Key Finding**: Build failure (7th consecutive) prevented hypothesis testing. Confirmed API gaps: scanLocation, setScanLocation:, scanDouble: are all missing from touchHLE's NSScanner.
**Debate Outcome**: Consensus in 2 turns - Code contributed method implementations + [DIAG-SCAN-LOC] logging; Error contributed dimension-tracing diagnostics ([DIAG-H1-LAYER], [DIAG-H2-VIEWPORT], [DIAG-H3-VIEW])

### Session: multiagent_2026-01-20_11-59-06 - Error Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Dimension-source tracing with [DIAG-H1-LAYER] for CALayer bounds, [DIAG-H2-VIEWPORT] for glGetIntegerv(GL_VIEWPORT), [DIAG-H3-VIEW] for UIView frame queries
**Key Finding**: Build failure (8th in multi-agent pipeline) prevented hypothesis testing. Hypotheses systematically trace iOS rendering dimension stack: UIView→CALayer→GL viewport→vertex generation
**Diagnostic Output**: None captured (build failed before test execution)
**Debate Contribution**: Dimension-source diagnostics accepted as Phase 2 fallback; accepted NSScanner fix as complementary quick-test approach

---

### Session: multiagent_2026-01-20_11-26-20 - Code Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: NSScanner method tracing to investigate .def file parsing (scanUpToString, scanString, scanInt, scanCharactersFromSet)
**Key Finding**: Build failure (6th consecutive) prevented all hypothesis testing - NSScanner diagnostics implemented but never executed
**Debate Outcome**: Consensus in 2 turns - Code contributed Phase 1B (NSScanner tracing) alongside Error's Phase 1A (matrix logging); both approaches recognized as complementary

### Session: multiagent_2026-01-20_11-26-20 - Error Pipeline
**Date**: 2026-01-20 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Projection matrix analysis with [DIAG-E1-MATRIX] glLoadMatrixf logging, [DIAG-E2-MATRIX-MODE] matrix mode tracking, [DIAG-E3-ORTHOX] fixed-point ortho
**Key Finding**: Build failure (7th in multi-agent pipeline) prevented hypothesis testing. Matrix logging was designated Phase 1A (HIGH PRIORITY) in consensus.
**Diagnostic Output**: None captured (build failed before test execution)
**Pending Hypothesis**: m[5] ≈ 0.00625 (2/320) would confirm projection uses 320-pixel height instead of 480 - remains untested

---

### Session: multiagent_2026-01-15_10-24-16 - Error Pipeline
**Date**: 2026-01-15 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Parallel vertex validation with [DIAG-E1-VERTEX] Y coordinate sampling, [DIAG-E2-SCISSOR] scissor state logging
**Key Finding**: Infrastructure discovery - touchHLE_log.txt contains 15K+ DIAG entries (logging WORKS, crash_monitor reads wrong source)
**Diagnostic Output**: None captured (build failed before test execution)
**Debate Contribution**: Promoted vertex sampling from backup (Phase 2) to parallel execution (Phase 1B); conceded mmap hypothesis based on zero fopen evidence

---

### Session: multiagent_2026-01-15_10-24-16 - Code Pipeline
**Date**: 2026-01-15 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: .def file format analysis with [DIAG-C1] hex dump and [DIAG-C2] ASCII preview
**Key Finding**: CRITICAL DISCOVERY during context analysis - touchHLE_log.txt contains 15K+ [DIAG-*] entries! Logging infrastructure WORKS - crash_monitor.sh was reading stdout/stderr instead of log file
**Debate Outcome**: Consensus in 2 turns - CODE contributed PHASE 1A (.def analysis) as primary, ERROR contributed PHASE 1B (vertex sampling) as parallel validation

---

### Session: multiagent_2026-01-14_21-20-46 - Code Pipeline
**Date**: 2026-01-14 | **Result**: FAIL (42.22% black - unchanged)
**Code Approach**: Observation-first consensus - execute 9 existing diagnostic prefixes with ZERO code changes
**Key Finding**: BREAKTHROUGH - First successful build in 5 sessions. NEW PROBLEM: Diagnostic logging not visible in test output (all [DIAG-*] show "None captured")
**Debate Outcome**: Consensus in 2 turns - code contributed documentation-grounded matrix, error contributed NSFileManager contingency; both agreed on observation-first principle

### Session: multiagent_2026-01-14_21-20-46 - Error Pipeline
**Date**: 2026-01-14 | **Result**: FAIL (42.22% black - unchanged)
**Error Approach**: Observation-first consensus - execute 9 existing DIAG-* prefixes (E1/E2/E3/FREAD/C2/C3/CASE/PATH/BUNDLE) with ZERO code changes
**Key Finding**: INFRASTRUCTURE GAP DISCOVERED - All 9 diagnostic prefixes produced ZERO captured output. Build succeeded, game ran, but log! macro output not visible in capture pipeline
**Diagnostic Output**: None captured (0 lines from all 9 prefixes - infrastructure bug, not hypothesis failure)
**Next Action Required**: Fix capture infrastructure before any hypothesis can be tested

---

## Infrastructure Updates (2026-01-11)

### Random Idea Injection System
Added random suggestion injection to help models discover new investigation angles.
- **Location**: `automation_framework/random_injection/`
- **Lists**: 49 code components, 62 debug/log items
- **Injection Points**: Planning Step 2, Planning Step 4 (error only), Debate turns
- **Verified**: Models actively evaluate suggestions, incorporate or dismiss with reasoning
- **Docs**: `automation_framework/random_injection/INTEGRATION_GUIDE.md`
- **Session Doc**: `automation_framework/docs/SESSION_2026-01-11_SUMMARY.md`

### Template Fix (phase_8_*_reflection.md)
Fixed KeyError in reflection phase templates caused by unescaped JSON curly braces.
- **Solution**: Escaped `{` to `{{` and `}` to `}}` in JSON example blocks

---

## Latest Sessions (newest first)

### Session: multiagent_2026-01-14_20-42-29 - Code Pipeline
**Date**: 2026-01-14 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Case-insensitive filesystem lookup fix (iOS HFS+ compatibility) with [DIAG-CASE], [DIAG-PATH], [DIAG-BUNDLE] diagnostics
**Key Finding**: Build failure prevented testing; case-insensitive fix implemented but not executed (5th consecutive build failure)
**Debate Outcome**: Hybrid consensus in 2 turns - code contributed iOS documentation-grounded fix, error contributed observation-first principle

---

### Session: multiagent_2026-01-14_20-42-29 - Error Pipeline
**Date**: 2026-01-14 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Observation-first principle - execute existing DIAG-E1/E2/E3/FREAD/C2/C3 before adding any new code
**Key Finding**: Build failure prevented testing; 5th consecutive build failure blocks all hypothesis testing
**Diagnostic Output**: None captured - 9 diagnostic prefixes implemented and waiting for successful build
**Debate Contribution**: Observation-first principle accepted; deferred fix argument rejected (case-insensitive fix is low-risk)

---

### Session: multiagent_2026-01-14_12-32-51 - Code Pipeline
**Date**: 2026-01-14 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Three-hypothesis plan targeting fread (C99), path resolution, CgBI PNG handling
**Key Finding**: Build failure prevented testing; fread logging and draw call diagnostics implemented but never executed
**Debate Outcome**: Hybrid consensus in 2 turns - code contributed [DIAG-FREAD], error contributed [DIAG-E3]
**Critical Pattern**: Third consecutive build failure - infrastructure is blocking all hypothesis testing

---

### Session: multiagent_2026-01-14_12-32-51 - Error Pipeline
**Date**: 2026-01-14 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Observation-first phased diagnostics with conditional fread/draw call logging
**Key Finding**: Build failure prevented testing; DIAG-E3 draw call logging upgraded from log_dbg! to log!
**Diagnostic Output**: None captured (4th consecutive build failure)
**Debate Contribution**: "Observation-first" principle accepted; DIAG-E3 upgrade was unique error contribution

---

### Session: multiagent_2026-01-11_21-35-37 - Error Pipeline
**Date**: 2026-01-11 | **Result**: BUILD FAILED (exit -1)
**Error Approach**: Pipeline tracing diagnostics (fopen E1, TexImage2D E2, with deferred fread E3)
**Key Finding**: Build failure prevented testing; E2 (TexImage2D logging) accepted as unique error contribution
**Diagnostic Output**: None captured (build failure)
**Debate Contribution**: E2 filled "critical gap" in code pipeline; targeted glGetError accepted over comprehensive E4

---

### Session: multiagent_2026-01-11_21-35-37 - Code Pipeline
**Date**: 2026-01-11 | **Result**: BUILD FAILED (exit -1)
**Code Approach**: Documentation-grounded diagnostics for texture pipeline (fopen, decode, UIImage, TexImage2D)
**Key Finding**: Build failure prevented testing; all diagnostic code implemented but not executed
**Debate Outcome**: Consensus reached in 2 turns - merged code + error pipeline diagnostics
**Hypotheses**: H1 (fopen expansion), H2 (decode failures), H3 (.def manifests) - all INCONCLUSIVE
**See**: `automation_framework/sessions/multiagent_2026-01-11_21-35-37/`

---
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
