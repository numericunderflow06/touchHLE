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

    // Scroll game world via accelerometer tilt.
    // child[0] = backgrounds (CCNode), child[1] = entities+HUD (CCNode)
    // Strategy: scroll child[0] and child[1] together, then compensate HUD
    // sub-children within child[1] so they stay fixed on screen.
    // HUD identification: CDEButton, CDELabelAtlas, CDELabel, CDEProgressBar,
    // CDEColorNode, and CDESprite at HUD y-positions (y<50 or y>280).
    {
        use crate::frameworks::core_graphics::CGPoint;
        static SCROLL_POS: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0); // f32 bits
        static LAST_DELEGATE: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

        // Reset scroll when delegate (MainGameLayer) changes (new level loaded)
        let delegate_bits = delegate.to_bits();
        let prev_delegate = LAST_DELEGATE.swap(delegate_bits, std::sync::atomic::Ordering::Relaxed);
        if prev_delegate != 0 && prev_delegate != delegate_bits {
            log!("[DIAG-SCROLL] Delegate changed ({:#x} -> {:#x}), resetting scroll", prev_delegate, delegate_bits);
            SCROLL_POS.store(0u32, std::sync::atomic::Ordering::Relaxed);
        }

        let children: id = msg![env; delegate children];
        if children != nil {
            let count: u32 = msg![env; children count];

            // Compute scroll from tilt
            let scroll_speed = 300.0f32;
            let dt = 1.0f32 / 60.0;
            let velocity = x as f32 * scroll_speed * dt;
            let cur_bits = SCROLL_POS.load(std::sync::atomic::Ordering::Relaxed);
            let cur_scroll = f32::from_bits(cur_bits);
            let new_scroll = (cur_scroll - velocity).clamp(-1000.0, 0.0);
            SCROLL_POS.store(new_scroll.to_bits(), std::sync::atomic::Ordering::Relaxed);

            // Scroll child[0] (backgrounds) and child[1] (entities+HUD)
            for i in 0..2u32.min(count) {
                let child: id = msg![env; children objectAtIndex:i];
                let pos = CGPoint { x: new_scroll, y: 0.0 };
                let _: () = msg![env; child setPosition:pos];
            }

            // Compensate HUD elements within child[1] so they stay fixed
            if count > 1 {
                let child1: id = msg![env; children objectAtIndex:(1u32)];
                let sub_children: id = msg![env; child1 children];
                if sub_children != nil {
                    let sub_count: u32 = msg![env; sub_children count];
                    // Collect HUD nodes to compensate (can't borrow env during iteration)
                    let mut hud_nodes: Vec<(id, f32, f32)> = Vec::new();
                    for i in 0..sub_count {
                        let sub: id = msg![env; sub_children objectAtIndex:i];
                        let sub_isa = crate::objc::ObjC::read_isa(sub, &env.mem);
                        let sub_class = env.objc.get_class_name(sub_isa).to_string();
                        let sub_pos: CGPoint = msg![env; sub position];

                        // HUD elements: buttons, labels, progress bars, color nodes
                        // Also CDESprite at HUD y-positions (bottom bar y<50, top bar y>280)
                        let is_hud = match sub_class.as_str() {
                            "CDEButton" | "CDELabelAtlas" | "CDELabel"
                            | "CDEProgressBar" | "CDEColorNode" => true,
                            "CDESprite" => sub_pos.y < 50.0 || sub_pos.y > 280.0,
                            _ => false,
                        };
                        if is_hud {
                            hud_nodes.push((sub, sub_pos.x, sub_pos.y));
                        }
                    }
                    // Apply compensation: shift HUD nodes by -scroll to cancel parent scroll
                    for (node, orig_x, orig_y) in hud_nodes {
                        let compensated = CGPoint { x: orig_x - new_scroll, y: orig_y };
                        let _: () = msg![env; node setPosition:compensated];
                    }
                }
            }
        }
    }

    release(env, pool);

    env.framework_state.uikit.ui_accelerometer.due_by
}
