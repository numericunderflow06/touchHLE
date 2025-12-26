/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `NSOperation` and `NSOperationQueue` stub implementations.

use crate::objc::{id, msg_class, nil, objc_classes, ClassExports, HostObject, NSZonePtr};

#[derive(Default)]
pub struct NSOperationQueueHostObject;
impl HostObject for NSOperationQueueHostObject {}

#[derive(Default)]
pub struct NSOperationHostObject {
    is_cancelled: bool,
    is_finished: bool,
    is_executing: bool,
}
impl HostObject for NSOperationHostObject {}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation NSOperation: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSOperationHostObject::default());
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    this
}

- (())start {
    log!("Warning: NSOperation start called but operation execution not implemented");
    // Mark as executing then finished
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_executing = true;
    // Immediately finish since we don't actually run anything
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_executing = false;
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_finished = true;
}

- (())main {
    // Subclasses override this - base implementation does nothing
    log_dbg!("NSOperation main called - base implementation");
}

- (())cancel {
    log_dbg!("NSOperation cancel");
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_cancelled = true;
}

- (bool)isCancelled {
    env.objc.borrow::<NSOperationHostObject>(this).is_cancelled
}

- (bool)isExecuting {
    env.objc.borrow::<NSOperationHostObject>(this).is_executing
}

- (bool)isFinished {
    env.objc.borrow::<NSOperationHostObject>(this).is_finished
}

- (bool)isReady {
    true // Always ready since we don't support dependencies
}

- (bool)isConcurrent {
    false // Default is non-concurrent
}

- (())setCompletionBlock:(id)_block {
    log!("Warning: NSOperation setCompletionBlock: ignored");
}

- (id)completionBlock {
    nil
}

- (())addDependency:(id)_op {
    log!("Warning: NSOperation addDependency: ignored");
}

- (())removeDependency:(id)_op {
    log!("Warning: NSOperation removeDependency: ignored");
}

- (id)dependencies {
    // Return empty array
    msg_class![env; NSArray array]
}

@end

@implementation NSInvocationOperation: NSOperation

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSOperationHostObject::default());
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithTarget:(id)_target
            selector:(id)_sel
              object:(id)_arg {
    log!("Warning: NSInvocationOperation initWithTarget:selector:object: - operation will not actually execute");
    this
}

- (id)result {
    nil
}

@end

@implementation NSOperationQueue: NSObject

+ (id)alloc {
    let host_object = Box::new(NSOperationQueueHostObject::default());
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    this
}

- (())addOperation:(id)_op {
    log!("Warning: NSOperationQueue addOperation: ignored");
}

- (())addOperationWithBlock:(id)_block {
    log!("Warning: NSOperationQueue addOperationWithBlock: ignored");
}

- (())setMaxConcurrentOperationCount:(i32)_count {
    log!("Warning: NSOperationQueue setMaxConcurrentOperationCount: ignored");
}

@end

};
