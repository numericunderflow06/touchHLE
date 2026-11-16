/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Where does the emulator's time go?
//!
//! Off unless a control client asks for it; while off, each hook costs one
//! relaxed atomic load. While on, wall-clock time is split between:
//!
//! - guest code (the app's own ARM code), attributed to the guest address
//!   where each stretch of execution ended: the return address of the host
//!   call that ended it, or the program counter if its time slice ran out;
//! - each host function and host-implemented Objective-C method, exclusive
//!   of the guest code and other host calls made from inside it;
//! - host code that runs outside any such call (on the main thread that is
//!   the run loop: events, timers, compositing);
//! - everything between one guest thread being suspended and the next being
//!   resumed: scheduling, and sleeping when no thread has work.
//!
//! Message sends to methods implemented by the app are counted (not timed).
//!
//! The accounting works on transitions: the time since the previous
//! transition belongs to whatever was running in between. That needs one
//! clock reading per transition, and the two transitions that happen for
//! practically every host call (guest code stops, host function starts; host
//! function returns, guest code resumes) share one reading each. The
//! remaining cost per transition is measured and reported, so that a reader
//! can judge how much the profiler itself inflated the numbers.

use crate::objc::{PointerMap, SEL};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

static ENABLED: AtomicBool = AtomicBool::new(false);

#[inline(always)]
pub fn enabled() -> bool {
    ENABLED.load(Ordering::Relaxed)
}

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub enum Key {
    /// Index of a linked host function, see
    /// [crate::dyld::Dyld::linked_function_name].
    Function(u32),
    /// Host implementation of a method: class it was found on, and selector.
    Method(u32, SEL),
}

/// A cheap monotonic clock. Its unit is converted to time at the end, by
/// comparing against [Instant] over the whole profile.
#[inline(always)]
fn ticks() -> u64 {
    #[cfg(target_arch = "x86_64")]
    {
        // SAFETY: RDTSC is available on every x86-64 processor.
        unsafe { core::arch::x86_64::_rdtsc() }
    }
    #[cfg(not(target_arch = "x86_64"))]
    {
        use std::sync::OnceLock;
        static BASE: OnceLock<Instant> = OnceLock::new();
        BASE.get_or_init(Instant::now).elapsed().as_nanos() as u64
    }
}

#[derive(Default, Clone, Copy)]
struct RawStat {
    calls: u64,
    ticks: u64,
}

#[derive(Default, Clone, Copy)]
pub struct Stat {
    pub calls: u64,
    pub time: Duration,
}

pub struct Profile {
    pub wall: Duration,
    pub host: Vec<(Key, Stat)>,
    /// By guest address, see the module documentation.
    pub guest: Vec<(u32, Stat)>,
    pub guest_total: Duration,
    pub host_total: Duration,
    /// Message sends to guest methods, by class and selector.
    pub guest_messages: Vec<((u32, SEL), u64)>,
    /// Host code outside any profiled call, on the main thread.
    pub run_loop: Duration,
    /// The same on other threads.
    pub outside_other_threads: Duration,
    /// Between a thread being suspended and one being resumed.
    pub between_threads: Duration,
    /// Number of clock readings taken, and what each cost, bookkeeping
    /// included.
    pub transitions: u64,
    pub cost_per_transition: Duration,
}

#[derive(Default)]
struct State {
    /// Clock reading at the previous transition.
    last: u64,
    /// Guest code ran since `last` and stopped at this address, for a host
    /// call that is about to be reported.
    pending_guest: Option<u32>,
    /// The previous transition was a host function returning to guest code,
    /// so guest code resuming needs no clock reading of its own.
    resuming_guest: bool,
    /// Per guest thread: the host calls in progress, innermost last.
    stacks: Vec<Vec<Key>>,
    host: PointerMap<Key, RawStat>,
    guest: PointerMap<u32, RawStat>,
    guest_messages: PointerMap<(u32, SEL), u64>,
    guest_total: u64,
    outside_main: u64,
    outside_other: u64,
    between_threads: u64,
    transitions: u64,
}

impl State {
    /// Take a clock reading; returns the time since the previous one.
    #[inline(always)]
    fn lap(&mut self) -> u64 {
        let now = ticks();
        let elapsed = now.saturating_sub(self.last);
        self.last = now;
        self.transitions += 1;
        self.resuming_guest = false;
        elapsed
    }

    /// Account for time during which `thread` was running host code (unless
    /// guest code is known to have been running instead).
    #[inline(always)]
    fn host_ran(&mut self, thread: usize, elapsed: u64) {
        if let Some(address) = self.pending_guest.take() {
            self.guest_ran(address, elapsed);
        } else if let Some(key) = self.stacks.get(thread).and_then(|stack| stack.last()) {
            self.host.entry(*key).or_default().ticks += elapsed;
        } else if thread == 0 {
            self.outside_main += elapsed;
        } else {
            self.outside_other += elapsed;
        }
    }

    #[inline(always)]
    fn guest_ran(&mut self, address: u32, elapsed: u64) {
        let stat = self.guest.entry(address).or_default();
        stat.calls += 1;
        stat.ticks += elapsed;
        self.guest_total += elapsed;
    }

    #[inline(always)]
    fn enter(&mut self, thread: usize, key: Key) {
        let elapsed = self.lap();
        self.host_ran(thread, elapsed);
        if self.stacks.len() <= thread {
            self.stacks.resize_with(thread + 1, Vec::new);
        }
        self.stacks[thread].push(key);
        self.host.entry(key).or_default().calls += 1;
    }

    #[inline(always)]
    fn exit(&mut self, thread: usize, to_guest: bool) {
        let elapsed = self.lap();
        self.host_ran(thread, elapsed);
        // (A call that began before profiling did is not on the stack. Its
        // time was counted as outside any call, which is the best we can do.)
        if let Some(stack) = self.stacks.get_mut(thread) {
            stack.pop();
        }
        self.resuming_guest = to_guest;
    }
}

struct Running {
    started: Instant,
    started_ticks: u64,
    state: State,
}

static STATE: Mutex<Option<Box<Running>>> = Mutex::new(None);

pub fn start() {
    let now = ticks();
    *STATE.lock().unwrap() = Some(Box::new(Running {
        started: Instant::now(),
        started_ticks: now,
        state: State {
            last: now,
            ..Default::default()
        },
    }));
    ENABLED.store(true, Ordering::Relaxed);
}

pub fn stop() -> Option<Profile> {
    ENABLED.store(false, Ordering::Relaxed);
    let running = STATE.lock().unwrap().take()?;
    let wall = running.started.elapsed();
    let total_ticks = ticks().saturating_sub(running.started_ticks).max(1);
    let nanos_per_tick = wall.as_nanos() as f64 / total_ticks as f64;
    let time = |ticks: u64| Duration::from_nanos((ticks as f64 * nanos_per_tick) as u64);
    let stat = |raw: RawStat| Stat {
        calls: raw.calls,
        time: time(raw.ticks),
    };
    let state = running.state;

    // What does a transition cost? Measure the same code on scratch state,
    // going through the lock like the real hooks.
    let cost_per_transition = {
        const ROUNDS: u32 = 20_000;
        *STATE.lock().unwrap() = Some(Box::new(Running {
            started: Instant::now(),
            started_ticks: 0,
            state: State::default(),
        }));
        let begin = Instant::now();
        for i in 0..ROUNDS {
            with_state(|state| state.enter(0, Key::Function(i % 64)));
            with_state(|state| state.exit(0, true));
        }
        let cost = begin.elapsed() / (ROUNDS * 2);
        *STATE.lock().unwrap() = None;
        cost
    };

    Some(Profile {
        wall,
        host_total: time(state.host.values().map(|raw| raw.ticks).sum()),
        host: state.host.into_iter().map(|(key, raw)| (key, stat(raw))).collect(),
        guest: state
            .guest
            .into_iter()
            .map(|(address, raw)| (address, stat(raw)))
            .collect(),
        guest_total: time(state.guest_total),
        guest_messages: state.guest_messages.into_iter().collect(),
        run_loop: time(state.outside_main),
        outside_other_threads: time(state.outside_other),
        between_threads: time(state.between_threads),
        transitions: state.transitions,
        cost_per_transition,
    })
}

#[inline(always)]
fn with_state(f: impl FnOnce(&mut State)) {
    if let Some(running) = STATE.lock().unwrap().as_mut() {
        f(&mut running.state)
    }
}

/// A host function or method is about to run on guest thread `thread`.
pub fn enter(thread: usize, key: Key) {
    with_state(|state| state.enter(thread, key));
}

/// The host function or method most recently entered on `thread` returned.
/// `to_guest` says that guest code resumes right away (the function was
/// called by guest code through the dynamic linker's stubs).
pub fn exit(thread: usize, to_guest: bool) {
    with_state(|state| state.exit(thread, to_guest));
}

/// Guest code is about to run on `thread`.
pub fn guest_starts(thread: usize) {
    with_state(|state| {
        if state.resuming_guest {
            state.resuming_guest = false;
        } else {
            let elapsed = state.lap();
            state.host_ran(thread, elapsed);
        }
    });
}

/// Guest code stopped running at `address`. `host_call_follows` says that it
/// stopped in order to call a host function, in which case [enter] comes next.
pub fn guest_stopped(address: u32, host_call_follows: bool) {
    with_state(|state| {
        if host_call_follows {
            state.pending_guest = Some(address);
        } else {
            let elapsed = state.lap();
            state.pending_guest = None;
            state.guest_ran(address, elapsed);
        }
    });
}

/// `thread` is about to be suspended (sleeping, blocked, or out of time).
pub fn suspending(thread: usize) {
    with_state(|state| {
        let elapsed = state.lap();
        state.host_ran(thread, elapsed);
    });
}

/// A thread was resumed after being suspended.
pub fn resumed() {
    with_state(|state| {
        let elapsed = state.lap();
        state.between_threads += elapsed;
    });
}

/// A message was dispatched to a method implemented by the app.
pub fn guest_message(class: u32, selector: SEL) {
    with_state(|state| *state.guest_messages.entry((class, selector)).or_default() += 1);
}
