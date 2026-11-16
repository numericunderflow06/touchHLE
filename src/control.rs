/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Control interface: lets an external process drive the emulated app and
//! observe it. Intended for automated testing.
//!
//! Enabled with `--control=<host:port>`. A single client connects over TCP and
//! exchanges one JSON object per line.
//!
//! * A request looks like `{"id": 7, "cmd": "tap", "x": 115, "y": 160}`.
//! * Its response is `{"id": 7, "ok": true, "frame": 1234, ...}` or
//!   `{"id": 7, "ok": false, "error": "..."}`. Requests are executed strictly
//!   in order, and a response is only sent once the command has finished (for
//!   example, a tap responds after the finger was lifted).
//! * Unsolicited lines of the form `{"event": "...", ...}` report things the
//!   client subscribed to (see the `watch` command).
//!
//! Co-ordinates are in "screen points": the pixel co-ordinates of a screenshot
//! taken at scale 1 in the current orientation, origin at the top-left. They
//! are converted to the app's own co-ordinate space here.
//!
//! The socket is serviced once per iteration of the main run loop (see
//! [crate::frameworks::uikit::handle_events]), so commands are handled at the
//! same point where real input would be. Nothing in this module runs unless
//! the option is given, apart from one atomic increment per presented frame.

use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};
use crate::frameworks::foundation::ns_string;
use crate::gles::gles11_raw as gles11;
use crate::gles::GLES;
use crate::mem::{ConstPtr, GuestUSize, Mem, MutPtr, Ptr};
use crate::objc::{id, msg_send_no_type_checking, nil, ObjC, SEL};
use crate::window::{Event, FingerId};
use crate::Environment;
use json::{json, Map, Value};
use std::collections::{HashMap, VecDeque};
use std::io::{ErrorKind, Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

mod json;
pub mod profile;

/// Number of frames presented to the window so far.
static FRAME_COUNT: AtomicU64 = AtomicU64::new(0);

struct ScreenshotState {
    request: Option<PathBuf>,
    /// Width, height and frame number, or an error.
    result: Option<Result<(u32, u32, u64), String>>,
}
static SCREENSHOT: Mutex<ScreenshotState> = Mutex::new(ScreenshotState {
    request: None,
    result: None,
});

/// For [crate::window::Window::swap_window]: count a presented frame.
pub fn frame_presented() {
    FRAME_COUNT.fetch_add(1, Ordering::Relaxed);
}

fn frame_count() -> u64 {
    FRAME_COUNT.load(Ordering::Relaxed)
}

/// For [crate::gles::present::present_frame]: if a screenshot was requested,
/// read back the frame that is about to be presented (the final image the user
/// would see, after rotation, scaling and UI composition) and save it.
///
/// The default framebuffer must be bound and `viewport` must be the region the
/// frame was just drawn to.
pub unsafe fn capture_if_requested(gles: &mut dyn GLES, viewport: (u32, u32, u32, u32)) {
    let Some(path) = SCREENSHOT.lock().unwrap().request.take() else {
        return;
    };
    let (x, y, width, height) = viewport;
    let mut pixels = vec![0x7Fu8; width as usize * height as usize * 4];
    gles.ReadPixels(
        x as _,
        y as _,
        width as _,
        height as _,
        gles11::RGBA,
        gles11::UNSIGNED_BYTE,
        pixels.as_mut_ptr() as *mut _,
    );
    // The frame being captured is the one the next swap will present.
    let frame = frame_count() + 1;
    let result = write_png(&path, width, height, &pixels)
        .map(|()| (width, height, frame))
        .map_err(|e| format!("Could not write {}: {}", path.display(), e));
    SCREENSHOT.lock().unwrap().result = Some(result);
}

/// Write bottom-to-top RGBA8 pixels (as returned by `glReadPixels`) as an RGB8
/// PNG file. The file is written under a temporary name and then renamed, so a
/// reader never sees a partial file.
fn write_png(path: &Path, width: u32, height: u32, pixels: &[u8]) -> std::io::Result<()> {
    let (w, h) = (width as usize, height as usize);
    let mut raw = Vec::with_capacity((w * 3 + 1) * h);
    for row in (0..h).rev() {
        raw.push(0); // filter type: none
        for px in pixels[row * w * 4..(row + 1) * w * 4].chunks_exact(4) {
            raw.extend_from_slice(&px[..3]);
        }
    }
    let mut encoder =
        flate2::write::ZlibEncoder::new(Vec::new(), flate2::Compression::new(4));
    encoder.write_all(&raw)?;
    let compressed = encoder.finish()?;

    fn chunk(out: &mut Vec<u8>, kind: &[u8; 4], data: &[u8]) {
        out.extend_from_slice(&(data.len() as u32).to_be_bytes());
        out.extend_from_slice(kind);
        out.extend_from_slice(data);
        let mut hasher = crc32fast::Hasher::new();
        hasher.update(kind);
        hasher.update(data);
        out.extend_from_slice(&hasher.finalize().to_be_bytes());
    }
    let mut out = Vec::with_capacity(compressed.len() + 64);
    out.extend_from_slice(b"\x89PNG\r\n\x1a\n");
    let mut ihdr = Vec::with_capacity(13);
    ihdr.extend_from_slice(&width.to_be_bytes());
    ihdr.extend_from_slice(&height.to_be_bytes());
    ihdr.extend_from_slice(&[8, 2, 0, 0, 0]); // 8-bit, RGB, no interlacing
    chunk(&mut out, b"IHDR", &ihdr);
    chunk(&mut out, b"IDAT", &compressed);
    chunk(&mut out, b"IEND", &[]);

    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    let tmp = path.with_extension("png.tmp");
    std::fs::write(&tmp, &out)?;
    // rename() on Windows fails if the destination exists.
    let _ = std::fs::remove_file(path);
    std::fs::rename(&tmp, path)
}

struct Client {
    stream: TcpStream,
    in_buf: Vec<u8>,
    lines: VecDeque<String>,
}

/// Condition for a command that takes several frames to finish. It is
/// satisfied when enough frames were presented and a minimum time passed, or
/// unconditionally at a deadline, so that an app which stopped presenting
/// frames (for example while loading) cannot stall the client forever.
#[derive(Clone, Copy)]
struct Until {
    frame: u64,
    not_before: Instant,
    deadline: Instant,
}
impl Until {
    fn frames(frames: u64) -> Until {
        let now = Instant::now();
        Until {
            frame: frame_count() + frames,
            // A frame is at least 1/60s; be a little more lenient than that.
            not_before: now + Duration::from_millis(10 * frames),
            deadline: now + Duration::from_millis(250 + 120 * frames),
        }
    }
    fn reached(&self) -> bool {
        let now = Instant::now();
        (frame_count() >= self.frame && now >= self.not_before) || now >= self.deadline
    }
}

enum Busy {
    Wait {
        id: Value,
        until: Until,
    },
    WaitMs {
        id: Value,
        until: Instant,
    },
    /// Finger is down, waiting to lift it.
    Tap {
        id: Value,
        finger: u32,
        point: (f32, f32),
        until: Until,
    },
    Drag {
        id: Value,
        finger: u32,
        from: (f32, f32),
        to: (f32, f32),
        step: u32,
        steps: u32,
        until: Until,
    },
    Screenshot {
        id: Value,
        path: String,
        deadline: Instant,
    },
}

pub struct Control {
    listener: TcpListener,
    client: Option<Client>,
    busy: Option<Busy>,
    /// Selectors (by pointer) whose message sends are reported as events.
    watch: HashMap<u32, String>,
    out_events: Vec<Value>,
    started: Instant,
    fps_mark: (Instant, u64),
    fps: f32,
    profile_start_frame: u64,
}

impl Control {
    pub fn new(addr: SocketAddr) -> Result<Control, String> {
        let listener = TcpListener::bind(addr)
            .map_err(|e| format!("Could not bind control interface to {addr}: {e}"))?;
        listener
            .set_nonblocking(true)
            .map_err(|e| format!("Could not set up control interface: {e}"))?;
        echo!(
            "Control interface listening on {}.",
            listener.local_addr().map_err(|e| e.to_string())?
        );
        let now = Instant::now();
        Ok(Control {
            listener,
            client: None,
            busy: None,
            watch: HashMap::new(),
            out_events: Vec::new(),
            started: now,
            fps_mark: (now, frame_count()),
            fps: 0.0,
            profile_start_frame: 0,
        })
    }

    /// Whether [on_message] needs to be called at all.
    pub fn is_watching(&self) -> bool {
        !self.watch.is_empty()
    }
}

/// For `objc_msgSend`: report a message send if its selector is being watched.
/// Only called when [Control::is_watching] is true.
pub fn on_message(env: &mut Environment, receiver: id, selector: SEL) {
    let Some(control) = env.control.as_mut() else {
        return;
    };
    let Some(name) = control.watch.get(&selector_bits(selector)) else {
        return;
    };
    let class = ObjC::read_isa(receiver, &env.mem);
    let class_name = env.objc.try_get_class_name(class).unwrap_or("?");
    // r0 = receiver, r1 = selector; the first two word-sized arguments of a
    // method that doesn't return a struct follow in r2 and r3.
    let regs = env.cpu.regs();
    control.out_events.push(json!({
        "event": "msg",
        "sel": name,
        "class": class_name,
        "self": hex(receiver.to_bits()),
        "args": [regs[2], regs[3]],
        // Return address, which identifies the caller.
        "lr": hex(regs[14]),
        "frame": frame_count(),
    }));
}

fn selector_bits(selector: SEL) -> u32 {
    selector.to_bits()
}

fn hex(value: u32) -> String {
    format!("{value:#x}")
}

/// For [crate::frameworks::uikit::handle_events]: process pending requests.
pub fn service(env: &mut Environment) {
    // The control state is taken out of the environment while it runs, so
    // that it can freely borrow the environment. A side effect is that
    // messages sent by our own queries are never reported as events.
    let Some(mut control) = env.control.take() else {
        return;
    };
    control.service(env);
    env.control = Some(control);
}

impl Control {
    fn service(&mut self, env: &mut Environment) {
        // FPS over roughly the last second.
        let now = Instant::now();
        let elapsed = now.duration_since(self.fps_mark.0);
        if elapsed >= Duration::from_secs(1) {
            let frames = frame_count() - self.fps_mark.1;
            self.fps = frames as f32 / elapsed.as_secs_f32();
            self.fps_mark = (now, frame_count());
        }

        self.accept(env);
        self.read_lines();

        loop {
            if let Some(busy) = self.busy.take() {
                match self.continue_busy(env, busy) {
                    Ok(response) => self.send(&response),
                    Err(still_busy) => {
                        self.busy = Some(still_busy);
                        break;
                    }
                }
            }
            let Some(line) = self.client.as_mut().and_then(|c| c.lines.pop_front()) else {
                break;
            };
            if let Some(response) = self.handle_line(env, &line) {
                self.send(&response);
            }
        }

        // Events are kept while no client is connected (a client may connect
        // only briefly for each command), up to a limit.
        if self.client.is_some() {
            for event in std::mem::take(&mut self.out_events) {
                self.send(&event);
            }
        } else if self.out_events.len() > 20_000 {
            let excess = self.out_events.len() - 20_000;
            self.out_events.drain(..excess);
        }
    }

    fn accept(&mut self, env: &mut Environment) {
        match self.listener.accept() {
            Ok((stream, addr)) => {
                echo!("Control client connected from {}.", addr);
                let _ = stream.set_nonblocking(true);
                let _ = stream.set_nodelay(true);
                self.client = Some(Client {
                    stream,
                    in_buf: Vec::new(),
                    lines: VecDeque::new(),
                });
                self.busy = None;
                let hello = json!({
                    "event": "hello",
                    "version": crate::VERSION,
                    "app": env.bundle.bundle_identifier(),
                    "frame": frame_count(),
                });
                self.send(&hello);
            }
            Err(e) if e.kind() == ErrorKind::WouldBlock => {}
            Err(e) => echo!("Control interface accept failed: {}", e),
        }
    }

    fn read_lines(&mut self) {
        let Some(client) = self.client.as_mut() else {
            return;
        };
        let mut buf = [0u8; 4096];
        let mut disconnected = false;
        loop {
            match client.stream.read(&mut buf) {
                Ok(0) => {
                    disconnected = true;
                    break;
                }
                Ok(n) => client.in_buf.extend_from_slice(&buf[..n]),
                Err(e) if e.kind() == ErrorKind::WouldBlock => break,
                Err(e) if e.kind() == ErrorKind::Interrupted => continue,
                Err(_) => {
                    disconnected = true;
                    break;
                }
            }
        }
        while let Some(pos) = client.in_buf.iter().position(|&b| b == b'\n') {
            let line: Vec<u8> = client.in_buf.drain(..=pos).collect();
            let line = String::from_utf8_lossy(&line).trim().to_string();
            if !line.is_empty() {
                client.lines.push_back(line);
            }
        }
        if disconnected && client.lines.is_empty() {
            echo!("Control client disconnected.");
            self.client = None;
            self.busy = None;
        }
    }

    fn send(&mut self, value: &Value) {
        let Some(client) = self.client.as_mut() else {
            return;
        };
        let mut data = value.to_string().into_bytes();
        data.push(b'\n');
        // The socket is non-blocking so that reads never stall the emulator.
        // Responses are small, so briefly waiting for the send buffer is fine.
        let mut written = 0;
        let deadline = Instant::now() + Duration::from_secs(2);
        while written < data.len() {
            match client.stream.write(&data[written..]) {
                Ok(n) => written += n,
                Err(e)
                    if e.kind() == ErrorKind::WouldBlock || e.kind() == ErrorKind::Interrupted =>
                {
                    if Instant::now() > deadline {
                        echo!("Control client is not reading, dropping it.");
                        self.client = None;
                        return;
                    }
                    std::thread::sleep(Duration::from_millis(1));
                }
                Err(_) => {
                    self.client = None;
                    return;
                }
            }
        }
    }

    fn handle_line(&mut self, env: &mut Environment, line: &str) -> Option<Value> {
        let request: Value = match json::parse(line) {
            Ok(value @ Value::Object(_)) => value,
            Ok(_) => return Some(error(Value::Null, "request must be a JSON object")),
            Err(e) => return Some(error(Value::Null, &format!("invalid JSON: {e}"))),
        };
        let id = request.get("id").cloned().unwrap_or(Value::Null);
        let Some(cmd) = request.get("cmd").and_then(Value::as_str) else {
            return Some(error(id, "missing \"cmd\""));
        };
        match self.execute(env, cmd, &request, &id) {
            Ok(Some(result)) => Some(ok(id, result)),
            Ok(None) => None, // became busy; responds later
            Err(message) => Some(error(id, &message)),
        }
    }

    /// Run a command. Returns the result fields, or [None] if the command is
    /// still in progress (in which case `self.busy` was set).
    fn execute(
        &mut self,
        env: &mut Environment,
        cmd: &str,
        request: &Value,
        id: &Value,
    ) -> Result<Option<Value>, String> {
        match cmd {
            "ping" => {
                let (width, height) = env.window().screen_size_points();
                Ok(Some(json!({
                    "fps": (self.fps * 10.0).round() / 10.0,
                    "uptime_ms": self.started.elapsed().as_millis() as u64,
                    "screen": [width, height],
                    "orientation": format!("{:?}", env.window().current_rotation()),
                    "app": env.bundle.bundle_identifier(),
                    "app_version": env.bundle.bundle_version(),
                    "watching": self.watch.values().collect::<Vec<_>>(),
                })))
            }
            "touch" => {
                let phase = get_str(request, "phase")?;
                let point = (get_f32(request, "x")?, get_f32(request, "y")?);
                let finger = opt_u32(request, "finger", 0)?;
                let phase = match phase {
                    "down" => TouchPhase::Down,
                    "move" => TouchPhase::Move,
                    "up" => TouchPhase::Up,
                    _ => return Err("phase must be down, move or up".to_string()),
                };
                push_touch(env, phase, finger, point);
                Ok(Some(json!({})))
            }
            "tap" => {
                let point = (get_f32(request, "x")?, get_f32(request, "y")?);
                let finger = opt_u32(request, "finger", 0)?;
                let hold = opt_u32(request, "hold_frames", 4)?.clamp(1, 600);
                push_touch(env, TouchPhase::Down, finger, point);
                self.busy = Some(Busy::Tap {
                    id: id.clone(),
                    finger,
                    point,
                    until: Until::frames(hold as u64),
                });
                Ok(None)
            }
            "drag" => {
                let from = (get_f32(request, "x1")?, get_f32(request, "y1")?);
                let to = (get_f32(request, "x2")?, get_f32(request, "y2")?);
                let finger = opt_u32(request, "finger", 0)?;
                let steps = opt_u32(request, "frames", 20)?.clamp(1, 6000);
                push_touch(env, TouchPhase::Down, finger, from);
                self.busy = Some(Busy::Drag {
                    id: id.clone(),
                    finger,
                    from,
                    to,
                    step: 0,
                    steps,
                    until: Until::frames(2),
                });
                Ok(None)
            }
            "wait" => {
                if let Some(ms) = request.get("ms") {
                    let ms = ms.as_u64().ok_or("ms must be a non-negative integer")?;
                    self.busy = Some(Busy::WaitMs {
                        id: id.clone(),
                        until: Instant::now() + Duration::from_millis(ms.min(600_000)),
                    });
                } else {
                    let frames = opt_u32(request, "frames", 1)?.min(36_000);
                    self.busy = Some(Busy::Wait {
                        id: id.clone(),
                        until: Until::frames(frames as u64),
                    });
                }
                Ok(None)
            }
            "accel" => {
                let window = env.window_mut();
                if request.get("clear").and_then(Value::as_bool) == Some(true) {
                    window.control_set_accel(None);
                    window.control_set_tilt(None);
                } else {
                    window.control_set_accel(Some((
                        get_f32(request, "x")?,
                        get_f32(request, "y")?,
                        get_f32(request, "z")?,
                    )));
                }
                Ok(Some(json!({})))
            }
            "tilt" => {
                let window = env.window_mut();
                if request.get("clear").and_then(Value::as_bool) == Some(true) {
                    window.control_set_tilt(None);
                } else {
                    let x = get_f32(request, "x")?.clamp(-1.0, 1.0);
                    let y = get_f32(request, "y")?.clamp(-1.0, 1.0);
                    window.control_set_accel(None);
                    window.control_set_tilt(Some((x, y)));
                }
                Ok(Some(json!({})))
            }
            "screenshot" => {
                let path = get_str(request, "path")?.to_string();
                {
                    let mut state = SCREENSHOT.lock().unwrap();
                    state.request = Some(PathBuf::from(&path));
                    state.result = None;
                }
                let timeout = opt_u32(request, "timeout_ms", 3000)?;
                self.busy = Some(Busy::Screenshot {
                    id: id.clone(),
                    path,
                    deadline: Instant::now() + Duration::from_millis(timeout as u64),
                });
                Ok(None)
            }
            "watch" => {
                let selectors = request
                    .get("selectors")
                    .and_then(Value::as_array)
                    .ok_or("missing \"selectors\" (array of selector names)")?;
                let mut unknown = Vec::new();
                for selector in selectors {
                    let name = selector.as_str().ok_or("selectors must be strings")?;
                    match env.objc.lookup_selector(name) {
                        Some(sel) => {
                            self.watch.insert(selector_bits(sel), name.to_string());
                        }
                        // A selector the app has never registered cannot be
                        // sent, so there is nothing to watch.
                        None => unknown.push(name),
                    }
                }
                Ok(Some(json!({
                    "watching": self.watch.values().collect::<Vec<_>>(),
                    "unknown": unknown,
                })))
            }
            "unwatch" => {
                match request.get("selectors").and_then(Value::as_array) {
                    Some(selectors) => {
                        for selector in selectors {
                            let name = selector.as_str().ok_or("selectors must be strings")?;
                            self.watch.retain(|_, watched| watched != name);
                        }
                    }
                    None => self.watch.clear(),
                }
                Ok(Some(json!({ "watching": self.watch.values().collect::<Vec<_>>() })))
            }
            "profile" => match get_str(request, "action")? {
                "start" => {
                    profile::start();
                    self.profile_start_frame = frame_count();
                    Ok(Some(json!({})))
                }
                "stop" => {
                    let top = opt_u32(request, "top", 40)? as usize;
                    let profile = profile::stop().ok_or("profiling was not started")?;
                    let frames = frame_count() - self.profile_start_frame;
                    Ok(Some(profile_json(env, profile, frames, top)))
                }
                _ => Err("action must be start or stop".to_string()),
            },
            "quit" => {
                echo!("Control client requested quit, exiting.");
                self.send(&ok(id.clone(), json!({})));
                env.window_mut().control_push_event(Event::Quit);
                Ok(None)
            }
            // Everything below inspects guest state. A bad pointer from the
            // client must not take the emulator down, so panics are turned
            // into error responses.
            "find" | "describe" | "read" | "nodes" | "views" | "call" => {
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    match cmd {
                        "find" => query_find(env, request),
                        "describe" => query_describe(env, request),
                        "read" => query_read(env, request),
                        "nodes" => query_nodes(env, request),
                        "views" => query_views(env, request),
                        "call" => query_call(env, request),
                        _ => unreachable!(),
                    }
                }));
                match result {
                    Ok(result) => result.map(Some),
                    Err(payload) => {
                        let message = if let Some(s) = payload.downcast_ref::<&str>() {
                            s.to_string()
                        } else if let Some(s) = payload.downcast_ref::<String>() {
                            s.clone()
                        } else {
                            "(non-string panic payload)".to_string()
                        };
                        Err(format!("query panicked: {message}"))
                    }
                }
            }
            _ => Err(format!("unknown command {cmd:?}")),
        }
    }

    /// Advance a multi-frame command. Returns its response when finished.
    fn continue_busy(&mut self, env: &mut Environment, busy: Busy) -> Result<Value, Busy> {
        match busy {
            Busy::Wait { id, until } => {
                if until.reached() {
                    Ok(ok(id, json!({})))
                } else {
                    Err(Busy::Wait { id, until })
                }
            }
            Busy::WaitMs { id, until } => {
                if Instant::now() >= until {
                    Ok(ok(id, json!({})))
                } else {
                    Err(Busy::WaitMs { id, until })
                }
            }
            Busy::Tap {
                id,
                finger,
                point,
                until,
            } => {
                if until.reached() {
                    push_touch(env, TouchPhase::Up, finger, point);
                    // Let the app see the lifted finger before the next
                    // command runs.
                    Err(Busy::Wait {
                        id,
                        until: Until::frames(1),
                    })
                } else {
                    Err(Busy::Tap {
                        id,
                        finger,
                        point,
                        until,
                    })
                }
            }
            Busy::Drag {
                id,
                finger,
                from,
                to,
                step,
                steps,
                until,
            } => {
                if !until.reached() {
                    return Err(Busy::Drag {
                        id,
                        finger,
                        from,
                        to,
                        step,
                        steps,
                        until,
                    });
                }
                if step >= steps {
                    push_touch(env, TouchPhase::Up, finger, to);
                    return Err(Busy::Wait {
                        id,
                        until: Until::frames(1),
                    });
                }
                let step = step + 1;
                let t = step as f32 / steps as f32;
                let point = (from.0 + (to.0 - from.0) * t, from.1 + (to.1 - from.1) * t);
                push_touch(env, TouchPhase::Move, finger, point);
                Err(Busy::Drag {
                    id,
                    finger,
                    from,
                    to,
                    step,
                    steps,
                    // Hold still for a moment at the end, so the app doesn't
                    // treat the release as a fling.
                    until: Until::frames(if step == steps { 2 } else { 1 }),
                })
            }
            Busy::Screenshot { id, path, deadline } => {
                let mut state = SCREENSHOT.lock().unwrap();
                if let Some(result) = state.result.take() {
                    return Ok(match result {
                        Ok((width, height, frame)) => ok(
                            id,
                            json!({
                                "path": path,
                                "width": width,
                                "height": height,
                                "shot_frame": frame,
                            }),
                        ),
                        Err(message) => error(id, &message),
                    });
                }
                if Instant::now() >= deadline {
                    state.request = None;
                    return Ok(error(
                        id,
                        "no frame was presented before the timeout (app is not drawing)",
                    ));
                }
                drop(state);
                Err(Busy::Screenshot { id, path, deadline })
            }
        }
    }
}

fn profile_json(env: &Environment, profile: profile::Profile, frames: u64, top: usize) -> Value {
    fn ms(time: Duration) -> f64 {
        (time.as_secs_f64() * 100_000.0).round() / 100.0
    }
    let class_name = |class: u32| -> String {
        env.objc
            .try_get_class_name(Ptr::from_bits(class))
            .unwrap_or("?")
            .to_string()
    };

    let mut host = profile.host;
    host.sort_by_key(|&(_, stat)| std::cmp::Reverse(stat.time));
    let host: Vec<Value> = host
        .into_iter()
        .take(top)
        .map(|(key, stat)| {
            let name = match key {
                profile::Key::Function(index) => env.dyld.linked_function_name(index).to_string(),
                profile::Key::Method(class, selector) => {
                    format!("[{} {}]", class_name(class), selector.as_str(&env.mem))
                }
            };
            json!({ "name": name, "calls": stat.calls, "ms": ms(stat.time) })
        })
        .collect();

    let mut guest = profile.guest;
    guest.sort_by_key(|&(_, stat)| std::cmp::Reverse(stat.time));
    let guest: Vec<Value> = guest
        .into_iter()
        .take(top * 10)
        .map(|(address, stat)| {
            json!({ "addr": hex(address), "stretches": stat.calls, "ms": ms(stat.time) })
        })
        .collect();

    let mut messages = profile.guest_messages;
    messages.sort_by_key(|&(_, calls)| std::cmp::Reverse(calls));
    let messages: Vec<Value> = messages
        .into_iter()
        .take(top)
        .map(|((class, selector), calls)| {
            json!({
                "name": format!("[{} {}]", class_name(class), selector.as_str(&env.mem)),
                "calls": calls,
            })
        })
        .collect();

    json!({
        "wall_ms": ms(profile.wall),
        "frames": frames,
        "guest_ms": ms(profile.guest_total),
        "host_ms": ms(profile.host_total),
        // Host code outside any profiled call. The main thread is inside the
        // run loop, so there this is the run loop's own work.
        "run_loop_ms": ms(profile.run_loop),
        "other_threads_outside_ms": ms(profile.outside_other_threads),
        // Scheduling, and sleeping while no thread has work.
        "between_threads_ms": ms(profile.between_threads),
        // What the profiler itself cost.
        "transitions": profile.transitions,
        "ns_per_transition": profile.cost_per_transition.as_nanos() as u64,
        "host": host,
        "guest": guest,
        "guest_messages": messages,
    })
}

fn ok(id: Value, result: Value) -> Value {
    let mut map = match result {
        Value::Object(map) => map,
        other => {
            let mut map = Map::new();
            map.insert("result".to_string(), other);
            map
        }
    };
    map.insert("id".to_string(), id);
    map.insert("ok".to_string(), Value::Bool(true));
    map.insert("frame".to_string(), json!(frame_count()));
    Value::Object(map)
}

fn error(id: Value, message: &str) -> Value {
    json!({ "id": id, "ok": false, "error": message, "frame": frame_count() })
}

fn get_str<'a>(request: &'a Value, key: &str) -> Result<&'a str, String> {
    request
        .get(key)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("missing string \"{key}\""))
}

fn get_f32(request: &Value, key: &str) -> Result<f32, String> {
    request
        .get(key)
        .and_then(Value::as_f64)
        .map(|v| v as f32)
        .ok_or_else(|| format!("missing number \"{key}\""))
}

fn opt_u32(request: &Value, key: &str, default: u32) -> Result<u32, String> {
    match request.get(key) {
        None | Some(Value::Null) => Ok(default),
        Some(value) => value
            .as_u64()
            .and_then(|v| u32::try_from(v).ok())
            .ok_or_else(|| format!("\"{key}\" must be a non-negative integer")),
    }
}

/// Parse a guest pointer given as a number or as a hexadecimal string.
fn get_ptr(request: &Value, key: &str) -> Result<u32, String> {
    let value = request
        .get(key)
        .ok_or_else(|| format!("missing pointer \"{key}\""))?;
    parse_ptr(value).ok_or_else(|| format!("\"{key}\" is not a valid pointer"))
}

fn parse_ptr(value: &Value) -> Option<u32> {
    match value {
        Value::Number(_) => value.as_u64().and_then(|v| u32::try_from(v).ok()),
        Value::String(s) => {
            let s = s.trim();
            match s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
                Some(hex) => u32::from_str_radix(hex, 16).ok(),
                None => s.parse().ok(),
            }
        }
        _ => None,
    }
}

#[derive(Clone, Copy)]
enum TouchPhase {
    Down,
    Move,
    Up,
}

fn push_touch(env: &mut Environment, phase: TouchPhase, finger: u32, point: (f32, f32)) {
    let window = env.window_mut();
    let coords = window.control_point_to_touch_coords(point);
    let map = HashMap::from([(FingerId::Control(finger), coords)]);
    window.control_push_event(match phase {
        TouchPhase::Down => Event::TouchesDown(map),
        TouchPhase::Move => Event::TouchesMove(map),
        TouchPhase::Up => Event::TouchesUp(map),
    });
}

// ---------------------------------------------------------------------------
// Guest state queries
// ---------------------------------------------------------------------------

fn to_id(bits: u32) -> id {
    Ptr::from_bits(bits)
}

/// Returns the object if the pointer refers to a live Objective-C object.
fn checked_object(env: &Environment, bits: u32) -> Result<id, String> {
    let object = to_id(bits);
    if object == nil || env.objc.get_host_object(object).is_none() {
        return Err(format!("{} is not a known object", hex(bits)));
    }
    Ok(object)
}

fn class_name_of(env: &Environment, object: id) -> String {
    let class = ObjC::read_isa(object, &env.mem);
    env.objc.try_get_class_name(class).unwrap_or("?").to_string()
}

fn ivar_ptr(env: &Environment, object: id, name: &str) -> Option<MutPtr<GuestUSize>> {
    env.objc
        .object_lookup_ivar(&env.mem, object, &name.to_string())
}

fn read_ivar<T: crate::mem::SafeRead>(env: &Environment, object: id, name: &str) -> Option<T> {
    ivar_ptr(env, object, name).map(|ptr| env.mem.read(ptr.cast::<T>()))
}

/// If `object` is an `NSString`, get its contents.
fn string_value(env: &mut Environment, object: id) -> Option<String> {
    if object == nil || env.objc.get_host_object(object).is_none() {
        return None;
    }
    let class = ObjC::read_isa(object, &env.mem);
    if !env.objc.class_chain_names(class).iter().any(|n| n == "NSString") {
        return None;
    }
    Some(ns_string::to_rust_string(env, object).to_string())
}

fn point_json(point: CGPoint) -> Value {
    json!([point.x, point.y])
}
fn size_json(size: CGSize) -> Value {
    json!([size.width, size.height])
}

/// Read a value of a named type from guest memory.
fn read_typed(env: &mut Environment, addr: u32, type_: &str) -> Result<Value, String> {
    if addr < 0x1000 {
        return Err(format!("address {} is in the null page", hex(addr)));
    }
    fn at<T: crate::mem::SafeRead>(mem: &Mem, addr: u32) -> T {
        mem.read(ConstPtr::<T>::from_bits(addr))
    }
    let mem = &env.mem;
    Ok(match type_ {
        "bool" => json!(at::<u8>(mem, addr) != 0),
        "i8" => json!(at::<i8>(mem, addr)),
        "u8" => json!(at::<u8>(mem, addr)),
        "i16" => json!(at::<i16>(mem, addr)),
        "u16" => json!(at::<u16>(mem, addr)),
        "i32" | "int" => json!(at::<i32>(mem, addr)),
        "u32" => json!(at::<u32>(mem, addr)),
        "f32" | "float" => json!(at::<f32>(mem, addr)),
        "f64" | "double" => json!(at::<f64>(mem, addr)),
        "ptr" => json!(hex(at::<u32>(mem, addr))),
        "point" => point_json(at::<CGPoint>(mem, addr)),
        "size" => size_json(at::<CGSize>(mem, addr)),
        "rect" => {
            let rect = at::<CGRect>(mem, addr);
            json!([rect.origin.x, rect.origin.y, rect.size.width, rect.size.height])
        }
        "id" => {
            let bits = at::<u32>(mem, addr);
            let object = to_id(bits);
            if bits == 0 {
                Value::Null
            } else if env.objc.get_host_object(object).is_some() {
                let mut map = Map::new();
                map.insert("ptr".to_string(), json!(hex(bits)));
                map.insert("class".to_string(), json!(class_name_of(env, object)));
                if let Some(string) = string_value(env, object) {
                    map.insert("string".to_string(), json!(string));
                }
                Value::Object(map)
            } else {
                json!({ "ptr": hex(bits), "class": Value::Null })
            }
        }
        "cstr" => {
            let ptr = at::<u32>(mem, addr);
            if ptr < 0x1000 {
                Value::Null
            } else {
                match mem.cstr_at_utf8(ConstPtr::<u8>::from_bits(ptr)) {
                    Ok(s) => json!(s),
                    Err(_) => Value::Null,
                }
            }
        }
        _ => {
            return Err(format!(
                "unknown type {type_:?} (use bool, i8, u8, i16, u16, i32, u32, f32, f64, ptr, id, cstr, point, size or rect)"
            ))
        }
    })
}

/// `find`: list live objects by class name.
fn query_find(env: &mut Environment, request: &Value) -> Result<Value, String> {
    let wanted = get_str(request, "class")?;
    let subclasses = request
        .get("subclasses")
        .and_then(Value::as_bool)
        .unwrap_or(true);
    let limit = opt_u32(request, "limit", 100)? as usize;

    let mut found = Vec::new();
    let mut total = 0usize;
    let objects: Vec<id> = env.objc.all_objects().collect();
    for object in objects {
        if env.objc.is_class_object(object) {
            continue;
        }
        let class = ObjC::read_isa(object, &env.mem);
        let Some(name) = env.objc.try_get_class_name(class) else {
            continue;
        };
        let matches = name == wanted
            || (subclasses && env.objc.class_chain_names(class).iter().any(|n| n == wanted));
        if matches {
            total += 1;
            if found.len() < limit {
                found.push(json!({ "ptr": hex(object.to_bits()), "class": name }));
            }
        }
    }
    Ok(json!({ "objects": found, "total": total }))
}

/// `describe`: class chain and instance variable names of an object.
fn query_describe(env: &mut Environment, request: &Value) -> Result<Value, String> {
    let object = checked_object(env, get_ptr(request, "ptr")?)?;
    let class = ObjC::read_isa(object, &env.mem);
    let chain = env.objc.class_chain_names(class);
    let mut offsets = env.objc.class_ivar_offsets(class, &env.mem);
    offsets.sort_by_key(|&(_, offset)| offset);
    let ivars: Vec<Value> = offsets
        .into_iter()
        .map(|(name, offset)| json!({ "name": name, "offset": offset }))
        .collect();
    let mut result = Map::new();
    result.insert("ptr".to_string(), json!(hex(object.to_bits())));
    result.insert("classes".to_string(), json!(chain));
    result.insert("ivars".to_string(), json!(ivars));
    if let Some(string) = string_value(env, object) {
        result.insert("string".to_string(), json!(string));
    }
    Ok(Value::Object(result))
}

/// `read`: read an instance variable (`ptr` + `ivar`) or raw memory (`addr`).
/// `ivar` may be a dotted path through object references, e.g.
/// `gameNode.position_`.
fn query_read(env: &mut Environment, request: &Value) -> Result<Value, String> {
    let type_ = get_str(request, "type")?;
    if request.get("addr").is_some() {
        let addr = get_ptr(request, "addr")?;
        return Ok(json!({ "value": read_typed(env, addr, type_)? }));
    }
    let mut object = checked_object(env, get_ptr(request, "ptr")?)?;
    let path = get_str(request, "ivar")?;
    let mut parts = path.split('.').peekable();
    while let Some(part) = parts.next() {
        let ptr = ivar_ptr(env, object, part).ok_or_else(|| {
            format!(
                "class {} has no instance variable {:?}",
                class_name_of(env, object),
                part
            )
        })?;
        if parts.peek().is_none() {
            return Ok(json!({ "value": read_typed(env, ptr.to_bits(), type_)? }));
        }
        let next: u32 = env.mem.read(ptr.cast::<u32>());
        object = checked_object(env, next)
            .map_err(|e| format!("{part:?} does not hold an object: {e}"))?;
    }
    unreachable!()
}

/// Elements of a Cocos2D `CCArray` or a Foundation array.
fn array_elements(env: &mut Environment, array: id) -> Vec<id> {
    if array == nil || env.objc.get_host_object(array).is_none() {
        return Vec::new();
    }
    // CCArray (cocos2d 0.99.4+) wraps a C struct: { NSUInteger num, max;
    // id *arr; }. Read it directly so no guest code has to run.
    if class_name_of(env, array) == "CCArray" {
        if let Some(data) = read_ivar::<u32>(env, array, "data") {
            if data >= 0x1000 {
                let num: u32 = env.mem.read(ConstPtr::<u32>::from_bits(data));
                let arr: u32 = env.mem.read(ConstPtr::<u32>::from_bits(data + 8));
                if arr >= 0x1000 && num < 100_000 {
                    return (0..num)
                        .map(|i| to_id(env.mem.read(ConstPtr::<u32>::from_bits(arr + i * 4))))
                        .collect();
                }
            }
            return Vec::new();
        }
    }
    let class = ObjC::read_isa(array, &env.mem);
    if env.objc.class_chain_names(class).iter().any(|n| n == "NSArray") {
        let count_sel = env.objc.lookup_selector("count");
        let object_at_sel = env.objc.lookup_selector("objectAtIndex:");
        if let (Some(count_sel), Some(object_at_sel)) = (count_sel, object_at_sel) {
            let count: u32 = msg_send_no_type_checking(env, (array, count_sel));
            return (0..count.min(100_000))
                .map(|i| msg_send_no_type_checking(env, (array, object_at_sel, i)))
                .collect();
        }
    }
    Vec::new()
}

/// Describe a Cocos2D node and its children, reading instance variables only.
fn node_json(env: &mut Environment, node: id, depth: u32, budget: &mut u32) -> Value {
    if node == nil || env.objc.get_host_object(node).is_none() {
        return Value::Null;
    }
    let mut map = Map::new();
    map.insert("ptr".to_string(), json!(hex(node.to_bits())));
    map.insert("class".to_string(), json!(class_name_of(env, node)));
    {
        // Superclasses, so a client can tell what kind of node a custom
        // class is. The two root classes carry no information.
        let class = ObjC::read_isa(node, &env.mem);
        let supers: Vec<String> = env
            .objc
            .class_chain_names(class)
            .into_iter()
            .skip(1)
            .filter(|name| name != "NSObject" && name != "CCNode")
            .collect();
        if !supers.is_empty() {
            map.insert("supers".to_string(), json!(supers));
        }
    }
    if let Some(position) = read_ivar::<CGPoint>(env, node, "position_") {
        map.insert("pos".to_string(), point_json(position));
    }
    if let Some(size) = read_ivar::<CGSize>(env, node, "contentSize_") {
        map.insert("size".to_string(), size_json(size));
    }
    if let Some(anchor) = read_ivar::<CGPoint>(env, node, "anchorPoint_") {
        map.insert("anchor".to_string(), point_json(anchor));
    }
    if let Some(anchor) = read_ivar::<CGPoint>(env, node, "anchorPointInPixels_") {
        map.insert("anchor_px".to_string(), point_json(anchor));
    }
    if let Some(relative) = read_ivar::<u8>(env, node, "isRelativeAnchorPoint_") {
        map.insert("rel_anchor".to_string(), json!(relative != 0));
    }
    if let Some(visible) = read_ivar::<u8>(env, node, "visible_") {
        map.insert("visible".to_string(), json!(visible != 0));
    }
    if let Some(tag) = read_ivar::<i32>(env, node, "tag_") {
        map.insert("tag".to_string(), json!(tag));
    }
    if let Some(z) = read_ivar::<i32>(env, node, "zOrder_") {
        map.insert("z".to_string(), json!(z));
    }
    if let (Some(x), Some(y)) = (
        read_ivar::<f32>(env, node, "scaleX_"),
        read_ivar::<f32>(env, node, "scaleY_"),
    ) {
        if x != 1.0 || y != 1.0 {
            map.insert("scale".to_string(), json!([x, y]));
        }
    }
    if let Some(opacity) = read_ivar::<u8>(env, node, "opacity_") {
        if opacity != 255 {
            map.insert("opacity".to_string(), json!(opacity));
        }
    }
    if let Some(enabled) = read_ivar::<u8>(env, node, "isEnabled_") {
        map.insert("enabled".to_string(), json!(enabled != 0));
    }
    if let Some(string) = read_ivar::<u32>(env, node, "string_") {
        if let Some(string) = string_value(env, to_id(string)) {
            map.insert("string".to_string(), json!(string));
        }
    }
    let children = read_ivar::<u32>(env, node, "children_")
        .map(|children| array_elements(env, to_id(children)))
        .unwrap_or_default();
    if !children.is_empty() {
        if depth == 0 || *budget == 0 {
            map.insert("child_count".to_string(), json!(children.len()));
        } else {
            let mut list = Vec::new();
            for child in children {
                if *budget == 0 {
                    break;
                }
                *budget -= 1;
                list.push(node_json(env, child, depth - 1, budget));
            }
            map.insert("children".to_string(), Value::Array(list));
        }
    }
    Value::Object(map)
}

/// `nodes`: the Cocos2D scene graph, from a given node or the running scene.
fn query_nodes(env: &mut Environment, request: &Value) -> Result<Value, String> {
    let depth = opt_u32(request, "depth", 8)?;
    let mut budget = opt_u32(request, "max_nodes", 2000)?;
    let root = if request.get("ptr").is_some() {
        checked_object(env, get_ptr(request, "ptr")?)?
    } else {
        // Find the director without calling +sharedDirector, which would
        // create one as a side effect if the app hasn't yet.
        let objects: Vec<id> = env.objc.all_objects().collect();
        let mut scene = nil;
        for object in objects {
            if env.objc.is_class_object(object) {
                continue;
            }
            let class = ObjC::read_isa(object, &env.mem);
            if !env.objc.class_chain_names(class).iter().any(|n| n == "CCDirector") {
                continue;
            }
            if let Some(running) = read_ivar::<u32>(env, object, "runningScene_") {
                scene = to_id(running);
                break;
            }
        }
        if scene == nil {
            return Err("no running Cocos2D scene found".to_string());
        }
        scene
    };
    let tree = node_json(env, root, depth, &mut budget);
    Ok(json!({ "root": tree, "truncated": budget == 0 }))
}

/// Describe a UIKit view and its subviews.
fn view_json(env: &mut Environment, view: id, window: id, depth: u32, budget: &mut u32) -> Value {
    if view == nil || env.objc.get_host_object(view).is_none() {
        return Value::Null;
    }
    let mut map = Map::new();
    map.insert("ptr".to_string(), json!(hex(view.to_bits())));
    map.insert("class".to_string(), json!(class_name_of(env, view)));
    let frame: CGRect = crate::objc::msg![env; view frame];
    map.insert(
        "frame".to_string(),
        json!([frame.origin.x, frame.origin.y, frame.size.width, frame.size.height]),
    );
    let hidden: bool = crate::objc::msg![env; view isHidden];
    if hidden {
        map.insert("hidden".to_string(), json!(true));
    }
    // Where the middle of the view is on the screen as the user sees it, in
    // the co-ordinates `tap` takes. Views can be rotated (an alert in a
    // landscape app is), so this is not simply a sum of frame origins.
    let bounds: CGRect = crate::objc::msg![env; view bounds];
    let middle = CGPoint {
        x: bounds.origin.x + bounds.size.width / 2.0,
        y: bounds.origin.y + bounds.size.height / 2.0,
    };
    let in_window: CGPoint = if view == window {
        middle
    } else {
        crate::objc::msg![env; view convertPoint:middle toView:window]
    };
    let (x, y) = env
        .window()
        .touch_coords_to_control_point((in_window.x, in_window.y));
    map.insert("screen".to_string(), json!([x.round(), y.round()]));
    // What a label says and what a button is called.
    let classes = env.objc.class_chain_names(ObjC::read_isa(view, &env.mem));
    let is_a = |name: &str| classes.iter().any(|class| class == name);
    if is_a("UILabel") || is_a("UITextField") {
        let text: id = crate::objc::msg![env; view text];
        if let Some(text) = string_value(env, text) {
            map.insert("text".to_string(), json!(text));
        }
    }
    if is_a("UIButton") {
        let title: id = crate::objc::msg![env; view currentTitle];
        if let Some(title) = string_value(env, title) {
            map.insert("title".to_string(), json!(title));
        }
    }
    if is_a("UIControl") {
        let enabled: bool = crate::objc::msg![env; view isEnabled];
        map.insert("enabled".to_string(), json!(enabled));
    }
    let subviews: id = crate::objc::msg![env; view subviews];
    let subviews = array_elements(env, subviews);
    if !subviews.is_empty() {
        if depth == 0 || *budget == 0 {
            map.insert("child_count".to_string(), json!(subviews.len()));
        } else {
            let mut list = Vec::new();
            for subview in subviews {
                if *budget == 0 {
                    break;
                }
                *budget -= 1;
                list.push(view_json(env, subview, window, depth - 1, budget));
            }
            map.insert("children".to_string(), Value::Array(list));
        }
    }
    Value::Object(map)
}

/// `views`: the UIKit view hierarchy of every window.
fn query_views(env: &mut Environment, request: &Value) -> Result<Value, String> {
    let depth = opt_u32(request, "depth", 8)?;
    let mut budget = opt_u32(request, "max_nodes", 1000)?;
    let windows = crate::frameworks::uikit::all_windows(env);
    let mut list = Vec::new();
    for window in windows {
        list.push(view_json(env, window, window, depth, &mut budget));
    }
    Ok(json!({ "windows": list, "truncated": budget == 0 }))
}

/// `call`: send a message that takes no arguments to an object or class.
/// This runs guest code, so unlike the other queries it can have side effects.
fn query_call(env: &mut Environment, request: &Value) -> Result<Value, String> {
    let selector = get_str(request, "selector")?;
    if selector.contains(':') {
        return Err("only selectors without arguments are supported".to_string());
    }
    let receiver = if let Some(class) = request.get("class").and_then(Value::as_str) {
        env.objc
            .class_if_known(class, &env.mem)
            .ok_or_else(|| format!("unknown class {class:?}"))?
    } else {
        checked_object(env, get_ptr(request, "ptr")?)?
    };
    let sel = env
        .objc
        .lookup_selector(selector)
        .ok_or_else(|| format!("unknown selector {selector:?}"))?;
    if !env.objc.object_has_method(&env.mem, receiver, sel) {
        return Err(format!(
            "{} does not respond to {:?}",
            class_name_of(env, receiver),
            selector
        ));
    }
    let returns = request
        .get("returns")
        .and_then(Value::as_str)
        .unwrap_or("id");
    // As a micro-benchmark of message dispatch, the message can be sent many
    // times; the time per send is reported.
    let repeat = opt_u32(request, "repeat", 0)?;
    if repeat > 0 {
        if matches!(returns, "point" | "size") {
            return Err("repeat is not supported for struct returns".to_string());
        }
        let begin = Instant::now();
        for _ in 0..repeat {
            let _: u32 = msg_send_no_type_checking(env, (receiver, sel));
        }
        let nanos = begin.elapsed().as_nanos() as f64 / repeat as f64;
        return Ok(json!({ "repeat": repeat, "ns_per_send": (nanos * 10.0).round() / 10.0 }));
    }
    Ok(json!({ "value": match returns {
        "void" => {
            let () = msg_send_no_type_checking(env, (receiver, sel));
            Value::Null
        }
        "bool" => {
            let value: bool = msg_send_no_type_checking(env, (receiver, sel));
            json!(value)
        }
        "i32" | "int" => {
            let value: i32 = msg_send_no_type_checking(env, (receiver, sel));
            json!(value)
        }
        "u32" => {
            let value: u32 = msg_send_no_type_checking(env, (receiver, sel));
            json!(value)
        }
        "f32" | "float" => {
            let value: f32 = msg_send_no_type_checking(env, (receiver, sel));
            json!(value)
        }
        "point" => {
            let value: CGPoint = msg_send_no_type_checking(env, (receiver, sel));
            point_json(value)
        }
        "size" => {
            let value: CGSize = msg_send_no_type_checking(env, (receiver, sel));
            size_json(value)
        }
        "id" => {
            let value: id = msg_send_no_type_checking(env, (receiver, sel));
            if value == nil {
                Value::Null
            } else if env.objc.get_host_object(value).is_some() {
                let mut map = Map::new();
                map.insert("ptr".to_string(), json!(hex(value.to_bits())));
                map.insert("class".to_string(), json!(class_name_of(env, value)));
                if let Some(string) = string_value(env, value) {
                    map.insert("string".to_string(), json!(string));
                }
                Value::Object(map)
            } else {
                json!({ "ptr": hex(value.to_bits()), "class": Value::Null })
            }
        }
        _ => return Err("returns must be void, bool, i32, u32, f32, point, size or id".to_string()),
    }}))
}
