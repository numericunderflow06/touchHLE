# Plan Deduplication Check - Session research_2026-01-10_13-16-02

## Comparison Against Past Attempts

### Past Implementations (from MEMORY.md)

| Attempt | Description | Result |
|---------|-------------|--------|
| glMaterial fix | Fix face parameter handling | SUCCESS (97% → 63%) |
| Viewport investigation | Check viewport settings | RULED OUT - correct |
| Frustum investigation | Check frustum clipping | RULED OUT - correct |
| Depth buffer analysis | Check depth configuration | RULED OUT - correct |
| glFrustum shift hack | 2.5% bottom shift | INEFFECTIVE - removed |
| decodeBytesForKey impl | Add binary decode method | NOT TESTED - build failed |
| Diagnostic logging | [DIAG-H1/H2/H3] tags | NOT TESTED - build failed |

### Past Hypotheses (from HYPOTHESIS_TRACKER.json)

| ID | Hypothesis | Status |
|----|------------|--------|
| H001 | Lighting misconfiguration | PARTIALLY_CONFIRMED |
| H002 | Frustum clipping | NOT_CONFIRMED |
| H003 | Missing decodeBytesForKey | INCONCLUSIVE (not tested) |
| H004 | Other missing NSCoder methods | INCONCLUSIVE (not tested) |
| H005 | File-based terrain loading | INCONCLUSIVE (not tested) |

---

## Duplicate Analysis

### Is the current plan a duplicate?

**NO** - The current plan is NOT a duplicate.

**Reasoning**:
1. The previous session (research_2026-01-10_12-35-40) added diagnostic logging but **never tested it** due to build failure
2. This plan's primary action is to **run the existing code and analyze logs**
3. No past session has successfully collected [DIAG-*] log data
4. The approach (diagnostic-first, then targeted fix) is different from previous "try a fix and see" approaches

### What's Different This Time

| Previous Approaches | Current Plan |
|--------------------|--------------|
| Tried specific fixes blind | Run diagnostics first |
| Assumed problem location | Let logs reveal actual failure point |
| One hypothesis per session | Multiple conditional paths based on evidence |

---

## Novel Aspects of This Plan

1. **Diagnostic-driven debugging**: Instead of guessing fixes, we'll analyze actual log output to identify the failure point

2. **Conditional fix paths**: The plan defines 4 different scenarios (A-D) based on what logs reveal, each with a different fix strategy

3. **Upstream comparison completed**: Confirmed NSKeyedUnarchiver is already complete - we know this is NOT the gap

4. **Focus on evidence collection**: Primary goal is data gathering, not immediate code changes

---

## FINAL PLAN (Confirmed Novel)

### Phase 1: Build and Test (Immediate)
```bash
./build_monitor.sh start && ./build_monitor.sh wait
./crash_monitor.sh capture
```

### Phase 2: Analyze Logs
- Look for [DIAG-H1] entries (decodeBytesForKey calls)
- Look for [DIAG-H2] entries (missing NSKeyedUnarchiver keys)
- Look for [DIAG-H3] entries (NSBundle/NSData file loading)

### Phase 3: Targeted Fix (Based on Evidence)
- Scenario A: Bytes decode successful → trace downstream usage
- Scenario B: Keys missing → implement additional decoders
- Scenario C: Files failing to load → fix path resolution
- Scenario D: No logs → terrain uses different loading mechanism

---

## Conclusion

**Plan is NOVEL and ACTIONABLE**. Proceed with implementation.

The key insight is that we already have diagnostic code in place - we just need to run it and analyze the output. This is a fundamentally different approach from previous sessions that tried specific code fixes without evidence.
