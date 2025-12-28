/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `NSOperation` and `NSOperationQueue` implementations.
//!
//! Operations are executed synchronously on the main thread for simplicity.

use crate::abi::{CallFromHost, GuestFunction};
use crate::mem::{ConstVoidPtr, MutPtr, Ptr};
use crate::objc::{id, msg, msg_class, nil, objc_classes, retain, release, ClassExports, HostObject, NSZonePtr, SEL};

#[repr(C, packed)]
struct BlockLiteral {
    isa: ConstVoidPtr,
    flags: i32,
    reserved: i32,
    invoke: ConstVoidPtr,
}
unsafe impl crate::mem::SafeRead for BlockLiteral {}

fn invoke_block(env: &mut crate::Environment, block: ConstVoidPtr) {
    if block.is_null() {
        return;
    }
    let block_ptr: MutPtr<BlockLiteral> = Ptr::from_bits(block.to_bits());
    let block_literal = env.mem.read(block_ptr);
    if block_literal.invoke.is_null() {
        log!("Warning: Block has null invoke function");
        return;
    }
    let invoke_addr = block_literal.invoke.to_bits();
    log_dbg!("NSOperation: Invoking block at {:?}", block);
    let invoke_fn = GuestFunction::from_addr_with_thumb_bit(invoke_addr);
    let _: () = invoke_fn.call_from_host(env, (block,));
}

#[derive(Default)]
pub struct NSOperationQueueHostObject {
    max_concurrent_operations: i32,
}
impl HostObject for NSOperationQueueHostObject {}

#[derive(Default)]
pub struct NSOperationHostObject {
    is_cancelled: bool,
    is_finished: bool,
    is_executing: bool,
    completion_block: ConstVoidPtr,
}
impl HostObject for NSOperationHostObject {}

pub struct NSInvocationOperationHostObject {
    is_cancelled: bool,
    is_finished: bool,
    is_executing: bool,
    completion_block: ConstVoidPtr,
    target: id,
    selector: Option<SEL>,
    argument: id,
    result: id,
}
impl HostObject for NSInvocationOperationHostObject {}

pub struct NSBlockOperationHostObject {
    is_cancelled: bool,
    is_finished: bool,
    is_executing: bool,
    completion_block: ConstVoidPtr,
    execution_blocks: Vec<ConstVoidPtr>,
}
impl HostObject for NSBlockOperationHostObject {}

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
    let is_cancelled = env.objc.borrow::<NSOperationHostObject>(this).is_cancelled;
    if is_cancelled {
        env.objc.borrow_mut::<NSOperationHostObject>(this).is_finished = true;
        return;
    }
    log_dbg!("NSOperation start - executing main");
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_executing = true;
    () = msg![env; this main];
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_executing = false;
    env.objc.borrow_mut::<NSOperationHostObject>(this).is_finished = true;
    let completion_block = env.objc.borrow::<NSOperationHostObject>(this).completion_block;
    if !completion_block.is_null() {
        invoke_block(env, completion_block);
    }
}

- (())main {
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
    true
}

- (bool)isConcurrent {
    false
}

- (())setCompletionBlock:(id)block {
    let block_ptr = ConstVoidPtr::from_bits(block.to_bits());
    env.objc.borrow_mut::<NSOperationHostObject>(this).completion_block = block_ptr;
}

- (id)completionBlock {
    let block = env.objc.borrow::<NSOperationHostObject>(this).completion_block;
    id::from_bits(block.to_bits())
}

- (())addDependency:(id)_op {
    log!("Warning: NSOperation addDependency: ignored");
}

- (())removeDependency:(id)_op {
    log!("Warning: NSOperation removeDependency: ignored");
}

- (id)dependencies {
    msg_class![env; NSArray array]
}

@end

@implementation NSBlockOperation: NSOperation

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSBlockOperationHostObject {
        is_cancelled: false,
        is_finished: false,
        is_executing: false,
        completion_block: ConstVoidPtr::null(),
        execution_blocks: Vec::new(),
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

+ (id)blockOperationWithBlock:(id)block {
    let op: id = msg_class![env; NSBlockOperation alloc];
    let op: id = msg![env; op init];
    let block_ptr = ConstVoidPtr::from_bits(block.to_bits());
    if !block_ptr.is_null() {
        env.objc.borrow_mut::<NSBlockOperationHostObject>(op).execution_blocks.push(block_ptr);
    }
    op
}

- (id)init {
    this
}

- (())addExecutionBlock:(id)block {
    let block_ptr = ConstVoidPtr::from_bits(block.to_bits());
    if !block_ptr.is_null() {
        env.objc.borrow_mut::<NSBlockOperationHostObject>(this).execution_blocks.push(block_ptr);
    }
}

- (())start {
    let is_cancelled = env.objc.borrow::<NSBlockOperationHostObject>(this).is_cancelled;
    if is_cancelled {
        env.objc.borrow_mut::<NSBlockOperationHostObject>(this).is_finished = true;
        return;
    }
    log_dbg!("NSBlockOperation start - executing blocks");
    env.objc.borrow_mut::<NSBlockOperationHostObject>(this).is_executing = true;
    let blocks: Vec<ConstVoidPtr> = env.objc.borrow::<NSBlockOperationHostObject>(this).execution_blocks.clone();
    for block in blocks {
        let is_cancelled = env.objc.borrow::<NSBlockOperationHostObject>(this).is_cancelled;
        if is_cancelled { break; }
        invoke_block(env, block);
    }
    env.objc.borrow_mut::<NSBlockOperationHostObject>(this).is_executing = false;
    env.objc.borrow_mut::<NSBlockOperationHostObject>(this).is_finished = true;
    let completion_block = env.objc.borrow::<NSBlockOperationHostObject>(this).completion_block;
    if !completion_block.is_null() {
        invoke_block(env, completion_block);
    }
}

- (())main {
    let blocks: Vec<ConstVoidPtr> = env.objc.borrow::<NSBlockOperationHostObject>(this).execution_blocks.clone();
    for block in blocks {
        invoke_block(env, block);
    }
}

- (())cancel {
    log_dbg!("NSBlockOperation cancel");
    env.objc.borrow_mut::<NSBlockOperationHostObject>(this).is_cancelled = true;
}

- (bool)isCancelled {
    env.objc.borrow::<NSBlockOperationHostObject>(this).is_cancelled
}

- (bool)isExecuting {
    env.objc.borrow::<NSBlockOperationHostObject>(this).is_executing
}

- (bool)isFinished {
    env.objc.borrow::<NSBlockOperationHostObject>(this).is_finished
}

- (())setCompletionBlock:(id)block {
    let block_ptr = ConstVoidPtr::from_bits(block.to_bits());
    env.objc.borrow_mut::<NSBlockOperationHostObject>(this).completion_block = block_ptr;
}

- (id)completionBlock {
    let block = env.objc.borrow::<NSBlockOperationHostObject>(this).completion_block;
    id::from_bits(block.to_bits())
}

@end

@implementation NSInvocationOperation: NSOperation

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSInvocationOperationHostObject {
        is_cancelled: false,
        is_finished: false,
        is_executing: false,
        completion_block: ConstVoidPtr::null(),
        target: nil,
        selector: None,
        argument: nil,
        result: nil,
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithTarget:(id)target
            selector:(SEL)sel
              object:(id)arg {
    log_dbg!("NSInvocationOperation initWithTarget:selector:object:");
    retain(env, target);
    retain(env, arg);
    let host = env.objc.borrow_mut::<NSInvocationOperationHostObject>(this);
    host.target = target;
    host.selector = Some(sel);
    host.argument = arg;
    this
}

- (())start {
    let is_cancelled = env.objc.borrow::<NSInvocationOperationHostObject>(this).is_cancelled;
    if is_cancelled {
        env.objc.borrow_mut::<NSInvocationOperationHostObject>(this).is_finished = true;
        return;
    }
    log_dbg!("NSInvocationOperation start - executing");
    env.objc.borrow_mut::<NSInvocationOperationHostObject>(this).is_executing = true;
    () = msg![env; this main];
    env.objc.borrow_mut::<NSInvocationOperationHostObject>(this).is_executing = false;
    env.objc.borrow_mut::<NSInvocationOperationHostObject>(this).is_finished = true;
    let completion_block = env.objc.borrow::<NSInvocationOperationHostObject>(this).completion_block;
    if !completion_block.is_null() {
        invoke_block(env, completion_block);
    }
}

- (())main {
    let host = env.objc.borrow::<NSInvocationOperationHostObject>(this);
    let target = host.target;
    let selector = host.selector;
    let argument = host.argument;
    if let Some(sel) = selector {
        if target != nil {
            log_dbg!("NSInvocationOperation main: calling target method");
            let result: id = msg![env; target performSelector:sel withObject:argument];
            env.objc.borrow_mut::<NSInvocationOperationHostObject>(this).result = result;
        }
    }
}

- (())cancel {
    log_dbg!("NSInvocationOperation cancel");
    env.objc.borrow_mut::<NSInvocationOperationHostObject>(this).is_cancelled = true;
}

- (bool)isCancelled {
    env.objc.borrow::<NSInvocationOperationHostObject>(this).is_cancelled
}

- (bool)isExecuting {
    env.objc.borrow::<NSInvocationOperationHostObject>(this).is_executing
}

- (bool)isFinished {
    env.objc.borrow::<NSInvocationOperationHostObject>(this).is_finished
}

- (id)result {
    env.objc.borrow::<NSInvocationOperationHostObject>(this).result
}

- (())setCompletionBlock:(id)block {
    let block_ptr = ConstVoidPtr::from_bits(block.to_bits());
    env.objc.borrow_mut::<NSInvocationOperationHostObject>(this).completion_block = block_ptr;
}

- (id)completionBlock {
    let block = env.objc.borrow::<NSInvocationOperationHostObject>(this).completion_block;
    id::from_bits(block.to_bits())
}

- (())dealloc {
    let host = env.objc.borrow::<NSInvocationOperationHostObject>(this);
    let target = host.target;
    let argument = host.argument;
    release(env, target);
    release(env, argument);
    env.objc.dealloc_object(this, &mut env.mem)
}

@end

@implementation NSOperationQueue: NSObject

+ (id)alloc {
    let host_object = Box::new(NSOperationQueueHostObject {
        max_concurrent_operations: -1,
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

+ (id)mainQueue {
    let queue: id = msg_class![env; NSOperationQueue alloc];
    msg![env; queue init]
}

+ (id)currentQueue {
    msg_class![env; NSOperationQueue mainQueue]
}

- (id)init {
    this
}

- (())addOperation:(id)op {
    if op == nil {
        return;
    }
    log_dbg!("NSOperationQueue addOperation: executing operation synchronously");
    () = msg![env; op start];
}

- (())addOperations:(id)ops waitUntilFinished:(bool)wait {
    if ops == nil {
        return;
    }
    log_dbg!("NSOperationQueue addOperations:waitUntilFinished:{}", wait);
    let count: u32 = msg![env; ops count];
    for i in 0..count {
        let op: id = msg![env; ops objectAtIndex:i];
        () = msg![env; this addOperation:op];
    }
}

- (())addOperationWithBlock:(id)block {
    if block == nil {
        return;
    }
    log_dbg!("NSOperationQueue addOperationWithBlock: creating and executing block operation");
    let op: id = msg_class![env; NSBlockOperation blockOperationWithBlock:block];
    () = msg![env; this addOperation:op];
}

- (())cancelAllOperations {
    log_dbg!("NSOperationQueue cancelAllOperations - no-op");
}

- (())waitUntilAllOperationsAreFinished {
    log_dbg!("NSOperationQueue waitUntilAllOperationsAreFinished - no-op");
}

- (())setMaxConcurrentOperationCount:(i32)count {
    env.objc.borrow_mut::<NSOperationQueueHostObject>(this).max_concurrent_operations = count;
}

- (i32)maxConcurrentOperationCount {
    env.objc.borrow::<NSOperationQueueHostObject>(this).max_concurrent_operations
}

- (i32)operationCount {
    0
}

- (id)operations {
    msg_class![env; NSArray array]
}

- (())setSuspended:(bool)_suspended {
    log_dbg!("NSOperationQueue setSuspended: ignored");
}

- (bool)isSuspended {
    false
}

- (())setName:(id)_name {
    log_dbg!("NSOperationQueue setName: ignored");
}

- (id)name {
    nil
}

@end

};
