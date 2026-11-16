/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `CADisplayLink` - a timer object that synchronizes drawing to the display refresh rate.
//!
//! Integrates with `NSRunLoop` to fire callbacks at ~60fps (or at a reduced
//! rate based on `frameInterval`).

use crate::frameworks::core_foundation::time::CFTimeInterval;
use crate::frameworks::foundation::ns_run_loop;
use crate::objc::{
    id, msg, msg_class, msg_send, nil, objc_classes, release, retain, ClassExports, HostObject,
    NSZonePtr, SEL,
};
use crate::Environment;

pub(crate) struct CADisplayLinkHostObject {
    target: id,
    selector: Option<SEL>,
    paused: bool,
    frame_interval: i32,
    /// Frame counter for frame_interval support (fire every N frames)
    frame_counter: i32,
    /// Weak reference to the run loop this display link is added to
    run_loop: id,
}
impl HostObject for CADisplayLinkHostObject {}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation CADisplayLink: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(CADisplayLinkHostObject {
        target: nil,
        selector: None,
        paused: false,
        frame_interval: 1,
        frame_counter: 0,
        run_loop: nil,
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

+ (id)displayLinkWithTarget:(id)target selector:(SEL)sel {
    log!("[CADisplayLink] displayLinkWithTarget:{:?} selector:{:?}", target, sel);
    let new: id = msg![env; this alloc];
    let host_obj = env.objc.borrow_mut::<CADisplayLinkHostObject>(new);
    host_obj.target = target;
    host_obj.selector = Some(sel);
    // Note: We don't retain target to avoid reference cycles, matching Apple's behavior
    new
}

- (())addToRunLoop:(id)run_loop forMode:(id)_mode {
    log!("[CADisplayLink] addToRunLoop:{:?} forMode:{:?}", run_loop, _mode);
    let host_obj = env.objc.borrow_mut::<CADisplayLinkHostObject>(this);
    host_obj.run_loop = run_loop;
    ns_run_loop::add_display_link(env, run_loop, this);
}

- (())removeFromRunLoop:(id)run_loop forMode:(id)_mode {
    log!("[CADisplayLink] removeFromRunLoop:{:?} forMode:{:?}", run_loop, _mode);
    ns_run_loop::remove_display_link(env, run_loop, this);
    let host_obj = env.objc.borrow_mut::<CADisplayLinkHostObject>(this);
    host_obj.run_loop = nil;
}

- (())invalidate {
    log!("[CADisplayLink] invalidate");
    let host_obj = env.objc.borrow::<CADisplayLinkHostObject>(this);
    let run_loop = host_obj.run_loop;
    if run_loop != nil {
        ns_run_loop::remove_display_link(env, run_loop, this);
    }
    let host_obj = env.objc.borrow_mut::<CADisplayLinkHostObject>(this);
    host_obj.target = nil;
    host_obj.paused = true;
    host_obj.run_loop = nil;
}

- (bool)isPaused {
    env.objc.borrow::<CADisplayLinkHostObject>(this).paused
}

- (())setPaused:(bool)paused {
    log!("[CADisplayLink] setPaused:{}", paused);
    env.objc.borrow_mut::<CADisplayLinkHostObject>(this).paused = paused;
}

- (i32)frameInterval {
    env.objc.borrow::<CADisplayLinkHostObject>(this).frame_interval
}

- (())setFrameInterval:(i32)interval {
    log!("[CADisplayLink] setFrameInterval:{}", interval);
    env.objc.borrow_mut::<CADisplayLinkHostObject>(this).frame_interval = interval;
}

- (CFTimeInterval)timestamp {
    // Return current time as a reasonable approximation
    crate::frameworks::core_animation::CACurrentMediaTime(env)
}

- (CFTimeInterval)duration {
    // Return 1/60 second (60fps) as the frame duration
    1.0 / 60.0
}

@end

};

/// For use by `NSRunLoop`: fire the display link's callback if it's not paused
/// and the frame interval has elapsed.
pub fn handle_display_link(env: &mut Environment, display_link: id) {
    let host_obj = env.objc.borrow::<CADisplayLinkHostObject>(display_link);
    let target = host_obj.target;
    let selector = host_obj.selector;
    let paused = host_obj.paused;
    let frame_interval = host_obj.frame_interval;

    if paused || target == nil {
        return;
    }

    let selector = match selector {
        Some(sel) => sel,
        None => return,
    };

    // Handle frame interval: only fire every N frames
    let counter = env
        .objc
        .borrow_mut::<CADisplayLinkHostObject>(display_link)
        .frame_counter;
    let new_counter = counter + 1;
    if new_counter < frame_interval {
        env.objc
            .borrow_mut::<CADisplayLinkHostObject>(display_link)
            .frame_counter = new_counter;
        return;
    }
    env.objc
        .borrow_mut::<CADisplayLinkHostObject>(display_link)
        .frame_counter = 0;

    // Retain display_link during callback in case it's invalidated
    retain(env, display_link);

    let pool: id = msg_class![env; NSAutoreleasePool new];

    // Signature: - (void)selector:(CADisplayLink *)sender
    let _: () = msg_send(env, (target, selector, display_link));

    release(env, pool);
    release(env, display_link);
}
