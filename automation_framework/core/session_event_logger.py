#!/usr/bin/env python3
"""
Session Event Logger for touchHLE Research Pipeline
====================================================

Provides chronological event tracking for debugging sessions with:
- Sequential event numbering (001, 002, 003, ...)
- JSON timeline for programmatic access
- Markdown documents for human readability
- Clear phase/step organization

Adapted from AirSimBinaries/discovery pipeline.

Events are logged to:
- session_timeline.json - Master event log with pointers to all files
- events/ - Individual event files (prompts, responses, decisions)
- outputs/ - Session outputs numbered by creation order
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class EventType(Enum):
    """Types of events that can be logged."""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    STEP_START = "step_start"
    STEP_END = "step_end"
    CLAUDE_PROMPT = "claude_prompt"
    CLAUDE_RESPONSE = "claude_response"
    FILE_CREATED = "file_created"
    FILE_READ = "file_read"
    BUILD_START = "build_start"
    BUILD_END = "build_end"
    TEST_START = "test_start"
    TEST_END = "test_end"
    DECISION = "decision"
    ERROR = "error"
    NOTE = "note"


@dataclass
class Event:
    """Represents a single logged event."""
    event_id: int
    timestamp: str
    event_type: str
    phase: str = ""
    step: str = ""
    description: str = ""
    file: str = ""  # Relative path to associated file
    details: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    cost_usd: float = 0.0


@dataclass
class SessionTimeline:
    """Complete timeline for a session."""
    session_id: str
    session_type: str  # "research_pipeline"
    started_at: str
    ended_at: str = ""
    status: str = "running"

    # Counters
    total_events: int = 0
    total_phases: int = 0
    total_claude_calls: int = 0
    total_cost_usd: float = 0.0

    # Debugging metrics
    initial_black_pct: float = 0.0
    final_black_pct: float = 0.0
    builds_attempted: int = 0
    tests_run: int = 0

    # The event log
    events: List[Dict] = field(default_factory=list)

    # Phase summaries for quick reference
    phases: List[Dict] = field(default_factory=list)


class SessionEventLogger:
    """
    Chronological event logger for touchHLE debugging sessions.

    Usage:
        logger = SessionEventLogger(session_dir, "research_20260110_123456", "research_pipeline")

        # Log phase start
        logger.log_phase_start("planning", "Steps 1-6: Research and planning")

        # Log Claude interaction
        prompt_file = logger.log_claude_prompt("planning", prompt_text)
        response_file = logger.log_claude_response("planning", response)

        # Log test results
        logger.log_test_result("testing", exit_code=2, black_pct=12.5)

        # Finalize
        logger.finalize()
    """

    def __init__(self, session_dir: Path, session_id: str, session_type: str = "research_pipeline"):
        self.session_dir = Path(session_dir)
        self.session_id = session_id
        self.session_type = session_type

        # Create directories
        self.events_dir = self.session_dir / "events"
        self.outputs_dir = self.session_dir / "outputs"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        # Event counter (1-indexed for human readability)
        self._event_counter = 0
        self._output_counter = 0

        # Phase tracking
        self._current_phase: Optional[str] = None
        self._current_step: Optional[str] = None
        self._phase_start_time: Optional[datetime] = None
        self._step_start_time: Optional[datetime] = None
        self._phase_events: Dict[str, List[int]] = {}

        # Initialize timeline
        self.timeline = SessionTimeline(
            session_id=session_id,
            session_type=session_type,
            started_at=datetime.now().isoformat()
        )

        # Log session start
        self._log_event(
            EventType.SESSION_START,
            description=f"Session {session_id} started",
            details={"session_type": session_type}
        )

        # Write initial timeline
        self._save_timeline()

    def _next_event_id(self) -> int:
        """Get next event ID."""
        self._event_counter += 1
        return self._event_counter

    def _next_output_id(self) -> int:
        """Get next output file ID."""
        self._output_counter += 1
        return self._output_counter

    def _log_event(self, event_type: EventType, phase: str = "", step: str = "",
                   description: str = "", file: str = "", details: Dict = None,
                   duration_seconds: float = 0.0, cost_usd: float = 0.0) -> Event:
        """Log an event to the timeline."""
        event_id = self._next_event_id()

        event = Event(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type.value,
            phase=phase or self._current_phase or "",
            step=step or self._current_step or "",
            description=description,
            file=file,
            details=details or {},
            duration_seconds=duration_seconds,
            cost_usd=cost_usd
        )

        self.timeline.events.append(asdict(event))
        self.timeline.total_events = event_id

        if cost_usd > 0:
            self.timeline.total_cost_usd += cost_usd

        # Track events per phase
        if event.phase:
            if event.phase not in self._phase_events:
                self._phase_events[event.phase] = []
            self._phase_events[event.phase].append(event_id)

        return event

    def _save_timeline(self):
        """Save timeline to JSON file."""
        timeline_path = self.session_dir / "session_timeline.json"
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.timeline), f, indent=2, ensure_ascii=False)

    # =========================================================================
    # PHASE & STEP LOGGING
    # =========================================================================

    def log_phase_start(self, phase_name: str, description: str = "") -> int:
        """Log the start of a phase."""
        self._current_phase = phase_name
        self._phase_start_time = datetime.now()
        self.timeline.total_phases += 1

        event = self._log_event(
            EventType.PHASE_START,
            phase=phase_name,
            description=description or f"Starting phase: {phase_name}"
        )

        self._save_timeline()
        return event.event_id

    def log_phase_end(self, phase_name: str, success: bool = True,
                      summary: str = "") -> int:
        """Log the end of a phase."""
        duration = 0.0
        if self._phase_start_time:
            duration = (datetime.now() - self._phase_start_time).total_seconds()

        event = self._log_event(
            EventType.PHASE_END,
            phase=phase_name,
            description=summary or f"Completed phase: {phase_name}",
            details={"success": success},
            duration_seconds=duration
        )

        # Add phase summary
        self.timeline.phases.append({
            "phase": phase_name,
            "success": success,
            "duration_seconds": duration,
            "event_ids": self._phase_events.get(phase_name, []),
            "summary": summary
        })

        self._current_phase = None
        self._phase_start_time = None
        self._save_timeline()
        return event.event_id

    def log_step_start(self, step_name: str, description: str = "") -> int:
        """Log the start of a step within a phase."""
        self._current_step = step_name
        self._step_start_time = datetime.now()

        event = self._log_event(
            EventType.STEP_START,
            step=step_name,
            description=description or f"Starting step: {step_name}"
        )

        self._save_timeline()
        return event.event_id

    def log_step_end(self, step_name: str, success: bool = True,
                     summary: str = "") -> int:
        """Log the end of a step."""
        duration = 0.0
        if self._step_start_time:
            duration = (datetime.now() - self._step_start_time).total_seconds()

        event = self._log_event(
            EventType.STEP_END,
            step=step_name,
            description=summary or f"Completed step: {step_name}",
            details={"success": success},
            duration_seconds=duration
        )

        self._current_step = None
        self._step_start_time = None
        self._save_timeline()
        return event.event_id

    # =========================================================================
    # CLAUDE INTERACTION LOGGING
    # =========================================================================

    def log_claude_prompt(self, phase: str, prompt: str, step: str = "") -> str:
        """
        Log a prompt sent to Claude Code.

        Returns:
            Path to the saved prompt file (relative to session_dir)
        """
        event_id = self._next_event_id()

        # Save prompt to file
        filename = f"{event_id:03d}_claude_prompt.md"
        filepath = self.events_dir / filename
        relative_path = f"events/{filename}"

        content = f"""# Claude Prompt

**Event ID:** {event_id}
**Phase:** {phase}
**Step:** {step or "N/A"}
**Timestamp:** {datetime.now().isoformat()}

---

{prompt}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Log event
        event = Event(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.CLAUDE_PROMPT.value,
            phase=phase,
            step=step,
            description="Sent prompt to Claude Code",
            file=relative_path,
            details={"prompt_length": len(prompt)}
        )

        self.timeline.events.append(asdict(event))
        self.timeline.total_events = event_id
        self.timeline.total_claude_calls += 1

        self._save_timeline()
        return relative_path

    def log_claude_response(self, phase: str, response: Dict[str, Any],
                            step: str = "", prompt_event_id: int = None) -> str:
        """
        Log a response from Claude Code.

        Returns:
            Path to the saved response file (relative to session_dir)
        """
        event_id = self._next_event_id()

        # Extract response details
        result_text = response.get("result", "") or response.get("output", "") or str(response)
        is_error = response.get("is_error", False)
        cost = response.get("total_cost_usd", 0) or 0
        num_turns = response.get("num_turns", 0) or 0
        session_id = response.get("session_id", "")

        # Save response to file
        filename = f"{event_id:03d}_claude_response.md"
        filepath = self.events_dir / filename
        relative_path = f"events/{filename}"

        content = f"""# Claude Response

**Event ID:** {event_id}
**Phase:** {phase}
**Step:** {step or "N/A"}
**Timestamp:** {datetime.now().isoformat()}
**Cost:** ${cost:.4f}
**Turns:** {num_turns}
**Success:** {not is_error}
**Prompt Event:** {prompt_event_id or "N/A"}

---

{result_text if result_text else "(No response text)"}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Log event
        event = Event(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.CLAUDE_RESPONSE.value,
            phase=phase,
            step=step,
            description="Received response from Claude Code",
            file=relative_path,
            details={
                "response_length": len(result_text),
                "is_error": is_error,
                "num_turns": num_turns,
                "prompt_event_id": prompt_event_id,
                "claude_session_id": session_id
            },
            cost_usd=cost
        )

        self.timeline.events.append(asdict(event))
        self.timeline.total_events = event_id
        self.timeline.total_cost_usd += cost

        self._save_timeline()
        return relative_path

    # =========================================================================
    # BUILD & TEST LOGGING
    # =========================================================================

    def log_build_start(self, phase: str = "testing") -> int:
        """Log start of a build."""
        self.timeline.builds_attempted += 1

        event = self._log_event(
            EventType.BUILD_START,
            phase=phase,
            description="Starting build"
        )

        self._save_timeline()
        return event.event_id

    def log_build_end(self, phase: str = "testing", success: bool = True,
                      duration: float = 0.0, warnings: int = 0) -> int:
        """Log end of a build."""
        event = self._log_event(
            EventType.BUILD_END,
            phase=phase,
            description=f"Build {'succeeded' if success else 'failed'}",
            details={"success": success, "warnings": warnings},
            duration_seconds=duration
        )

        self._save_timeline()
        return event.event_id

    def log_test_start(self, phase: str = "testing") -> int:
        """Log start of a test run."""
        self.timeline.tests_run += 1

        event = self._log_event(
            EventType.TEST_START,
            phase=phase,
            description="Starting test (crash_monitor.sh capture)"
        )

        self._save_timeline()
        return event.event_id

    def log_test_result(self, phase: str, exit_code: int, black_pct: float = None,
                        output: str = "", duration: float = 0.0) -> int:
        """Log test result."""
        status_map = {2: "PASS", 3: "FAIL", 0: "CRASH", 1: "ERROR"}
        status = status_map.get(exit_code, f"EXIT_{exit_code}")

        # Update timeline metrics
        if black_pct is not None:
            self.timeline.final_black_pct = black_pct
            if self.timeline.initial_black_pct == 0:
                self.timeline.initial_black_pct = black_pct

        event = self._log_event(
            EventType.TEST_END,
            phase=phase,
            description=f"Test result: {status} ({black_pct}% black)" if black_pct else f"Test result: {status}",
            details={
                "exit_code": exit_code,
                "status": status,
                "black_pct": black_pct,
                "output_length": len(output)
            },
            duration_seconds=duration
        )

        self._save_timeline()
        return event.event_id

    # =========================================================================
    # FILE OPERATIONS LOGGING
    # =========================================================================

    def log_file_created(self, phase: str, filename: str,
                         description: str = "", content: str = None,
                         step: str = "") -> str:
        """Log creation of an output file."""
        event_id = self._next_event_id()

        if content is not None:
            # Write to outputs/ with numbering
            output_id = self._next_output_id()
            base, ext = filename.rsplit(".", 1) if "." in filename else (filename, "md")
            numbered_filename = f"{output_id:03d}_{base}.{ext}"
            filepath = self.outputs_dir / numbered_filename
            relative_path = f"outputs/{numbered_filename}"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            relative_path = filename

        self._log_event(
            EventType.FILE_CREATED,
            phase=phase,
            step=step,
            description=description or f"Created file: {filename}",
            file=relative_path
        )

        self._save_timeline()
        return relative_path

    def log_file_read(self, phase: str, filepath: str,
                      description: str = "", step: str = "") -> int:
        """Log reading of a file."""
        event = self._log_event(
            EventType.FILE_READ,
            phase=phase,
            step=step,
            description=description or f"Read file: {filepath}",
            file=filepath
        )

        self._save_timeline()
        return event.event_id

    # =========================================================================
    # DECISION & NOTE LOGGING
    # =========================================================================

    def log_decision(self, phase: str, decision: str, reasoning: str,
                     alternatives: List[str] = None, step: str = "") -> str:
        """Log a decision made during the session."""
        event_id = self._next_event_id()

        filename = f"{event_id:03d}_decision.md"
        filepath = self.events_dir / filename
        relative_path = f"events/{filename}"

        content = f"""# Decision

**Event ID:** {event_id}
**Phase:** {phase}
**Step:** {step or "N/A"}
**Timestamp:** {datetime.now().isoformat()}

## Decision

{decision}

## Reasoning

{reasoning}

"""
        if alternatives:
            content += "## Alternatives Considered\n\n"
            for alt in alternatives:
                content += f"- {alt}\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        self._log_event(
            EventType.DECISION,
            phase=phase,
            step=step,
            description=decision[:100],
            file=relative_path,
            details={"alternatives_count": len(alternatives) if alternatives else 0}
        )

        self._save_timeline()
        return relative_path

    def log_note(self, phase: str, note: str, step: str = "") -> int:
        """Log a general note or observation."""
        event = self._log_event(
            EventType.NOTE,
            phase=phase,
            step=step,
            description=note[:200]
        )

        self._save_timeline()
        return event.event_id

    def log_error(self, phase: str, error: str, details: Dict = None,
                  step: str = "") -> int:
        """Log an error."""
        event = self._log_event(
            EventType.ERROR,
            phase=phase,
            step=step,
            description=f"Error: {error[:100]}",
            details={"error_message": error, **(details or {})}
        )

        self._save_timeline()
        return event.event_id

    # =========================================================================
    # FINALIZATION
    # =========================================================================

    def finalize(self, status: str = "completed", summary: str = ""):
        """Finalize the session and generate summary files."""
        self.timeline.ended_at = datetime.now().isoformat()
        self.timeline.status = status

        # Log session end
        self._log_event(
            EventType.SESSION_END,
            description=summary or f"Session {status}",
            details={
                "total_events": self.timeline.total_events,
                "total_cost_usd": self.timeline.total_cost_usd,
                "initial_black_pct": self.timeline.initial_black_pct,
                "final_black_pct": self.timeline.final_black_pct,
                "builds_attempted": self.timeline.builds_attempted,
                "tests_run": self.timeline.tests_run
            }
        )

        # Save final timeline
        self._save_timeline()

        # Generate human-readable summary
        self._generate_summary()

    def _generate_summary(self):
        """Generate a human-readable session summary."""
        summary_path = self.session_dir / "SESSION_SUMMARY.md"

        t = self.timeline

        # Calculate duration
        try:
            start = datetime.fromisoformat(t.started_at)
            end = datetime.fromisoformat(t.ended_at) if t.ended_at else datetime.now()
            duration = (end - start).total_seconds()
            duration_str = f"{duration / 60:.1f} minutes"
        except:
            duration_str = "N/A"

        content = f"""# Session Summary: {t.session_id}

## Overview

| Metric | Value |
|--------|-------|
| Session ID | {t.session_id} |
| Type | {t.session_type} |
| Status | {t.status} |
| Started | {t.started_at} |
| Ended | {t.ended_at or "N/A"} |
| Duration | {duration_str} |
| Total Events | {t.total_events} |
| Total Cost | ${t.total_cost_usd:.4f} |

## Debugging Metrics

| Metric | Value |
|--------|-------|
| Initial Black % | {t.initial_black_pct:.2f}% |
| Final Black % | {t.final_black_pct:.2f}% |
| Improvement | {t.initial_black_pct - t.final_black_pct:.2f}% |
| Builds Attempted | {t.builds_attempted} |
| Tests Run | {t.tests_run} |
| Claude API Calls | {t.total_claude_calls} |
| Phases Completed | {t.total_phases} |

## Phase Summary

| # | Phase | Duration | Success | Events |
|---|-------|----------|---------|--------|
"""
        for i, phase in enumerate(t.phases, 1):
            success = "Yes" if phase.get("success") else "No"
            duration = f"{phase.get('duration_seconds', 0):.1f}s"
            events = len(phase.get("event_ids", []))
            content += f"| {i} | {phase.get('phase', 'Unknown')} | {duration} | {success} | {events} |\n"

        content += """
## Event Timeline

| ID | Time | Type | Phase | Description |
|----|------|------|-------|-------------|
"""
        events_to_show = t.events[:50]
        for event in events_to_show:
            eid = event.get("event_id", "?")
            timestamp = event.get("timestamp", "")
            time_part = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
            etype = event.get("event_type", "")
            phase = event.get("phase", "")
            desc = event.get("description", "")[:50]
            content += f"| {eid} | {time_part} | {etype} | {phase} | {desc} |\n"

        if len(t.events) > 50:
            content += f"\n*... and {len(t.events) - 50} more events. See session_timeline.json for full log.*\n"

        content += f"""
## Files Generated

### Events Directory (`events/`)
"""
        for event in t.events:
            if event.get("file", "").startswith("events/"):
                content += f"- `{event['file']}` - {event.get('description', '')[:50]}\n"

        content += """
### Outputs Directory (`outputs/`)
"""
        for event in t.events:
            if event.get("file", "").startswith("outputs/"):
                content += f"- `{event['file']}` - {event.get('description', '')[:50]}\n"

        content += f"""
---

*Generated at {datetime.now().isoformat()}*
*Full event log available in `session_timeline.json`*
"""

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(content)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def load_session_timeline(session_dir: Path) -> Optional[SessionTimeline]:
    """Load a session timeline from disk."""
    timeline_path = session_dir / "session_timeline.json"
    if not timeline_path.exists():
        return None

    with open(timeline_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return SessionTimeline(**data)


def get_phase_events(timeline: SessionTimeline, phase_name: str) -> List[Dict]:
    """Get all events for a specific phase."""
    return [e for e in timeline.events if e.get("phase") == phase_name]


def get_claude_interactions(timeline: SessionTimeline) -> List[Dict]:
    """Get all Claude prompt/response pairs."""
    interactions = []
    prompts = [e for e in timeline.events if e.get("event_type") == "claude_prompt"]
    responses = [e for e in timeline.events if e.get("event_type") == "claude_response"]

    for response in responses:
        prompt_id = response.get("details", {}).get("prompt_event_id")
        prompt = next((p for p in prompts if p.get("event_id") == prompt_id), None)
        interactions.append({
            "prompt": prompt,
            "response": response,
            "cost_usd": response.get("cost_usd", 0)
        })

    return interactions
