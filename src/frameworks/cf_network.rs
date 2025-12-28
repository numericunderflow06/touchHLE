/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! CFNetwork.framework stubs
//!
//! CFNetwork provides Core Foundation-level networking APIs. Most games
//! use higher-level APIs or can handle network unavailability gracefully.

use crate::dyld::{export_c_func, ConstantExports, FunctionExports, HostConstant, HostDylib};
use crate::mem::{ConstPtr, MutPtr, ConstVoidPtr, MutVoidPtr};
use crate::Environment;

pub const DYLIB: HostDylib = HostDylib {
    path: "/System/Library/Frameworks/CFNetwork.framework/CFNetwork",
    aliases: &[],
    class_exports: &[],
    constant_exports: &[CONSTANTS],
    function_exports: &[FUNCTIONS],
};

// CF types
type CFStringRef = ConstVoidPtr;
type CFURLRef = ConstVoidPtr;
type CFDictionaryRef = ConstVoidPtr;
type CFReadStreamRef = MutVoidPtr;
type CFWriteStreamRef = MutVoidPtr;
type CFHTTPMessageRef = MutVoidPtr;
type CFHostRef = MutVoidPtr;

fn CFReadStreamCreateForHTTPRequest(
    _env: &mut Environment,
    _alloc: ConstVoidPtr, // CFAllocatorRef
    request: CFHTTPMessageRef,
) -> CFReadStreamRef {
    log!("Warning: CFReadStreamCreateForHTTPRequest({:?}) - stubbed, returning NULL", request);
    MutVoidPtr::null()
}

fn CFHTTPMessageCreateRequest(
    _env: &mut Environment,
    _alloc: ConstVoidPtr,
    _request_method: CFStringRef,
    _url: CFURLRef,
    _http_version: CFStringRef,
) -> CFHTTPMessageRef {
    log!("Warning: CFHTTPMessageCreateRequest - stubbed, returning NULL");
    MutVoidPtr::null()
}

fn CFHTTPMessageCreateEmpty(
    _env: &mut Environment,
    _alloc: ConstVoidPtr,
    _is_request: bool,
) -> CFHTTPMessageRef {
    log!("Warning: CFHTTPMessageCreateEmpty - stubbed, returning NULL");
    MutVoidPtr::null()
}

fn CFHTTPMessageSetHeaderFieldValue(
    _env: &mut Environment,
    _message: CFHTTPMessageRef,
    _header_field: CFStringRef,
    _value: CFStringRef,
) {
    log!("Warning: CFHTTPMessageSetHeaderFieldValue - stubbed");
}

fn CFHTTPMessageSetBody(
    _env: &mut Environment,
    _message: CFHTTPMessageRef,
    _body_data: ConstVoidPtr, // CFDataRef
) {
    log!("Warning: CFHTTPMessageSetBody - stubbed");
}

fn CFHTTPMessageCopyHeaderFieldValue(
    _env: &mut Environment,
    _message: CFHTTPMessageRef,
    _header_field: CFStringRef,
) -> CFStringRef {
    log!("Warning: CFHTTPMessageCopyHeaderFieldValue - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn CFHTTPMessageGetResponseStatusCode(
    _env: &mut Environment,
    _response: CFHTTPMessageRef,
) -> i32 {
    log!("Warning: CFHTTPMessageGetResponseStatusCode - stubbed, returning 0");
    0
}

fn CFHTTPMessageIsHeaderComplete(
    _env: &mut Environment,
    _message: CFHTTPMessageRef,
) -> bool {
    log!("Warning: CFHTTPMessageIsHeaderComplete - stubbed, returning false");
    false
}

fn CFHostCreateWithName(
    _env: &mut Environment,
    _alloc: ConstVoidPtr,
    _hostname: CFStringRef,
) -> CFHostRef {
    log!("Warning: CFHostCreateWithName - stubbed, returning NULL");
    MutVoidPtr::null()
}

fn CFHostStartInfoResolution(
    _env: &mut Environment,
    _host: CFHostRef,
    _info: i32, // CFHostInfoType
    _error: MutPtr<i32>,
) -> bool {
    log!("Warning: CFHostStartInfoResolution - stubbed, returning false");
    false
}

fn CFHostGetAddressing(
    _env: &mut Environment,
    _host: CFHostRef,
    _has_been_resolved: MutPtr<bool>,
) -> ConstVoidPtr { // CFArrayRef
    log!("Warning: CFHostGetAddressing - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn CFNetworkCopySystemProxySettings(
    _env: &mut Environment,
) -> CFDictionaryRef {
    log!("Warning: CFNetworkCopySystemProxySettings - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn CFNetworkCopyProxiesForURL(
    _env: &mut Environment,
    _url: CFURLRef,
    _proxy_settings: CFDictionaryRef,
) -> ConstVoidPtr { // CFArrayRef
    log!("Warning: CFNetworkCopyProxiesForURL - stubbed, returning NULL");
    ConstVoidPtr::null()
}

const CONSTANTS: ConstantExports = &[
    // HTTP version constants
    ("_kCFHTTPVersion1_0", HostConstant::NSString("HTTP/1.0")),
    ("_kCFHTTPVersion1_1", HostConstant::NSString("HTTP/1.1")),

    // Stream property keys
    ("_kCFStreamPropertyHTTPResponseHeader", HostConstant::NSString("kCFStreamPropertyHTTPResponseHeader")),
    ("_kCFStreamPropertyHTTPFinalURL", HostConstant::NSString("kCFStreamPropertyHTTPFinalURL")),
    ("_kCFStreamPropertyHTTPFinalRequest", HostConstant::NSString("kCFStreamPropertyHTTPFinalRequest")),
    ("_kCFStreamPropertyHTTPProxy", HostConstant::NSString("kCFStreamPropertyHTTPProxy")),
    ("_kCFStreamPropertyHTTPShouldAutoredirect", HostConstant::NSString("kCFStreamPropertyHTTPShouldAutoredirect")),
    ("_kCFStreamPropertyHTTPAttemptPersistentConnection", HostConstant::NSString("kCFStreamPropertyHTTPAttemptPersistentConnection")),

    // Proxy dictionary keys
    ("_kCFProxyHostNameKey", HostConstant::NSString("kCFProxyHostNameKey")),
    ("_kCFProxyPortNumberKey", HostConstant::NSString("kCFProxyPortNumberKey")),
    ("_kCFProxyTypeKey", HostConstant::NSString("kCFProxyTypeKey")),
];

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(CFReadStreamCreateForHTTPRequest(_, _)),
    export_c_func!(CFHTTPMessageCreateRequest(_, _, _, _)),
    export_c_func!(CFHTTPMessageCreateEmpty(_, _)),
    export_c_func!(CFHTTPMessageSetHeaderFieldValue(_, _, _)),
    export_c_func!(CFHTTPMessageSetBody(_, _)),
    export_c_func!(CFHTTPMessageCopyHeaderFieldValue(_, _)),
    export_c_func!(CFHTTPMessageGetResponseStatusCode(_)),
    export_c_func!(CFHTTPMessageIsHeaderComplete(_)),
    export_c_func!(CFHostCreateWithName(_, _)),
    export_c_func!(CFHostStartInfoResolution(_, _, _)),
    export_c_func!(CFHostGetAddressing(_, _)),
    export_c_func!(CFNetworkCopySystemProxySettings()),
    export_c_func!(CFNetworkCopyProxiesForURL(_, _)),
];
