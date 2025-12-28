/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Security.framework stubs
//!
//! The Security framework provides keychain services, certificate handling,
//! and other security-related functionality. Most games don't need these
//! features to function properly.

use crate::dyld::{export_c_func, ConstantExports, FunctionExports, HostConstant, HostDylib};
use crate::mem::{ConstPtr, MutPtr, ConstVoidPtr, MutVoidPtr};
use crate::Environment;

pub const DYLIB: HostDylib = HostDylib {
    path: "/System/Library/Frameworks/Security.framework/Security",
    aliases: &[],
    class_exports: &[],
    constant_exports: &[CONSTANTS],
    function_exports: &[FUNCTIONS],
};

// Security error codes
const errSecSuccess: i32 = 0;
const errSecItemNotFound: i32 = -25300;
const errSecUnimplemented: i32 = -4;

// Keychain item attribute types (CFTypeRef stand-ins)
type CFTypeRef = ConstVoidPtr;
type CFDictionaryRef = ConstVoidPtr;
type CFArrayRef = ConstVoidPtr;
type CFDataRef = ConstVoidPtr;

fn SecItemCopyMatching(
    _env: &mut Environment,
    query: CFDictionaryRef,
    result: MutPtr<CFTypeRef>,
) -> i32 {
    log!("Warning: SecItemCopyMatching({:?}) - stubbed, returning errSecItemNotFound", query);
    if !result.is_null() {
        _env.mem.write(result, ConstVoidPtr::null());
    }
    errSecItemNotFound
}

fn SecItemAdd(
    _env: &mut Environment,
    attributes: CFDictionaryRef,
    result: MutPtr<CFTypeRef>,
) -> i32 {
    log!("Warning: SecItemAdd({:?}) - stubbed, returning errSecUnimplemented", attributes);
    if !result.is_null() {
        _env.mem.write(result, ConstVoidPtr::null());
    }
    errSecUnimplemented
}

fn SecItemUpdate(
    _env: &mut Environment,
    query: CFDictionaryRef,
    _attributes_to_update: CFDictionaryRef,
) -> i32 {
    log!("Warning: SecItemUpdate({:?}) - stubbed, returning errSecItemNotFound", query);
    errSecItemNotFound
}

fn SecItemDelete(
    _env: &mut Environment,
    query: CFDictionaryRef,
) -> i32 {
    log!("Warning: SecItemDelete({:?}) - stubbed, returning errSecItemNotFound", query);
    errSecItemNotFound
}

fn SecRandomCopyBytes(
    env: &mut Environment,
    _rnd: ConstVoidPtr, // SecRandomRef, usually kSecRandomDefault (NULL)
    count: u32,
    bytes: MutPtr<u8>,
) -> i32 {
    log!("SecRandomCopyBytes(count={}) - filling with random bytes", count);
    // Fill with pseudo-random bytes
    for i in 0..count {
        let random_byte = ((i * 1103515245 + 12345) >> 16) as u8;
        env.mem.write(bytes + i, random_byte);
    }
    errSecSuccess
}

fn SecCertificateCopySubjectSummary(
    _env: &mut Environment,
    certificate: ConstVoidPtr,
) -> ConstVoidPtr {
    log!("Warning: SecCertificateCopySubjectSummary({:?}) - stubbed, returning NULL", certificate);
    ConstVoidPtr::null()
}

fn SecCertificateCopyData(
    _env: &mut Environment,
    certificate: ConstVoidPtr,
) -> CFDataRef {
    log!("Warning: SecCertificateCopyData({:?}) - stubbed, returning NULL", certificate);
    ConstVoidPtr::null()
}

fn SecTrustGetCertificateCount(
    _env: &mut Environment,
    trust: ConstVoidPtr,
) -> i32 {
    log!("Warning: SecTrustGetCertificateCount({:?}) - stubbed, returning 0", trust);
    0
}

fn SecTrustGetCertificateAtIndex(
    _env: &mut Environment,
    trust: ConstVoidPtr,
    _ix: i32,
) -> ConstVoidPtr {
    log!("Warning: SecTrustGetCertificateAtIndex({:?}) - stubbed, returning NULL", trust);
    ConstVoidPtr::null()
}

fn SecTrustEvaluate(
    _env: &mut Environment,
    trust: ConstVoidPtr,
    result: MutPtr<u32>,
) -> i32 {
    log!("Warning: SecTrustEvaluate({:?}) - stubbed, returning success with proceed", trust);
    if !result.is_null() {
        // kSecTrustResultProceed = 1
        _env.mem.write(result, 1);
    }
    errSecSuccess
}

const CONSTANTS: ConstantExports = &[
    // Keychain item class keys
    ("_kSecClass", HostConstant::NSString("kSecClass")),
    ("_kSecClassGenericPassword", HostConstant::NSString("genp")),
    ("_kSecClassInternetPassword", HostConstant::NSString("inet")),
    ("_kSecClassCertificate", HostConstant::NSString("cert")),
    ("_kSecClassKey", HostConstant::NSString("keys")),
    ("_kSecClassIdentity", HostConstant::NSString("idnt")),

    // Attribute keys
    ("_kSecAttrAccount", HostConstant::NSString("acct")),
    ("_kSecAttrService", HostConstant::NSString("svce")),
    ("_kSecAttrGeneric", HostConstant::NSString("gena")),
    ("_kSecAttrAccessible", HostConstant::NSString("pdmn")),
    ("_kSecAttrAccessGroup", HostConstant::NSString("agrp")),

    // Value keys
    ("_kSecValueData", HostConstant::NSString("v_Data")),
    ("_kSecReturnData", HostConstant::NSString("r_Data")),
    ("_kSecReturnAttributes", HostConstant::NSString("r_Attributes")),
    ("_kSecReturnRef", HostConstant::NSString("r_Ref")),
    ("_kSecReturnPersistentRef", HostConstant::NSString("r_PersistentRef")),

    // Match keys
    ("_kSecMatchLimit", HostConstant::NSString("m_Limit")),
    ("_kSecMatchLimitOne", HostConstant::NSString("m_LimitOne")),
    ("_kSecMatchLimitAll", HostConstant::NSString("m_LimitAll")),

    // Random
    ("_kSecRandomDefault", HostConstant::NullPtr),
];

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(SecItemCopyMatching(_, _)),
    export_c_func!(SecItemAdd(_, _)),
    export_c_func!(SecItemUpdate(_, _)),
    export_c_func!(SecItemDelete(_)),
    export_c_func!(SecRandomCopyBytes(_, _, _)),
    export_c_func!(SecCertificateCopySubjectSummary(_)),
    export_c_func!(SecCertificateCopyData(_)),
    export_c_func!(SecTrustGetCertificateCount(_)),
    export_c_func!(SecTrustGetCertificateAtIndex(_, _)),
    export_c_func!(SecTrustEvaluate(_, _)),
];
