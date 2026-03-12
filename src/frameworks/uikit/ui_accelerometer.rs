/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIAccelerometer`.
//!
//! Useful resources:
//! - [Apple's documentation for UIAcceleration](https://developer.apple.com/documentation/uikit/uiacceleration) has a really nice diagram of how the accelerometer axes relate to an iPhone.

use crate::frameworks::foundation::NSTimeInterval;
use crate::objc::{
    autorelease, id, msg, msg_class, nil, objc_classes, release, ClassExports, HostObject,
    NSZonePtr, TrivialHostObject, SEL,
};
use crate::Environment;
use std::time::{Duration, Instant};

#[derive(Default)]
pub struct State {
    /// [UIAccelerometer sharedAccelerometer]
    shared_accelerometer: Option<id>,
    /// Something implementing UIAccelerometerDelegate, weak reference
    delegate: Option<id>,
    update_interval: Option<NSTimeInterval>,
    due_by: Option<Instant>,
}

type UIAccelerationValue = f64;

const DEFAULT_UPDATE_INTERVAL: f64 = 1.0 / 60.0;

struct UIAccelerationHostObject {
    x: UIAccelerationValue,
    y: UIAccelerationValue,
    z: UIAccelerationValue,
    timestamp: NSTimeInterval,
}
impl HostObject for UIAccelerationHostObject {}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

// This is a singleton.
@implementation UIAccelerometer: NSObject

+ (id)sharedAccelerometer {
    if let Some(accelerometer) =
        env.framework_state.uikit.ui_accelerometer.shared_accelerometer {
        accelerometer
    } else {
        let new = env.objc.alloc_static_object(
            this,
            Box::new(TrivialHostObject),
            &mut env.mem
        );
        env.framework_state.uikit.ui_accelerometer.shared_accelerometer = Some(new);
        new
   }
}
- (id)retain { this }
- (())release {}
- (id)autorelease { this }

// TODO: more accessors

- (id)delegate {
    env.framework_state.uikit.ui_accelerometer.delegate.unwrap_or(nil)
}
- (())setDelegate:(id)delegate {
    if delegate == nil {
        env.framework_state.uikit.ui_accelerometer.delegate = None;
    } else {
        env.framework_state.uikit.ui_accelerometer.delegate = Some(delegate);
        env.window().print_accelerometer_notice(&env.options);
    }
}

- (NSTimeInterval)updateInterval {
    env.framework_state.uikit.ui_accelerometer.update_interval.unwrap_or(DEFAULT_UPDATE_INTERVAL)
}
- (())setUpdateInterval:(NSTimeInterval)interval {
    // The system can limit this value, and must (some apps pass 0 and this can
    // cause a division-by-zero. 60Hz has been chosen here to match 60fps.
    let interval = interval.max(1.0 / 60.0);
    env.framework_state.uikit.ui_accelerometer.update_interval = Some(interval);
}

@end

@implementation UIAcceleration: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(UIAccelerationHostObject {
        x: 0.0,
        y: 0.0,
        z: 0.0,
        timestamp: 0.0,
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (UIAccelerationValue)x {
    env.objc.borrow::<UIAccelerationHostObject>(this).x
}
- (UIAccelerationValue)y {
    env.objc.borrow::<UIAccelerationHostObject>(this).y
}
- (UIAccelerationValue)z {
    env.objc.borrow::<UIAccelerationHostObject>(this).z
}
- (NSTimeInterval)timestamp {
    env.objc.borrow::<UIAccelerationHostObject>(this).timestamp
}

@end

};

/// For use by `NSRunLoop` via [super::handle_events]: check if an accelerometer
/// update is due and send one if appropriate.
///
/// Returns the time an accelerometer update is due, if any.
static ACCEL_LOG_COUNT: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

pub(super) fn handle_accelerometer(env: &mut Environment) -> Option<Instant> {
    let state = &mut env.framework_state.uikit.ui_accelerometer;

    let delegate = state.delegate?;

    let ns_interval = state.update_interval.unwrap_or(DEFAULT_UPDATE_INTERVAL);
    let rust_interval = Duration::from_secs_f64(ns_interval);

    let now = Instant::now();
    if let Some(due_by) = state.due_by {
        if due_by > now {
            return Some(due_by);
        }

        // See NSTimer implementation for a discussion of what this does.
        // I don't know if iPhone OS uses this approach for accelerometer
        // updates, but there's no obvious reason not to.
        let overdue_by = now.duration_since(due_by);
        // TODO: Use `.div_duration_f64()` once that is stabilized.
        let advance_by = (overdue_by.as_secs_f64() / ns_interval).max(1.0).ceil();
        assert!(advance_by == (advance_by as u32) as f64);
        let advance_by = advance_by as u32;
        if advance_by > 1 {
            log_dbg!("Warning: Accelerometer is lagging. It is overdue by {}s and has missed {} interval(s)!", overdue_by.as_secs_f64(), advance_by - 1);
        }
        let advance_by = rust_interval.checked_mul(advance_by).unwrap();
        let new_due_by = due_by.checked_add(advance_by).unwrap();
        state.due_by = Some(new_due_by);
    } else {
        // In Resident Evil 4 the delegate is set before it fully initializes.
        // If the first message is sent immediately, it crashes.
        // This change prevents it by not sending the first message until the
        // time interval first passes
        let new_due_by = now.checked_add(rust_interval).unwrap();
        state.due_by = Some(new_due_by);
        if new_due_by > now {
            return Some(new_due_by);
        }
    };

    // UIKit creates and drains autorelease pools when handling events.
    let pool: id = msg_class![env; NSAutoreleasePool new];

    let (x, y, z) = env.window().get_acceleration(&env.options);
    let timestamp: NSTimeInterval = {
        let process_info = msg_class![env; NSProcessInfo processInfo];
        msg![env; process_info systemUptime]
    };
    let acceleration: id = msg_class![env; UIAcceleration alloc];
    *env.objc.borrow_mut(acceleration) = UIAccelerationHostObject {
        x: x.into(),
        y: y.into(),
        z: z.into(),
        timestamp,
    };
    autorelease(env, acceleration);

    let accelerometer: id = msg_class![env; UIAccelerometer sharedAccelerometer];

    let count = ACCEL_LOG_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    if count < 10 || (x != 0.0 || y != 0.0) {
        log!(
            "[DIAG-ACCEL] #{} Sending [{:?} accelerometer:{:?} didAccelerate:{:?}] x={:.3} y={:.3} z={:.3}",
            count,
            delegate,
            accelerometer,
            acceleration,
            x, y, z,
        );
    }
    let sel: SEL = env
        .objc
        .register_host_selector("accelerometer:didAccelerate:".to_string(), &mut env.mem);
    let responds: bool = msg![env; delegate respondsToSelector:sel];
    if responds {
        let _: () = msg![env; delegate accelerometer:accelerometer
                                       didAccelerate:acceleration];
    } else {
        log!("[DIAG-ACCEL] delegate {:?} does NOT respond to accelerometer:didAccelerate:", delegate);
    }

    // Enumerate MainGameLayer children + force-scroll child[0] (game world node)
    {
        use crate::frameworks::core_graphics::CGPoint;
        static WORLD_NODE: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);
        static SCROLL_FRAME: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

        // One-time: find and log hierarchy, save child[0] pointer
        if WORLD_NODE.load(std::sync::atomic::Ordering::Relaxed) == 0 {
            let children: id = msg![env; delegate children];
            if children != nil {
                let count: u32 = msg![env; children count];
                log!("[DIAG-HIERARCHY] MainGameLayer {:?} has {} children:", delegate, count);
                let mut child_info: Vec<(id, String, i32)> = Vec::new();
                for i in 0..count {
                    let child: id = msg![env; children objectAtIndex:i];
                    let child_isa = crate::objc::ObjC::read_isa(child, &env.mem);
                    let class_name = env.objc.get_class_name(child_isa).to_string();
                    let tag: i32 = msg![env; child tag];
                    child_info.push((child, class_name, tag));
                }
                for (i, (child, class_name, tag)) in child_info.iter().enumerate() {
                    log!("[DIAG-HIERARCHY]   child[{}]: {:?} class={} tag={}", i, child, class_name, tag);
                }
                if count > 0 {
                    let first_child: id = msg![env; children objectAtIndex:(0u32)];
                    WORLD_NODE.store(first_child.to_bits(), std::sync::atomic::Ordering::Relaxed);
                    log!("[DIAG-SCROLL-HACK] Saved world node: {:?}", first_child);
                }
            }
            let parent: id = msg![env; delegate parent];
            if parent != nil {
                let parent_isa = crate::objc::ObjC::read_isa(parent, &env.mem);
                let pname = env.objc.get_class_name(parent_isa).to_string();
                log!("[DIAG-HIERARCHY] MainGameLayer parent: {:?} class={}", parent, pname);
            }
        }

        // Manual scroll: use accelerometer x-tilt (right-click drag) to scroll child[0]
        let world_bits = WORLD_NODE.load(std::sync::atomic::Ordering::Relaxed);
        if world_bits != 0 {
            // Use accel x value as scroll velocity (tilt left = scroll left, tilt right = scroll right)
            // x is the accelerometer reading: ~0 when level, positive when tilted right
            let scroll_speed = 300.0; // pixels per second at full tilt
            let dt = 1.0 / 60.0; // approximate frame time
            let velocity = x as f32 * scroll_speed * dt;

            // Accumulate scroll position
            let cur_bits = SCROLL_FRAME.load(std::sync::atomic::Ordering::Relaxed);
            let cur_scroll = f32::from_bits(cur_bits);
            let new_scroll = (cur_scroll - velocity).clamp(-1000.0, 0.0); // limit scroll range
            SCROLL_FRAME.store(new_scroll.to_bits(), std::sync::atomic::Ordering::Relaxed);

            let world_node = crate::objc::id::from_bits(world_bits);
            let pos = CGPoint { x: new_scroll, y: 0.0 };
            let _: () = msg![env; world_node setPosition:pos];
        }
    }

    release(env, pool);

    env.framework_state.uikit.ui_accelerometer.due_by
}
