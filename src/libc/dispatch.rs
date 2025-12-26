/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Stub for libdispatch (Grand Central Dispatch)
//!
//! GCD provides a task-based concurrency model. For now, we provide minimal
//! stubs that execute blocks synchronously on the main thread.

use crate::abi::{CallFromHost, GuestFunction};
use crate::dyld::{export_c_func, ConstantExports, FunctionExports, HostConstant};
use crate::mem::{ConstVoidPtr, GuestUSize, MutPtr, Ptr};
use crate::Environment;

/// Dispatch queue type (opaque pointer)
pub type dispatch_queue_t = ConstVoidPtr;

/// Dispatch block type - this is a pointer to a Block_literal structure
pub type dispatch_block_t = ConstVoidPtr;

/// Block_literal structure (from Blocks ABI)
/// The invoke function is at offset 12 (after isa, flags, reserved)
#[repr(C, packed)]
struct BlockLiteral {
    isa: ConstVoidPtr,
    flags: i32,
    reserved: i32,
    invoke: ConstVoidPtr, // Function pointer: void (*invoke)(void *, ...)
}
unsafe impl crate::mem::SafeRead for BlockLiteral {}

/// Helper function to invoke a block
/// Block invoke signature: void (*invoke)(void *block)
fn invoke_block(env: &mut Environment, block: dispatch_block_t) {
    if block.is_null() {
        log!("Warning: Tried to invoke null block, ignoring");
        return;
    }

    // Read the block structure to get the invoke function
    let block_ptr: MutPtr<BlockLiteral> = Ptr::from_bits(block.to_bits());
    let block_literal = env.mem.read(block_ptr);

    if block_literal.invoke.is_null() {
        log!("Warning: Block has null invoke function, ignoring");
        return;
    }

    let invoke_addr = block_literal.invoke.to_bits();
    log!(
        "dispatch: Invoking block at {:?} with invoke function at 0x{:x}",
        block,
        invoke_addr
    );

    // Create a GuestFunction from the invoke pointer
    let invoke_fn = GuestFunction::from_addr_with_thumb_bit(invoke_addr);

    // Call the invoke function with the block pointer as its argument
    // Signature: void (*invoke)(void *block)
    let _: () = invoke_fn.call_from_host(env, (block,));
    
    log!("dispatch: Block execution completed");
}

/// dispatch_async - queue a block for asynchronous execution
/// For now, we execute it synchronously on the main thread
fn dispatch_async(env: &mut Environment, queue: dispatch_queue_t, block: dispatch_block_t) {
    log!(
        "dispatch_async({:?}, {:?}) - executing synchronously",
        queue,
        block
    );

    invoke_block(env, block);
}

/// dispatch_sync - execute a block synchronously on a queue
fn dispatch_sync(env: &mut Environment, queue: dispatch_queue_t, block: dispatch_block_t) {
    log!(
        "dispatch_sync({:?}, {:?}) - executing synchronously",
        queue,
        block
    );

    invoke_block(env, block);
}

/// dispatch_once - execute a block exactly once
fn dispatch_once(
    env: &mut Environment,
    predicate: MutPtr<GuestUSize>,
    block: dispatch_block_t,
) {
    // Read the predicate value
    let pred_value = env.mem.read(predicate);

    if pred_value != 0 {
        // Already executed
        return;
    }

    log!("dispatch_once({:?}): executing block for first time", predicate);

    // Mark as executed BEFORE invoking the block (in case of recursive calls)
    env.mem.write(predicate, 1u32);

    invoke_block(env, block);
}

/// dispatch_get_global_queue - get a global concurrent queue
fn dispatch_get_global_queue(
    _env: &mut Environment,
    priority: i32,
    flags: u32,
) -> dispatch_queue_t {
    log!(
        "dispatch_get_global_queue(priority={}, flags={}) - returning stub queue",
        priority,
        flags
    );
    // Return a non-null stub value - we use a fixed address that won't collide
    ConstVoidPtr::from_bits(0xDEAD0001)
}

pub const CONSTANTS: ConstantExports = &[
    // Main dispatch queue - provide a non-null stub
    (
        "__dispatch_main_q",
        HostConstant::Custom(|env| {
            // Allocate a small stub value to use as the queue identifier
            // The actual value doesn't matter as long as it's non-null
            let queue_stub: u32 = 0xDEAD0000;
            env.mem.alloc_and_write(queue_stub).cast_void().cast_const()
        }),
    ),
];

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(dispatch_async(_, _)),
    export_c_func!(dispatch_sync(_, _)),
    export_c_func!(dispatch_once(_, _)),
    export_c_func!(dispatch_get_global_queue(_, _)),
];
