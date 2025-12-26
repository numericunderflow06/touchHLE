/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Event capture system for automation and testing.
//!
//! This module provides structured JSON logging of touch events and other
//! interactions to enable automated testing and monitoring of the emulator.

use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

/// Global frame counter for associating events with frames
static FRAME_COUNTER: AtomicU64 = AtomicU64::new(0);

/// Global event capture state
static EVENT_CAPTURE: Mutex<Option<EventCapture>> = Mutex::new(None);

/// Event types that can be captured
#[derive(Debug, Clone)]
pub enum CapturedEvent {
    TouchDown {
        finger_id: String,
        x: f32,
        y: f32,
    },
    TouchMove {
        finger_id: String,
        x: f32,
        y: f32,
    },
    TouchUp {
        finger_id: String,
        x: f32,
        y: f32,
    },
    TouchDelivered {
        view: String,
        method: String, // touchesBegan, touchesMoved, touchesEnded
        x: f32,
        y: f32,
    },
    FrameRendered {
        frame_number: u64,
    },
    Crash {
        message: String,
        location: Option<String>,
    },
    Log {
        level: String,
        message: String,
    },
}

/// State for event capture
pub struct EventCapture {
    file: File,
    path: PathBuf,
    capture_touches: bool,
    capture_frames: bool,
    capture_delivery: bool, // Capture when events are delivered to views
}

impl EventCapture {
    /// Create a new event capture instance
    fn new(path: PathBuf) -> std::io::Result<Self> {
        let file = OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&path)?;

        Ok(EventCapture {
            file,
            path,
            capture_touches: true,
            capture_frames: true,
            capture_delivery: true,
        })
    }

    /// Write an event to the capture file
    fn write_event(&mut self, event: &CapturedEvent) {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis())
            .unwrap_or(0);

        let frame = FRAME_COUNTER.load(Ordering::Relaxed);

        let json = match event {
            CapturedEvent::TouchDown { finger_id, x, y } => {
                if !self.capture_touches { return; }
                format!(
                    r#"{{"ts":{},"frame":{},"type":"touch_down","finger":"{}","x":{:.2},"y":{:.2}}}"#,
                    timestamp, frame, finger_id, x, y
                )
            }
            CapturedEvent::TouchMove { finger_id, x, y } => {
                if !self.capture_touches { return; }
                format!(
                    r#"{{"ts":{},"frame":{},"type":"touch_move","finger":"{}","x":{:.2},"y":{:.2}}}"#,
                    timestamp, frame, finger_id, x, y
                )
            }
            CapturedEvent::TouchUp { finger_id, x, y } => {
                if !self.capture_touches { return; }
                format!(
                    r#"{{"ts":{},"frame":{},"type":"touch_up","finger":"{}","x":{:.2},"y":{:.2}}}"#,
                    timestamp, frame, finger_id, x, y
                )
            }
            CapturedEvent::TouchDelivered { view, method, x, y } => {
                if !self.capture_delivery { return; }
                format!(
                    r#"{{"ts":{},"frame":{},"type":"touch_delivered","view":"{}","method":"{}","x":{:.2},"y":{:.2}}}"#,
                    timestamp, frame, view, method, x, y
                )
            }
            CapturedEvent::FrameRendered { frame_number } => {
                if !self.capture_frames { return; }
                format!(
                    r#"{{"ts":{},"frame":{},"type":"frame_rendered"}}"#,
                    timestamp, frame_number
                )
            }
            CapturedEvent::Crash { message, location } => {
                let loc = location.as_deref().unwrap_or("unknown");
                format!(
                    r#"{{"ts":{},"frame":{},"type":"crash","message":"{}","location":"{}"}}"#,
                    timestamp, frame,
                    message.replace('\\', "\\\\").replace('"', "\\\""),
                    loc.replace('\\', "\\\\").replace('"', "\\\"")
                )
            }
            CapturedEvent::Log { level, message } => {
                format!(
                    r#"{{"ts":{},"frame":{},"type":"log","level":"{}","message":"{}"}}"#,
                    timestamp, frame, level,
                    message.replace('\\', "\\\\").replace('"', "\\\"").replace('\n', "\\n")
                )
            }
        };

        // Write JSON line
        let _ = writeln!(self.file, "{}", json);
        let _ = self.file.flush();
    }
}

// Public API

/// Initialize event capture with the given output path
pub fn init(path: PathBuf) -> Result<(), String> {
    let capture = EventCapture::new(path.clone())
        .map_err(|e| format!("Failed to initialize event capture at {:?}: {}", path, e))?;

    let mut guard = EVENT_CAPTURE.lock().unwrap();
    *guard = Some(capture);

    echo!("Event capture initialized: {:?}", path);
    Ok(())
}

/// Check if event capture is enabled
pub fn is_enabled() -> bool {
    EVENT_CAPTURE.lock().unwrap().is_some()
}

/// Capture a touch down event
pub fn touch_down(finger_id: &str, x: f32, y: f32) {
    if let Some(ref mut capture) = *EVENT_CAPTURE.lock().unwrap() {
        capture.write_event(&CapturedEvent::TouchDown {
            finger_id: finger_id.to_string(),
            x,
            y,
        });
    }
}

/// Capture a touch move event
pub fn touch_move(finger_id: &str, x: f32, y: f32) {
    if let Some(ref mut capture) = *EVENT_CAPTURE.lock().unwrap() {
        capture.write_event(&CapturedEvent::TouchMove {
            finger_id: finger_id.to_string(),
            x,
            y,
        });
    }
}

/// Capture a touch up event
pub fn touch_up(finger_id: &str, x: f32, y: f32) {
    if let Some(ref mut capture) = *EVENT_CAPTURE.lock().unwrap() {
        capture.write_event(&CapturedEvent::TouchUp {
            finger_id: finger_id.to_string(),
            x,
            y,
        });
    }
}

/// Capture when a touch event is delivered to a view
pub fn touch_delivered(view: &str, method: &str, x: f32, y: f32) {
    if let Some(ref mut capture) = *EVENT_CAPTURE.lock().unwrap() {
        capture.write_event(&CapturedEvent::TouchDelivered {
            view: view.to_string(),
            method: method.to_string(),
            x,
            y,
        });
    }
}

/// Capture a frame render event and increment the frame counter
pub fn frame_rendered() {
    let frame = FRAME_COUNTER.fetch_add(1, Ordering::Relaxed);
    if let Some(ref mut capture) = *EVENT_CAPTURE.lock().unwrap() {
        capture.write_event(&CapturedEvent::FrameRendered {
            frame_number: frame,
        });
    }
}

/// Get the current frame number
pub fn current_frame() -> u64 {
    FRAME_COUNTER.load(Ordering::Relaxed)
}

/// Capture a crash event
pub fn capture_crash(message: &str, location: Option<&str>) {
    if let Some(ref mut capture) = *EVENT_CAPTURE.lock().unwrap() {
        capture.write_event(&CapturedEvent::Crash {
            message: message.to_string(),
            location: location.map(|s| s.to_string()),
        });
    }
}

/// Capture a log event
pub fn capture_log(level: &str, message: &str) {
    if let Some(ref mut capture) = *EVENT_CAPTURE.lock().unwrap() {
        capture.write_event(&CapturedEvent::Log {
            level: level.to_string(),
            message: message.to_string(),
        });
    }
}
