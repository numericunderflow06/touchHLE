/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Frame capture system for automation and debugging.
//!
//! This module provides the ability to capture screenshots of the emulator
//! for visual debugging and automated testing.

use std::fs::File;
use std::io::Write;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Mutex;

/// Global frame capture state
static FRAME_CAPTURE: Mutex<Option<FrameCapture>> = Mutex::new(None);

/// Flag to request a frame capture on next frame
static CAPTURE_REQUESTED: AtomicBool = AtomicBool::new(false);

/// Counter for captured frames
static CAPTURE_COUNT: AtomicU64 = AtomicU64::new(0);

/// State for frame capture
pub struct FrameCapture {
    output_dir: PathBuf,
    capture_on_event: bool,
}

impl FrameCapture {
    fn new(output_dir: PathBuf) -> std::io::Result<Self> {
        // Create output directory if it doesn't exist
        std::fs::create_dir_all(&output_dir)?;

        Ok(FrameCapture {
            output_dir,
            capture_on_event: true,
        })
    }

    fn get_next_filename(&self) -> PathBuf {
        let count = CAPTURE_COUNT.fetch_add(1, Ordering::Relaxed);
        self.output_dir.join(format!("frame_{:04}.ppm", count))
    }
}

/// Initialize frame capture with the given output directory
pub fn init(output_dir: PathBuf) -> Result<(), String> {
    let capture = FrameCapture::new(output_dir.clone())
        .map_err(|e| format!("Failed to initialize frame capture at {:?}: {}", output_dir, e))?;

    let mut guard = FRAME_CAPTURE.lock().unwrap();
    *guard = Some(capture);

    echo!("Frame capture initialized: {:?}", output_dir);
    echo!("Frames will be saved as PPM files.");
    Ok(())
}

/// Check if frame capture is enabled
pub fn is_enabled() -> bool {
    FRAME_CAPTURE.lock().unwrap().is_some()
}

/// Request a frame capture on the next frame
pub fn request_capture() {
    CAPTURE_REQUESTED.store(true, Ordering::Relaxed);
}

/// Check if a capture was requested and clear the flag
pub fn capture_requested() -> bool {
    CAPTURE_REQUESTED.swap(false, Ordering::Relaxed)
}

/// Save pixel data to a PPM file
/// PPM is a simple format: P6\nwidth height\n255\nRGBRGBRGB...
pub fn save_frame(width: u32, height: u32, pixels: &[u8]) -> Result<PathBuf, String> {
    let guard = FRAME_CAPTURE.lock().unwrap();
    let capture = guard.as_ref().ok_or("Frame capture not initialized")?;

    let filename = capture.get_next_filename();

    let mut file = File::create(&filename)
        .map_err(|e| format!("Failed to create file {:?}: {}", filename, e))?;

    // Write PPM header
    writeln!(file, "P6").map_err(|e| e.to_string())?;
    writeln!(file, "{} {}", width, height).map_err(|e| e.to_string())?;
    writeln!(file, "255").map_err(|e| e.to_string())?;

    // OpenGL gives us pixels bottom-to-top, but PPM expects top-to-bottom
    // Also, we might have RGBA data but PPM only wants RGB
    let row_size = (width * 4) as usize; // Assuming RGBA input
    for y in (0..height as usize).rev() {
        let row_start = y * row_size;
        for x in 0..width as usize {
            let pixel_start = row_start + x * 4;
            // Write RGB (skip Alpha)
            file.write_all(&pixels[pixel_start..pixel_start + 3])
                .map_err(|e| e.to_string())?;
        }
    }

    echo!("Frame captured: {:?}", filename);
    Ok(filename)
}

/// Get the output directory path
pub fn get_output_dir() -> Option<PathBuf> {
    FRAME_CAPTURE.lock().unwrap().as_ref().map(|c| c.output_dir.clone())
}
