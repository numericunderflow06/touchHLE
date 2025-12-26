/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Event injection system for automation and testing.
//!
//! This module allows external processes to inject touch events into the
//! emulator by writing JSON commands to a watched file.

use std::collections::VecDeque;
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Seek, SeekFrom};
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{Duration, Instant};

/// Commands that can be injected
#[derive(Debug, Clone)]
pub enum InjectCommand {
    /// Tap at the given coordinates (touch down + touch up)
    Tap { x: f32, y: f32 },
    /// Touch down at the given coordinates
    TouchDown { x: f32, y: f32 },
    /// Move touch to the given coordinates
    TouchMove { x: f32, y: f32 },
    /// Touch up at the given coordinates
    TouchUp { x: f32, y: f32 },
    /// Wait for a specified number of milliseconds
    Wait { ms: u64 },
    /// Replay events from a captured events file
    Replay { file: String },
    /// Capture a screenshot
    Capture,
}

/// Global event injection state
static EVENT_INJECT: Mutex<Option<EventInject>> = Mutex::new(None);

/// Pending synthetic events to inject
static PENDING_EVENTS: Mutex<VecDeque<SyntheticEvent>> = Mutex::new(VecDeque::new());

/// Synthetic event that should be injected
#[derive(Debug, Clone)]
pub enum SyntheticEvent {
    TouchDown { x: f32, y: f32 },
    TouchMove { x: f32, y: f32 },
    TouchUp { x: f32, y: f32 },
}

/// State for event injection
pub struct EventInject {
    path: PathBuf,
    last_read_pos: u64,
    last_check: Instant,
    check_interval: Duration,
    wait_until: Option<Instant>,
}

impl EventInject {
    fn new(path: PathBuf) -> std::io::Result<Self> {
        // Create the file if it doesn't exist
        if !path.exists() {
            File::create(&path)?;
        }

        Ok(EventInject {
            path,
            last_read_pos: 0,
            last_check: Instant::now() - Duration::from_secs(1),
            check_interval: Duration::from_millis(50), // Check every 50ms
            wait_until: None,
        })
    }

    /// Check for new commands in the injection file
    fn poll(&mut self) -> Vec<InjectCommand> {
        let now = Instant::now();

        // If we're waiting, don't process new commands yet
        if let Some(wait_until) = self.wait_until {
            if now < wait_until {
                return Vec::new();
            }
            self.wait_until = None;
        }

        // Rate limit file checks
        if now.duration_since(self.last_check) < self.check_interval {
            return Vec::new();
        }
        self.last_check = now;

        let mut commands = Vec::new();

        // Check file size to see if there's new content
        let metadata = match fs::metadata(&self.path) {
            Ok(m) => m,
            Err(_) => return commands,
        };

        let file_size = metadata.len();
        if file_size <= self.last_read_pos {
            // No new content (or file was truncated - reset position)
            if file_size < self.last_read_pos {
                self.last_read_pos = 0;
            }
            return commands;
        }

        // Read new lines
        let file = match File::open(&self.path) {
            Ok(f) => f,
            Err(_) => return commands,
        };

        let mut reader = BufReader::new(file);
        if self.last_read_pos > 0 {
            if reader.seek(SeekFrom::Start(self.last_read_pos)).is_err() {
                return commands;
            }
        }

        let mut new_pos = self.last_read_pos;
        for line in reader.lines() {
            let line = match line {
                Ok(l) => l,
                Err(_) => break,
            };
            new_pos += line.len() as u64 + 1; // +1 for newline

            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }

            if let Some(cmd) = parse_command(line) {
                commands.push(cmd);
            }
        }

        self.last_read_pos = new_pos;
        commands
    }
}

/// Parse a single JSON command line
fn parse_command(line: &str) -> Option<InjectCommand> {
    // Simple JSON parsing without external dependencies
    let line = line.trim();
    if !line.starts_with('{') || !line.ends_with('}') {
        return None;
    }

    // Extract type field
    let cmd_type = extract_string_field(line, "type")?;

    match cmd_type.as_str() {
        "tap" => {
            let x = extract_number_field(line, "x")?;
            let y = extract_number_field(line, "y")?;
            Some(InjectCommand::Tap { x, y })
        }
        "touch_down" => {
            let x = extract_number_field(line, "x")?;
            let y = extract_number_field(line, "y")?;
            Some(InjectCommand::TouchDown { x, y })
        }
        "touch_move" => {
            let x = extract_number_field(line, "x")?;
            let y = extract_number_field(line, "y")?;
            Some(InjectCommand::TouchMove { x, y })
        }
        "touch_up" => {
            let x = extract_number_field(line, "x")?;
            let y = extract_number_field(line, "y")?;
            Some(InjectCommand::TouchUp { x, y })
        }
        "wait" => {
            let ms = extract_number_field(line, "ms")? as u64;
            Some(InjectCommand::Wait { ms })
        }
        "replay" => {
            let file = extract_string_field(line, "file")?;
            Some(InjectCommand::Replay { file })
        }
        "capture" => Some(InjectCommand::Capture),
        _ => None,
    }
}

fn extract_string_field(json: &str, field: &str) -> Option<String> {
    let pattern = format!(r#""{}":"#, field);
    let start = json.find(&pattern)? + pattern.len();
    let rest = &json[start..];

    // Skip whitespace
    let rest = rest.trim_start();

    if rest.starts_with('"') {
        // String value
        let rest = &rest[1..];
        let end = rest.find('"')?;
        Some(rest[..end].to_string())
    } else {
        None
    }
}

fn extract_number_field(json: &str, field: &str) -> Option<f32> {
    let pattern = format!(r#""{}":"#, field);
    let start = json.find(&pattern)? + pattern.len();
    let rest = &json[start..];

    // Skip whitespace
    let rest = rest.trim_start();

    // Find the end of the number (comma, closing brace, or whitespace)
    let end = rest.find(|c: char| c == ',' || c == '}' || c.is_whitespace())?;
    let num_str = &rest[..end];

    num_str.parse().ok()
}

/// Replay events from a capture file
fn replay_file(path: &str) -> Vec<SyntheticEvent> {
    let mut events = Vec::new();

    let file = match File::open(path) {
        Ok(f) => f,
        Err(e) => {
            echo!("Failed to open replay file {}: {}", path, e);
            return events;
        }
    };

    let reader = BufReader::new(file);
    let mut last_ts: Option<u128> = None;

    for line in reader.lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => continue,
        };

        let line = line.trim();
        if line.is_empty() {
            continue;
        }

        // Parse the event type
        let event_type = match extract_string_field(line, "type") {
            Some(t) => t,
            None => continue,
        };

        // For now, replay only touch_down and touch_up, skip touch_delivered
        match event_type.as_str() {
            "touch_down" => {
                if let (Some(x), Some(y)) = (
                    extract_number_field(line, "x"),
                    extract_number_field(line, "y"),
                ) {
                    events.push(SyntheticEvent::TouchDown { x, y });
                }
            }
            "touch_up" => {
                if let (Some(x), Some(y)) = (
                    extract_number_field(line, "x"),
                    extract_number_field(line, "y"),
                ) {
                    events.push(SyntheticEvent::TouchUp { x, y });
                }
            }
            "touch_move" => {
                if let (Some(x), Some(y)) = (
                    extract_number_field(line, "x"),
                    extract_number_field(line, "y"),
                ) {
                    events.push(SyntheticEvent::TouchMove { x, y });
                }
            }
            _ => {}
        }
    }

    echo!("Loaded {} events from replay file {}", events.len(), path);
    events
}

// Public API

/// Initialize event injection with the given command file path
pub fn init(path: PathBuf) -> Result<(), String> {
    let inject = EventInject::new(path.clone())
        .map_err(|e| format!("Failed to initialize event injection at {:?}: {}", path, e))?;

    let mut guard = EVENT_INJECT.lock().unwrap();
    *guard = Some(inject);

    echo!("Event injection initialized: {:?}", path);
    echo!("Write JSON commands to this file to inject events.");
    echo!("Commands: tap, touch_down, touch_move, touch_up, wait, replay");
    echo!("Example: {{\"type\":\"tap\",\"x\":100,\"y\":200}}");
    Ok(())
}

/// Check if event injection is enabled
pub fn is_enabled() -> bool {
    EVENT_INJECT.lock().unwrap().is_some()
}

/// Poll for new commands and process them
/// Returns synthetic events that should be injected into the window event queue
pub fn poll() -> Vec<SyntheticEvent> {
    let mut result = Vec::new();

    // First, drain any pending events
    {
        let mut pending = PENDING_EVENTS.lock().unwrap();
        while let Some(event) = pending.pop_front() {
            result.push(event);
        }
    }

    // Then check for new commands
    let commands = {
        let mut guard = EVENT_INJECT.lock().unwrap();
        if let Some(ref mut inject) = *guard {
            inject.poll()
        } else {
            Vec::new()
        }
    };

    for cmd in commands {
        match cmd {
            InjectCommand::Tap { x, y } => {
                echo!("Injecting tap at ({}, {})", x, y);
                result.push(SyntheticEvent::TouchDown { x, y });
                result.push(SyntheticEvent::TouchUp { x, y });
            }
            InjectCommand::TouchDown { x, y } => {
                echo!("Injecting touch down at ({}, {})", x, y);
                result.push(SyntheticEvent::TouchDown { x, y });
            }
            InjectCommand::TouchMove { x, y } => {
                result.push(SyntheticEvent::TouchMove { x, y });
            }
            InjectCommand::TouchUp { x, y } => {
                echo!("Injecting touch up at ({}, {})", x, y);
                result.push(SyntheticEvent::TouchUp { x, y });
            }
            InjectCommand::Wait { ms } => {
                let mut guard = EVENT_INJECT.lock().unwrap();
                if let Some(ref mut inject) = *guard {
                    inject.wait_until = Some(Instant::now() + Duration::from_millis(ms));
                    echo!("Waiting {} ms", ms);
                }
            }
            InjectCommand::Replay { file } => {
                let events = replay_file(&file);
                let mut pending = PENDING_EVENTS.lock().unwrap();
                for event in events {
                    pending.push_back(event);
                }
            }
            InjectCommand::Capture => {
                echo!("Requesting frame capture...");
                crate::frame_capture::request_capture();
            }
        }
    }

    result
}
