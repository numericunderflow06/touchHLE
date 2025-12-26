/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Objective-C Blocks Runtime support.
//!
//! Blocks are closures in Objective-C. They have a specific ABI that is
//! documented at: https://clang.llvm.org/docs/Block-ABI-Apple.html
//!
//! The key structures are:
//! - __NSConcreteGlobalBlock: class for blocks that don't capture any state
//! - __NSConcreteStackBlock: class for blocks that capture state
//!
//! When a block is invoked, the runtime calls through the `invoke` function
//! pointer in the block structure, not through objc_msgSend.

use super::{id, msg, objc_classes, ClassExports, TrivialHostObject, NSZonePtr};
use crate::mem::MutVoidPtr;

/// Block classes.
///
/// In the real runtime, blocks are special objects that contain an invoke
/// function pointer. The class is used mainly for retain/release semantics.
pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

// NSBlock is the abstract base class for all block types.
// In Apple's runtime, this inherits from NSObject.
@implementation NSBlock: NSObject

+ (id)alloc {
    log!("Warning: NSBlock alloc called directly - blocks should be created by the compiler");
    env.objc.alloc_object(this, Box::new(TrivialHostObject), &mut env.mem)
}

+ (id)allocWithZone:(NSZonePtr)_zone {
    log!("Warning: NSBlock allocWithZone: called directly");
    env.objc.alloc_object(this, Box::new(TrivialHostObject), &mut env.mem)
}

- (id)init {
    this
}

- (id)copy {
    // For blocks, copy returns the same block (after retain for stack blocks)
    // Global blocks don't need copying
    log_dbg!("NSBlock copy called");
    this
}

- (id)copyWithZone:(MutVoidPtr)_zone {
    log_dbg!("NSBlock copyWithZone: called");
    this
}

@end

// __NSGlobalBlock__ is the class for global blocks (blocks that don't capture state).
// These are allocated in static memory and never deallocated.
@implementation __NSGlobalBlock__: NSBlock

- (id)retain {
    // Global blocks are never deallocated, so retain is a no-op
    this
}

- (())release {
    // Global blocks are never deallocated
}

- (id)autorelease {
    // Global blocks are never deallocated
    this
}

- (id)copy {
    // Copying a global block just returns itself
    this
}

- (id)copyWithZone:(MutVoidPtr)_zone {
    this
}

@end

// __NSStackBlock__ is the class for stack blocks (blocks that capture state).
// These are allocated on the stack and must be copied to the heap if they
// need to outlive the scope.
@implementation __NSStackBlock__: NSBlock

- (id)copy {
    // TODO: Properly implement block copying (allocate on heap, copy captured vars)
    // For now, just log and return self
    log!("Warning: __NSStackBlock__ copy not fully implemented");
    this
}

- (id)copyWithZone:(MutVoidPtr)_zone {
    log!("Warning: __NSStackBlock__ copyWithZone: not fully implemented");
    this
}

@end

// __NSMallocBlock__ is the class for heap-allocated blocks (after copy from stack)
@implementation __NSMallocBlock__: NSBlock

- (id)copy {
    // Copying a malloc block increments refcount and returns self
    () = msg![env; this retain];
    this
}

- (id)copyWithZone:(MutVoidPtr)_zone {
    () = msg![env; this retain];
    this
}

@end

};
