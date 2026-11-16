"""Sample where a running emulator's main thread is executing (Windows).

usage: python aow/tools/sample.py <pid> [seconds] [depth]

A plain sampling profiler: several hundred times a second the busiest thread of
the process is paused for an instant, its instruction pointer and a few return
addresses are read, and it is resumed. Addresses are named from the debug
information next to the binary (`touchHLE.pdb`, which a release build writes).
Samples inside code the emulator generated at run time (the translated ARM
code of the app) have no name and are reported as "(translated app code)";
stacks cannot be followed through that code, so callers are listed only up to
it.

This complements the emulator's own `profile` command, which knows about the
app's side (which host function, which guest function) but cannot see inside
host functions.
"""

import collections
import ctypes
import ctypes.wintypes as wt
import json
import sys
import time
from pathlib import Path

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbghelp = ctypes.WinDLL("dbghelp", use_last_error=True)

PROCESS_ALL_ACCESS = 0x1F0FFF
THREAD_ALL_ACCESS = 0x1F03FF
TH32CS_SNAPTHREAD = 0x4
CONTEXT_AMD64 = 0x100000
CONTEXT_FULL = CONTEXT_AMD64 | 0x1 | 0x2 | 0x8
IMAGE_FILE_MACHINE_AMD64 = 0x8664
SYMOPT_UNDNAME = 0x2
SYMOPT_DEFERRED_LOADS = 0x4


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ThreadID", wt.DWORD),
                ("th32OwnerProcessID", wt.DWORD), ("tpBasePri", wt.LONG), ("tpDeltaPri", wt.LONG),
                ("dwFlags", wt.DWORD)]


class ADDRESS64(ctypes.Structure):
    _fields_ = [("Offset", ctypes.c_uint64), ("Segment", wt.WORD), ("Mode", wt.DWORD)]


class KDHELP64(ctypes.Structure):
    _fields_ = [("Thread", ctypes.c_uint64), ("ThCallbackStack", wt.DWORD),
                ("ThCallbackBStore", wt.DWORD), ("NextCallback", wt.DWORD),
                ("FramePointer", wt.DWORD), ("KiCallUserMode", ctypes.c_uint64),
                ("KeUserCallbackDispatcher", ctypes.c_uint64), ("SystemRangeStart", ctypes.c_uint64),
                ("KiUserExceptionDispatcher", ctypes.c_uint64), ("StackBase", ctypes.c_uint64),
                ("StackLimit", ctypes.c_uint64), ("BuildVersion", wt.DWORD),
                ("RetpolineStubFunctionTableSize", wt.DWORD),
                ("RetpolineStubFunctionTable", ctypes.c_uint64), ("RetpolineStubOffset", wt.DWORD),
                ("RetpolineStubSize", wt.DWORD), ("Reserved0", ctypes.c_uint64 * 2)]


class STACKFRAME64(ctypes.Structure):
    _fields_ = [("AddrPC", ADDRESS64), ("AddrReturn", ADDRESS64), ("AddrFrame", ADDRESS64),
                ("AddrStack", ADDRESS64), ("AddrBStore", ADDRESS64), ("FuncTableEntry", ctypes.c_void_p),
                ("Params", ctypes.c_uint64 * 4), ("Far", wt.BOOL), ("Virtual", wt.BOOL),
                ("Reserved", ctypes.c_uint64 * 3), ("KdHelp", KDHELP64)]


class SYMBOL_INFO(ctypes.Structure):
    _fields_ = [("SizeOfStruct", wt.ULONG), ("TypeIndex", wt.ULONG), ("Reserved", ctypes.c_uint64 * 2),
                ("Index", wt.ULONG), ("Size", wt.ULONG), ("ModBase", ctypes.c_uint64),
                ("Flags", wt.ULONG), ("Value", ctypes.c_uint64), ("Address", ctypes.c_uint64),
                ("Register", wt.ULONG), ("Scope", wt.ULONG), ("Tag", wt.ULONG),
                ("NameLen", wt.ULONG), ("MaxNameLen", wt.ULONG), ("Name", ctypes.c_char * 512)]


# Offsets inside the x64 CONTEXT structure (winnt.h).
CONTEXT_SIZE = 1232
OFFSET_FLAGS, OFFSET_RSP, OFFSET_RBP, OFFSET_RIP = 0x30, 0x98, 0xA0, 0xF8

kernel32.OpenProcess.restype = wt.HANDLE
kernel32.OpenThread.restype = wt.HANDLE
kernel32.CreateToolhelp32Snapshot.restype = wt.HANDLE
kernel32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
kernel32.GetThreadTimes.argtypes = [wt.HANDLE] + [ctypes.POINTER(wt.FILETIME)] * 4
dbghelp.SymInitializeW.argtypes = [wt.HANDLE, wt.LPCWSTR, wt.BOOL]
dbghelp.SymFromAddr.argtypes = [wt.HANDLE, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
                                ctypes.POINTER(SYMBOL_INFO)]
dbghelp.SymGetModuleBase64.argtypes = [wt.HANDLE, ctypes.c_uint64]
dbghelp.SymGetModuleBase64.restype = ctypes.c_uint64
dbghelp.SymFunctionTableAccess64.argtypes = [wt.HANDLE, ctypes.c_uint64]
dbghelp.SymFunctionTableAccess64.restype = ctypes.c_void_p
dbghelp.StackWalk64.argtypes = [wt.DWORD, wt.HANDLE, wt.HANDLE, ctypes.POINTER(STACKFRAME64),
                                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                ctypes.c_void_p]


def threads_of(pid):
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    entry = THREADENTRY32()
    entry.dwSize = ctypes.sizeof(entry)
    found = []
    ok = kernel32.Thread32First(snapshot, ctypes.byref(entry))
    while ok:
        if entry.th32OwnerProcessID == pid:
            found.append(entry.th32ThreadID)
        ok = kernel32.Thread32Next(snapshot, ctypes.byref(entry))
    kernel32.CloseHandle(snapshot)
    return found


def cpu_time(thread):
    times = [wt.FILETIME() for _ in range(4)]
    kernel32.GetThreadTimes(thread, *[ctypes.byref(t) for t in times])
    return sum((t.dwHighDateTime << 32 | t.dwLowDateTime) for t in times[2:])


def busiest_thread(pid, settle=0.3):
    handles = {tid: kernel32.OpenThread(THREAD_ALL_ACCESS, False, tid) for tid in threads_of(pid)}
    before = {tid: cpu_time(handle) for tid, handle in handles.items() if handle}
    time.sleep(settle)
    best = max(before, key=lambda tid: cpu_time(handles[tid]) - before[tid])
    for tid, handle in handles.items():
        if handle and tid != best:
            kernel32.CloseHandle(handle)
    return handles[best]


def aligned_context():
    raw = ctypes.create_string_buffer(CONTEXT_SIZE + 16)
    address = ctypes.addressof(raw)
    offset = (16 - address % 16) % 16
    return raw, address + offset


def sample(pid, seconds=3.0, depth=6, interval=0.001):
    process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not process:
        raise SystemExit(f"cannot open process {pid}: error {ctypes.get_last_error()}")
    dbghelp.SymSetOptions(SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS)
    # Runs use a private copy of the binary; its debug information stays where
    # the build wrote it.
    release = Path(__file__).resolve().parents[2] / "target" / "release"
    search = f"{release};{release / 'deps'}"
    if not dbghelp.SymInitializeW(process, search, True):
        raise SystemExit(f"SymInitialize failed: error {ctypes.get_last_error()}")
    thread = busiest_thread(pid)
    keep, context = aligned_context()

    stacks = collections.Counter()
    deadline = time.time() + seconds
    while time.time() < deadline:
        if kernel32.SuspendThread(thread) == 0xFFFFFFFF:
            break
        try:
            ctypes.memset(context, 0, CONTEXT_SIZE)
            ctypes.c_uint32.from_address(context + OFFSET_FLAGS).value = CONTEXT_FULL
            if not kernel32.GetThreadContext(thread, context):
                continue
            frame = STACKFRAME64()
            for field, offset in (("AddrPC", OFFSET_RIP), ("AddrFrame", OFFSET_RBP), ("AddrStack", OFFSET_RSP)):
                address = getattr(frame, field)
                address.Offset = ctypes.c_uint64.from_address(context + offset).value
                address.Mode = 3  # AddrModeFlat
            addresses = []
            for _ in range(depth):
                if not dbghelp.StackWalk64(IMAGE_FILE_MACHINE_AMD64, process, thread, ctypes.byref(frame),
                                           context, None, dbghelp.SymFunctionTableAccess64,
                                           dbghelp.SymGetModuleBase64, None):
                    break
                if not frame.AddrPC.Offset:
                    break
                addresses.append(frame.AddrPC.Offset)
                # Stacks cannot be followed through generated code.
                if not dbghelp.SymGetModuleBase64(process, frame.AddrPC.Offset):
                    break
            if addresses:
                stacks[tuple(addresses)] += 1
        finally:
            kernel32.ResumeThread(thread)
        time.sleep(interval)

    names = {}

    def name_of(address):
        if address not in names:
            info = SYMBOL_INFO()
            info.SizeOfStruct = ctypes.sizeof(SYMBOL_INFO) - 512
            info.MaxNameLen = 511
            displacement = ctypes.c_uint64()
            if dbghelp.SymFromAddr(process, address, ctypes.byref(displacement), ctypes.byref(info)):
                names[address] = info.Name.decode("utf-8", "replace")
            elif dbghelp.SymGetModuleBase64(process, address):
                names[address] = "(unnamed host code)"
            else:
                names[address] = "(translated app code)"
        return names[address]

    total = sum(stacks.values())
    leaf = collections.Counter()
    chains = collections.Counter()
    for addresses, count in stacks.items():
        named = [name_of(a) for a in addresses]
        leaf[named[0]] += count
        chains[" < ".join(named)] += count
    dbghelp.SymCleanup(process)
    kernel32.CloseHandle(thread)
    kernel32.CloseHandle(process)
    return total, leaf, chains


def main():
    pid = int(sys.argv[1])
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    total, leaf, chains = sample(pid, seconds, depth)
    print(json.dumps({
        "samples": total,
        "functions": [{"percent": round(100 * n / max(total, 1), 1), "name": name}
                      for name, n in leaf.most_common(40)],
        "stacks": [{"percent": round(100 * n / max(total, 1), 1), "stack": chain}
                   for chain, n in chains.most_common(40)],
    }, indent=1))


if __name__ == "__main__":
    main()
