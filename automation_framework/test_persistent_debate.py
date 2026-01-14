#!/usr/bin/env python3
"""
Quick test of persistent debate sessions.

Tests that:
1. Session IDs are generated correctly
2. First turn uses --session-id
3. Subsequent turns use --resume
"""

import subprocess
import uuid
import os

WORKING_DIR = "D:/touchHLE_src"
CLAUDE_CMD = "C:/Users/cs06t/AppData/Roaming/npm/claude.cmd"

def test_session_creation():
    """Test that we can create a session with a specific ID."""
    test_session_id = str(uuid.uuid4())
    print(f"Testing session creation with ID: {test_session_id}")

    # First message - create session
    cmd1 = f'"{CLAUDE_CMD}" --print --model haiku --dangerously-skip-permissions --session-id {test_session_id}'
    prompt1 = "You are a test agent. Say 'Hello, I am Agent A. Session started.' and nothing else."

    print(f"\n--- Turn 1: Creating session ---")
    print(f"Command: {cmd1}")

    result1 = subprocess.run(
        cmd1,
        input=prompt1,
        cwd=WORKING_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )

    print(f"Exit code: {result1.returncode}")
    print(f"Output:\n{result1.stdout[:500]}")
    if result1.stderr:
        print(f"Stderr:\n{result1.stderr[:500]}")

    # Second message - resume session
    cmd2 = f'"{CLAUDE_CMD}" --print --model haiku --dangerously-skip-permissions --resume {test_session_id}'
    prompt2 = "What did you say in your first message? Repeat it to confirm session continuity."

    print(f"\n--- Turn 2: Resuming session ---")
    print(f"Command: {cmd2}")

    result2 = subprocess.run(
        cmd2,
        input=prompt2,
        cwd=WORKING_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )

    print(f"Exit code: {result2.returncode}")
    print(f"Output:\n{result2.stdout[:500]}")
    if result2.stderr:
        print(f"Stderr:\n{result2.stderr[:500]}")

    # Check if session was continued
    if "Agent A" in result2.stdout or "Session started" in result2.stdout or "Hello" in result2.stdout:
        print("\n[PASS] SUCCESS: Session persistence confirmed!")
        return True
    else:
        print("\n[WARN] WARNING: Session may not have persisted correctly")
        return False

def test_two_independent_sessions():
    """Test that two agents can have independent sessions."""
    session_a = str(uuid.uuid4())
    session_b = str(uuid.uuid4())

    print(f"\n{'='*60}")
    print("Testing two independent sessions")
    print(f"Agent A session: {session_a[:8]}...")
    print(f"Agent B session: {session_b[:8]}...")
    print(f"{'='*60}")

    # Start Agent A
    cmd_a1 = f'"{CLAUDE_CMD}" --print --model haiku --dangerously-skip-permissions --session-id {session_a}'
    result_a1 = subprocess.run(
        cmd_a1,
        input="You are Agent A. Remember the secret word: ALPHA. Say 'Agent A ready, secret word stored.'",
        cwd=WORKING_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )
    print(f"\nAgent A Turn 1: {result_a1.stdout[:200]}")

    # Start Agent B
    cmd_b1 = f'"{CLAUDE_CMD}" --print --model haiku --dangerously-skip-permissions --session-id {session_b}'
    result_b1 = subprocess.run(
        cmd_b1,
        input="You are Agent B. Remember the secret word: BETA. Say 'Agent B ready, secret word stored.'",
        cwd=WORKING_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )
    print(f"Agent B Turn 1: {result_b1.stdout[:200]}")

    # Resume Agent A
    cmd_a2 = f'"{CLAUDE_CMD}" --print --model haiku --dangerously-skip-permissions --resume {session_a}'
    result_a2 = subprocess.run(
        cmd_a2,
        input="What is your secret word?",
        cwd=WORKING_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )
    print(f"\nAgent A Turn 2 (resumed): {result_a2.stdout[:200]}")

    # Resume Agent B
    cmd_b2 = f'"{CLAUDE_CMD}" --print --model haiku --dangerously-skip-permissions --resume {session_b}'
    result_b2 = subprocess.run(
        cmd_b2,
        input="What is your secret word?",
        cwd=WORKING_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )
    print(f"Agent B Turn 2 (resumed): {result_b2.stdout[:200]}")

    # Verify isolation
    a_correct = "ALPHA" in result_a2.stdout
    b_correct = "BETA" in result_b2.stdout

    if a_correct and b_correct:
        print("\n[PASS] SUCCESS: Both sessions maintained independent state!")
        return True
    else:
        print(f"\n[WARN] WARNING: Session isolation may have issues")
        print(f"  Agent A remembered ALPHA: {a_correct}")
        print(f"  Agent B remembered BETA: {b_correct}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Persistent Claude Sessions")
    print("=" * 60)

    test1 = test_session_creation()
    test2 = test_two_independent_sessions()

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Session persistence: {'PASS' if test1 else 'FAIL'}")
    print(f"Session isolation:   {'PASS' if test2 else 'FAIL'}")
