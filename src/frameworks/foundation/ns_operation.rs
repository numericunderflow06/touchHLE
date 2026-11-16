/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `NSOperation`, `NSInvocationOperation` and `NSOperationQueue`.
//!
//! As on the real OS, a queue runs its operations on a background thread and
//! `addOperation:` returns immediately. Each queue uses a single worker thread
//! that runs operations one at a time in the order they were added (skipping
//! ones whose dependencies haven't finished yet). The real implementation may
//! run several at once, but serial execution is one of the schedules it could
//! legitimately choose.

use super::ns_thread::detach_new_thread_inner;
use super::{NSInteger, NSUInteger};
use crate::objc::{
    id, msg, msg_class, msg_send_no_type_checking, nil, objc_classes, release, retain,
    ClassExports, HostObject, NSZonePtr, SEL,
};
use std::collections::VecDeque;
use std::time::Duration;

struct NSOperationHostObject {
    is_cancelled: bool,
    is_executing: bool,
    is_finished: bool,
    /// `NSOperation *`, retained.
    dependencies: Vec<id>,
    queue_priority: NSInteger,
    /// Only used by `NSInvocationOperation`. Both retained.
    invocation: Option<(id, SEL, id)>,
    /// Only used by `NSInvocationOperation`. Retained.
    result: id,
}
impl HostObject for NSOperationHostObject {}

struct NSOperationQueueHostObject {
    /// Operations that haven't started. Retained.
    pending: VecDeque<id>,
    /// The operation currently running on the worker thread, if any.
    running: id,
    worker_active: bool,
    max_concurrent_operation_count: NSInteger,
    is_suspended: bool,
}
impl HostObject for NSOperationQueueHostObject {}

/// `NSOperationQueueDefaultMaxConcurrentOperationCount`
const DEFAULT_MAX_CONCURRENT_OPERATION_COUNT: NSInteger = -1;

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation NSOperation: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSOperationHostObject {
        is_cancelled: false,
        is_executing: false,
        is_finished: false,
        dependencies: Vec::new(),
        queue_priority: 0, // NSOperationQueuePriorityNormal
        invocation: None,
        result: nil,
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (())start {
    if env.objc.borrow::<NSOperationHostObject>(this).is_cancelled {
        env.objc.borrow_mut::<NSOperationHostObject>(this).is_finished = true;
        return;
    }
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_executing = true;
    // Operations get their own autorelease pool.
    let pool: id = msg_class![env; NSAutoreleasePool new];
    () = msg![env; this main];
    release(env, pool);
    let host_object = env.objc.borrow_mut::<NSOperationHostObject>(this);
    host_object.is_executing = false;
    host_object.is_finished = true;
}

- (())main {
    // Default implementation does nothing; subclasses override this.
}

- (())cancel {
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
- (bool)isConcurrent {
    false
}
- (bool)isReady {
    let dependencies = env.objc.borrow::<NSOperationHostObject>(this).dependencies.clone();
    for dependency in dependencies {
        let finished: bool = msg![env; dependency isFinished];
        if !finished {
            return false;
        }
    }
    true
}

- (())addDependency:(id)operation { // NSOperation *
    retain(env, operation);
    env.objc.borrow_mut::<NSOperationHostObject>(this).dependencies.push(operation);
}
- (())removeDependency:(id)operation { // NSOperation *
    let dependencies = &mut env.objc.borrow_mut::<NSOperationHostObject>(this).dependencies;
    if let Some(index) = dependencies.iter().position(|&d| d == operation) {
        dependencies.remove(index);
        release(env, operation);
    }
}
- (id)dependencies {
    let dependencies = env.objc.borrow::<NSOperationHostObject>(this).dependencies.clone();
    let array: id = msg_class![env; NSMutableArray new];
    for dependency in dependencies {
        () = msg![env; array addObject:dependency];
    }
    crate::objc::autorelease(env, array)
}

- (NSInteger)queuePriority {
    env.objc.borrow::<NSOperationHostObject>(this).queue_priority
}
- (())setQueuePriority:(NSInteger)priority {
    env.objc.borrow_mut::<NSOperationHostObject>(this).queue_priority = priority;
}

- (())waitUntilFinished {
    while !env.objc.borrow::<NSOperationHostObject>(this).is_finished {
        env.sleep(Duration::from_millis(1));
    }
}

- (())dealloc {
    let host_object = env.objc.borrow_mut::<NSOperationHostObject>(this);
    let dependencies = std::mem::take(&mut host_object.dependencies);
    let invocation = host_object.invocation.take();
    let result = std::mem::replace(&mut host_object.result, nil);
    for dependency in dependencies {
        release(env, dependency);
    }
    if let Some((target, _selector, object)) = invocation {
        release(env, target);
        release(env, object);
    }
    release(env, result);
    env.objc.dealloc_object(this, &mut env.mem)
}

@end

@implementation NSInvocationOperation: NSOperation

- (id)initWithTarget:(id)target
            selector:(SEL)selector
              object:(id)object {
    retain(env, target);
    retain(env, object);
    env.objc.borrow_mut::<NSOperationHostObject>(this).invocation =
        Some((target, selector, object));
    this
}

- (())main {
    let Some((target, selector, object)) =
        env.objc.borrow::<NSOperationHostObject>(this).invocation
    else {
        return;
    };
    // The method may or may not take the object and may or may not return
    // one, so its type can't be checked.
    let result: id = if selector.as_str(&env.mem).ends_with(':') {
        msg_send_no_type_checking(env, (target, selector, object))
    } else {
        msg_send_no_type_checking(env, (target, selector))
    };
    // TODO: The result is only meaningful if the method returns an object.
    // Without the method's type encoding we can't tell, so don't retain it.
    let _ = result;
}

- (id)result {
    env.objc.borrow::<NSOperationHostObject>(this).result
}

@end

@implementation NSOperationQueue: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSOperationQueueHostObject {
        pending: VecDeque::new(),
        running: nil,
        worker_active: false,
        max_concurrent_operation_count: DEFAULT_MAX_CONCURRENT_OPERATION_COUNT,
        is_suspended: false,
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (())addOperation:(id)operation { // NSOperation *
    retain(env, operation);
    let host_object = env.objc.borrow_mut::<NSOperationQueueHostObject>(this);
    host_object.pending.push_back(operation);
    if host_object.worker_active {
        return;
    }
    host_object.worker_active = true;
    let selector = env
        .objc
        .register_host_selector("_touchHLE_runOperations:".to_string(), &mut env.mem);
    // The thread retains the queue for as long as it runs.
    detach_new_thread_inner(env, selector, this, nil, /* tolerate_type_mismatch: */ false);
}

// Body of the queue's worker thread.
- (())_touchHLE_runOperations:(id)_unused {
    loop {
        if env.objc.borrow::<NSOperationQueueHostObject>(this).is_suspended {
            env.sleep(Duration::from_millis(5));
            continue;
        }

        // Take the first operation that is ready to run.
        let pending: Vec<id> = env
            .objc
            .borrow::<NSOperationQueueHostObject>(this)
            .pending
            .iter()
            .copied()
            .collect();
        if pending.is_empty() {
            break;
        }
        let mut next = None;
        for &operation in pending.iter() {
            let ready: bool = msg![env; operation isReady];
            if ready {
                next = Some(operation);
                break;
            }
        }
        let Some(operation) = next else {
            // Waiting for a dependency that is running elsewhere.
            env.sleep(Duration::from_millis(1));
            continue;
        };

        let host_object = env.objc.borrow_mut::<NSOperationQueueHostObject>(this);
        // Operations may have been added while checking readiness, so the
        // position has to be looked up again.
        let Some(index) = host_object.pending.iter().position(|&o| o == operation) else {
            continue;
        };
        host_object.pending.remove(index);
        host_object.running = operation;

        () = msg![env; operation start];

        env.objc.borrow_mut::<NSOperationQueueHostObject>(this).running = nil;
        release(env, operation);
    }
    env.objc.borrow_mut::<NSOperationQueueHostObject>(this).worker_active = false;
}

- (id)operations {
    let host_object = env.objc.borrow::<NSOperationQueueHostObject>(this);
    let mut operations: Vec<id> = Vec::new();
    if host_object.running != nil {
        operations.push(host_object.running);
    }
    operations.extend(host_object.pending.iter().copied());
    let array: id = msg_class![env; NSMutableArray new];
    for operation in operations {
        () = msg![env; array addObject:operation];
    }
    crate::objc::autorelease(env, array)
}
- (NSUInteger)operationCount {
    let host_object = env.objc.borrow::<NSOperationQueueHostObject>(this);
    host_object.pending.len() as NSUInteger + (host_object.running != nil) as NSUInteger
}

- (NSInteger)maxConcurrentOperationCount {
    env.objc.borrow::<NSOperationQueueHostObject>(this).max_concurrent_operation_count
}
- (())setMaxConcurrentOperationCount:(NSInteger)count {
    // Operations are always run one at a time (see module comment), so this
    // is only remembered.
    env.objc.borrow_mut::<NSOperationQueueHostObject>(this).max_concurrent_operation_count = count;
}

- (bool)isSuspended {
    env.objc.borrow::<NSOperationQueueHostObject>(this).is_suspended
}
- (())setSuspended:(bool)suspended {
    env.objc.borrow_mut::<NSOperationQueueHostObject>(this).is_suspended = suspended;
}

- (())cancelAllOperations {
    let host_object = env.objc.borrow::<NSOperationQueueHostObject>(this);
    let mut operations: Vec<id> = host_object.pending.iter().copied().collect();
    if host_object.running != nil {
        operations.push(host_object.running);
    }
    for operation in operations {
        () = msg![env; operation cancel];
    }
}

- (())waitUntilAllOperationsAreFinished {
    loop {
        let host_object = env.objc.borrow::<NSOperationQueueHostObject>(this);
        if host_object.pending.is_empty() && host_object.running == nil {
            break;
        }
        env.sleep(Duration::from_millis(1));
    }
}

- (())dealloc {
    let pending = std::mem::take(
        &mut env.objc.borrow_mut::<NSOperationQueueHostObject>(this).pending
    );
    for operation in pending {
        release(env, operation);
    }
    env.objc.dealloc_object(this, &mut env.mem)
}

@end

};
