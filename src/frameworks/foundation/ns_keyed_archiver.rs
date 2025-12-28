/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `NSKeyedArchiver` stub implementation.
//!
//! NSKeyedArchiver serializes object graphs to data. This is a stub that
//! returns empty/nil data since we don't need actual serialization for games.

use crate::objc::{id, msg_class, nil, objc_classes, ClassExports, HostObject, NSZonePtr};

#[derive(Default)]
struct NSKeyedArchiverHostObject {
    output_format: i32, // NSPropertyListFormat
}
impl HostObject for NSKeyedArchiverHostObject {}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation NSKeyedArchiver: NSCoder

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSKeyedArchiverHostObject::default());
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

+ (id)archivedDataWithRootObject:(id)_root_object {
    log!("Warning: NSKeyedArchiver archivedDataWithRootObject: stubbed, returning empty data");
    // Return empty NSData
    msg_class![env; NSData data]
}

+ (bool)archiveRootObject:(id)_root_object toFile:(id)_path {
    log!("Warning: NSKeyedArchiver archiveRootObject:toFile: stubbed, returning false");
    false
}

- (id)init {
    log!("Warning: NSKeyedArchiver init - stubbed");
    this
}

- (id)initForWritingWithMutableData:(id)_data {
    log!("Warning: NSKeyedArchiver initForWritingWithMutableData: stubbed");
    this
}

- (())finishEncoding {
    log!("Warning: NSKeyedArchiver finishEncoding - stubbed");
}

- (())setOutputFormat:(i32)format {
    env.objc.borrow_mut::<NSKeyedArchiverHostObject>(this).output_format = format;
}

- (i32)outputFormat {
    env.objc.borrow::<NSKeyedArchiverHostObject>(this).output_format
}

// Encoding methods - all stubbed
- (())encodeObject:(id)_object forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeObject:forKey: stubbed");
}

- (())encodeBool:(bool)_value forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeBool:forKey: stubbed");
}

- (())encodeInt:(i32)_value forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeInt:forKey: stubbed");
}

- (())encodeInt32:(i32)_value forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeInt32:forKey: stubbed");
}

- (())encodeInt64:(i64)_value forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeInt64:forKey: stubbed");
}

- (())encodeFloat:(f32)_value forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeFloat:forKey: stubbed");
}

- (())encodeDouble:(f64)_value forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeDouble:forKey: stubbed");
}

- (())encodeBytes:(id)_bytes length:(u32)_length forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeBytes:length:forKey: stubbed");
}

- (())encodeConditionalObject:(id)_object forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeConditionalObject:forKey: stubbed");
}

- (())encodeInteger:(i32)_value forKey:(id)_key {
    log_dbg!("NSKeyedArchiver encodeInteger:forKey: stubbed");
}

- (())setDelegate:(id)_delegate {
    log_dbg!("NSKeyedArchiver setDelegate: stubbed");
}

- (id)delegate {
    nil
}

@end

};
