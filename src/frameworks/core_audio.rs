/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! CoreAudio.framework stubs
//!
//! The Core Audio framework provides low-level audio services. Most games use
//! higher-level frameworks like AudioToolbox or AVFoundation, so we can stub
//! this as most functionality is already provided by those frameworks.
//!
//! Note: Core Audio Types are in a separate module (core_audio_types.rs).

use crate::dyld::{export_c_func, ConstantExports, FunctionExports, HostDylib};
use crate::mem::{ConstPtr, MutPtr, ConstVoidPtr, MutVoidPtr};
use crate::Environment;

pub const DYLIB: HostDylib = HostDylib {
    path: "/System/Library/Frameworks/CoreAudio.framework/CoreAudio",
    aliases: &[],
    class_exports: &[],
    constant_exports: &[CONSTANTS],
    function_exports: &[FUNCTIONS],
};

// Audio Hardware error codes
const kAudioHardwareNoError: i32 = 0;
const kAudioHardwareUnspecifiedError: i32 = 0x77686174; // 'what'
const kAudioHardwareNotRunningError: i32 = 0x73746f70; // 'stop'
const kAudioHardwareUnknownPropertyError: i32 = 0x77686f3f; // 'who?'

type AudioObjectID = u32;
type AudioObjectPropertyAddress = ConstVoidPtr;

fn AudioObjectGetPropertyData(
    _env: &mut Environment,
    in_object_id: AudioObjectID,
    _in_address: AudioObjectPropertyAddress,
    _in_qualifier_data_size: u32,
    _in_qualifier_data: ConstVoidPtr,
    io_data_size: MutPtr<u32>,
    _out_data: MutVoidPtr,
) -> i32 {
    log!("Warning: AudioObjectGetPropertyData(objectID={}) - stubbed, returning error", in_object_id);
    if !io_data_size.is_null() {
        _env.mem.write(io_data_size, 0);
    }
    kAudioHardwareUnknownPropertyError
}

fn AudioObjectSetPropertyData(
    _env: &mut Environment,
    in_object_id: AudioObjectID,
    _in_address: AudioObjectPropertyAddress,
    _in_qualifier_data_size: u32,
    _in_qualifier_data: ConstVoidPtr,
    _in_data_size: u32,
    _in_data: ConstVoidPtr,
) -> i32 {
    log!("Warning: AudioObjectSetPropertyData(objectID={}) - stubbed, returning error", in_object_id);
    kAudioHardwareUnknownPropertyError
}

fn AudioObjectHasProperty(
    _env: &mut Environment,
    in_object_id: AudioObjectID,
    _in_address: AudioObjectPropertyAddress,
) -> bool {
    log!("Warning: AudioObjectHasProperty(objectID={}) - stubbed, returning false", in_object_id);
    false
}

fn AudioObjectIsPropertySettable(
    _env: &mut Environment,
    in_object_id: AudioObjectID,
    _in_address: AudioObjectPropertyAddress,
    out_is_settable: MutPtr<bool>,
) -> i32 {
    log!("Warning: AudioObjectIsPropertySettable(objectID={}) - stubbed", in_object_id);
    if !out_is_settable.is_null() {
        _env.mem.write(out_is_settable, false);
    }
    kAudioHardwareNoError
}

fn AudioObjectGetPropertyDataSize(
    _env: &mut Environment,
    in_object_id: AudioObjectID,
    _in_address: AudioObjectPropertyAddress,
    _in_qualifier_data_size: u32,
    _in_qualifier_data: ConstVoidPtr,
    out_data_size: MutPtr<u32>,
) -> i32 {
    log!("Warning: AudioObjectGetPropertyDataSize(objectID={}) - stubbed", in_object_id);
    if !out_data_size.is_null() {
        _env.mem.write(out_data_size, 0);
    }
    kAudioHardwareNoError
}

fn AudioObjectAddPropertyListener(
    _env: &mut Environment,
    in_object_id: AudioObjectID,
    _in_address: AudioObjectPropertyAddress,
    _in_listener: ConstVoidPtr,
    _in_client_data: MutVoidPtr,
) -> i32 {
    log!("Warning: AudioObjectAddPropertyListener(objectID={}) - stubbed", in_object_id);
    kAudioHardwareNoError
}

fn AudioObjectRemovePropertyListener(
    _env: &mut Environment,
    in_object_id: AudioObjectID,
    _in_address: AudioObjectPropertyAddress,
    _in_listener: ConstVoidPtr,
    _in_client_data: MutVoidPtr,
) -> i32 {
    log!("Warning: AudioObjectRemovePropertyListener(objectID={}) - stubbed", in_object_id);
    kAudioHardwareNoError
}

const CONSTANTS: ConstantExports = &[];

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(AudioObjectGetPropertyData(_, _, _, _, _, _)),
    export_c_func!(AudioObjectSetPropertyData(_, _, _, _, _, _)),
    export_c_func!(AudioObjectHasProperty(_, _)),
    export_c_func!(AudioObjectIsPropertySettable(_, _, _)),
    export_c_func!(AudioObjectGetPropertyDataSize(_, _, _, _, _)),
    export_c_func!(AudioObjectAddPropertyListener(_, _, _, _)),
    export_c_func!(AudioObjectRemovePropertyListener(_, _, _, _)),
];
