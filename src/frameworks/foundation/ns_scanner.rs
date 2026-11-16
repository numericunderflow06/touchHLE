/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! The `NSScanner` class.

use crate::frameworks::foundation::ns_string::{from_u16_vec, to_rust_string};
use crate::frameworks::foundation::{unichar, NSNotFound, NSRange, NSUInteger};
use crate::mem::MutPtr;
use crate::objc::{
    autorelease, id, msg, msg_class, nil, objc_classes, release, retain, ClassExports, HostObject,
    NSZonePtr,
};
use crate::Environment;

// TODO: Speed up by optimizing for internal subclasses
#[derive(Default, Clone)]
struct NSScannerHostObject {
    /// NSCharacterSet *, characters to be skipped
    to_be_skipped: id,
    /// NSString *, should always be immutable since it's copied
    string: id,
    /// Length is cached since it is immutable.
    len: NSUInteger,
    pos: NSUInteger,
}
impl HostObject for NSScannerHostObject {}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation NSScanner: NSObject

+ (id)scannerWithString:(id)string {
    let new: id = msg![env; this alloc];
    let new = msg![env; new initWithString:string];
    autorelease(env, new)
}

+ (id)allocWithZone:(NSZonePtr)zone {
    // NSScanner might be subclassed by something which needs
    // allocWithZone: to have the normal behaviour. Unimplemented: call
    // superclass alloc then.
    assert!(this == env.objc.get_known_class("NSScanner", &mut env.mem));
    msg_class![env; _touchHLE_NSScanner allocWithZone:zone]
}

@end

// Our private subclass that is the single implementation of NSScanner for
// the time being.
@implementation _touchHLE_NSScanner: NSScanner

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(NSScannerHostObject::default());
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithString:(id)string { // NSString *
    assert!(string != nil);
    let string: id = msg![env; string copy]; // Same behaviour as simulator
    let len: NSUInteger = msg![env; string length];
    let default_set = msg_class![env; NSCharacterSet whitespaceAndNewlineCharacterSet];
    retain(env, default_set);
    *env.objc.borrow_mut(this) = NSScannerHostObject {
        to_be_skipped: default_set,
        string,
        len,
        pos: 0
    };
    this
}

- (())dealloc {
    let &NSScannerHostObject {
        to_be_skipped,
        string,
        ..
    } = env.objc.borrow(this);
    release(env, string);
    release(env, to_be_skipped);
    env.objc.dealloc_object(this, &mut env.mem);
}

- (id)charactersToBeSkipped { // NSCharacterSet *
    env.objc.borrow::<NSScannerHostObject>(this).to_be_skipped
}

- (bool)isAtEnd {
    skip_characters(env, this);
    let NSScannerHostObject { len, pos, .. } = env.objc.borrow::<NSScannerHostObject>(this);
    len == pos
}

// [DIAG-SCAN-LOC] scanLocation getter - per Apple documentation
// Returns the index of the character at which the scanner will begin its next scanning operation
- (NSUInteger)scanLocation {
    let pos = env.objc.borrow::<NSScannerHostObject>(this).pos;
    log!("[DIAG-SCAN-LOC] scanLocation called, returning {}", pos);
    pos
}

// [DIAG-SCAN-LOC] setScanLocation: setter - per Apple documentation
// Sets the location at which the scanner will begin its next scanning operation
- (())setScanLocation:(NSUInteger)location {
    let host = env.objc.borrow_mut::<NSScannerHostObject>(this);
    let old_pos = host.pos;
    // Per Apple docs: "If index is beyond the string's end, the behavior is undefined"
    // We clamp to len for safety
    host.pos = location.min(host.len);
    log!("[DIAG-SCAN-LOC] setScanLocation:{} (was {}, clamped to {})", location, old_pos, host.pos);
}

- (bool)scanUpToCharactersFromSet:(id)cset intoString:(MutPtr<id>)str {
    skip_characters(env, this);

    let NSScannerHostObject { to_be_skipped, string, len, mut pos } = env.objc.borrow::<NSScannerHostObject>(this).clone();
    if pos >= len {
        // Does nothing (same as simulator)
        return false;
    }
    let first_scan: unichar = msg![env; string characterAtIndex:pos];
    if msg![env; cset characterIsMember:first_scan] {
        // Does nothing (same as simulator)
        return false;
    }
    let mut chars = vec![first_scan];
    pos += 1;
    while pos < len {
        let curr = msg![env; string characterAtIndex:pos];
        if msg![env; cset characterIsMember:curr] {
            break
        }
        pos += 1;
        chars.push(curr);
    }
    if !str.is_null() {
        let out = from_u16_vec(env, chars);
        autorelease(env, out);
        env.mem.write(str, out);
    }

    *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos };
    true
}

- (bool)scanCharactersFromSet:(id)cset intoString:(MutPtr<id>)str {
    // [DIAG-C4] Log scanCharactersFromSet call
    let pos = env.objc.borrow::<NSScannerHostObject>(this).pos;
    log!("[DIAG-C4-SCAN-CHARS] pos={} scanning characters from set", pos);
    let inv_cset: id = msg![env; cset invertedSet];
    let result: bool = msg![env; this scanUpToCharactersFromSet:inv_cset intoString:str];
    let new_pos = env.objc.borrow::<NSScannerHostObject>(this).pos;
    log!("[DIAG-C4-SCAN-CHARS] scanned {} characters, success={}", new_pos - pos, result);
    result
}

- (bool)scanHexInt:(MutPtr<u32>)result {
    assert!(!result.is_null());
    skip_characters(env, this);

    let NSScannerHostObject { to_be_skipped: _set, string, len, pos } = env.objc.borrow::<NSScannerHostObject>(this).clone();
    assert!(pos < len);
    let susbstring: id = msg![env; string substringFromIndex:pos];
    let tmp = to_rust_string(env, susbstring);
    assert!(!tmp.starts_with("0x") && !tmp.starts_with("0X"));
    assert!(!tmp.chars().next().unwrap().is_ascii_hexdigit()); // TODO
    env.mem.write(result, 0);
    false
}

- (bool)scanUpToString:(id)stop_string // NSString *
            intoString:(MutPtr<id>)result { // NSString **
    skip_characters(env, this);

    let NSScannerHostObject { to_be_skipped, string, len, pos } = std::mem::take(env.objc.borrow_mut::<NSScannerHostObject>(this));
    let stop_str_preview = to_rust_string(env, stop_string);
    log_dbg!("scanUpToString:'{}' intoString: from '{}' at {}", stop_str_preview, to_rust_string(env, string), pos);

    // TODO: avoid string copying
    let left: id = msg![env; string substringFromIndex:pos];
    let range: NSRange = msg![env; left rangeOfString:stop_string];
    if range.location == 0 {
        // [DIAG-C1] Log scanUpToString failure (stop string at current position)
        log!("[DIAG-C1-SCAN-UPTO] pos={} stop='{}' result=FAILED(at_start)", pos, &stop_str_preview[..50.min(stop_str_preview.len())]);
        *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    let scan_len = if range.location == NSNotFound as NSUInteger {
        len - pos
    } else {
        range.location
    };
    assert!(pos + scan_len <= len);
    *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos: pos + scan_len };

    if !result.is_null() {
        let copy: id = msg![env; left substringToIndex:scan_len];
        let scanned_str = to_rust_string(env, copy);
        // [DIAG-C1] Log scanUpToString success with scanned content
        log!("[DIAG-C1-SCAN-UPTO] pos={} stop='{}' scanned='{}' success=true",
             pos, &stop_str_preview[..50.min(stop_str_preview.len())],
             &scanned_str[..80.min(scanned_str.len())]);
        log_dbg!("scanned '{}' up to {}", scanned_str, pos + scan_len);
        // Note: substring is already autoreleased
        env.mem.write(result, copy);
    } else {
        // [DIAG-C1] Log scanUpToString success (no output requested)
        log!("[DIAG-C1-SCAN-UPTO] pos={} stop='{}' scanned_len={} success=true(no_output)",
             pos, &stop_str_preview[..50.min(stop_str_preview.len())], scan_len);
    }
    true
}

- (bool)scanString:(id)scan_string // NSString *
        intoString:(MutPtr<id>)result { // NSString **
    skip_characters(env, this);

    let NSScannerHostObject { to_be_skipped, string, len, pos } = std::mem::take(env.objc.borrow_mut::<NSScannerHostObject>(this));
    let scan_str_preview = to_rust_string(env, scan_string);
    log_dbg!("scanString:{} intoString: from '{}' at {}", scan_str_preview, to_rust_string(env, string), pos);

    // TODO: avoid string copying
    let left: id = msg![env; string substringFromIndex:pos];
    let same_prefix: bool = msg![env; left hasPrefix:scan_string];
    if !same_prefix {
        // [DIAG-C2] Log scanString failure (prefix mismatch)
        log!("[DIAG-C2-SCAN-STR] pos={} match='{}' success=false",
             pos, &scan_str_preview[..50.min(scan_str_preview.len())]);
        *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    let scan_len: NSUInteger = msg![env; scan_string length];
    assert!(pos + scan_len <= len);
    *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos: pos + scan_len };

    // [DIAG-C2] Log scanString success
    log!("[DIAG-C2-SCAN-STR] pos={} match='{}' success=true",
         pos, &scan_str_preview[..50.min(scan_str_preview.len())]);

    if !result.is_null() {
        let copy: id = msg![env; scan_string copy];
        autorelease(env, copy);
        env.mem.write(result, copy);
    }
    true
}

- (bool)scanInt:(MutPtr<i32>)result {
    skip_characters(env, this);

    let NSScannerHostObject { to_be_skipped, string, len, pos } = std::mem::take(env.objc.borrow_mut::<NSScannerHostObject>(this));
    let left: id = msg![env; string substringFromIndex:pos];
    if left == nil {
        // [DIAG-C3] Log scanInt failure (nil substring)
        log!("[DIAG-C3-SCAN-INT] pos={} value=NONE success=false(nil)", pos);
        *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    let st = to_rust_string(env, left);
    let mut cutoff = st.len();
    for (i, c) in st.char_indices() {
        if !c.is_ascii_digit() && c != '+' && c != '-' {
            cutoff = i;
            break;
        }
    }
    if cutoff == 0 {
        // [DIAG-C3] Log scanInt failure (no digits found)
        log!("[DIAG-C3-SCAN-INT] pos={} input='{}' success=false(no_digits)",
             pos, &st[..20.min(st.len())]);
        log_dbg!("scanInt: no valid int found for '{}'", st);
        *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    // TODO: handle over/underflow properly
    let res: i32 = st[..cutoff].parse().unwrap_or(0);
    // [DIAG-C3] Log scanInt success
    log!("[DIAG-C3-SCAN-INT] pos={} value={} success=true", pos, res);
    log_dbg!("scanInt: from '{}' -> {}", st, res);

    if !result.is_null() {
        env.mem.write(result, res);
    }

    *env.objc.borrow_mut::<NSScannerHostObject>(this) = NSScannerHostObject { to_be_skipped, string, len, pos: pos + cutoff as NSUInteger };
    true
}

// [DIAG-SCANFLOAT] Implementation per Apple documentation
// https://developer.apple.com/documentation/foundation/nsscanner/1411677-scanfloat
- (bool)scanFloat:(MutPtr<f32>)result {
    log!("[DIAG-SCANFLOAT] scanFloat: called at pos {}",
         env.objc.borrow::<NSScannerHostObject>(this).pos);

    skip_characters(env, this);

    let NSScannerHostObject { to_be_skipped, string, len, pos } =
        std::mem::take(env.objc.borrow_mut::<NSScannerHostObject>(this));

    if pos >= len {
        *env.objc.borrow_mut::<NSScannerHostObject>(this) =
            NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    let left: id = msg![env; string substringFromIndex:pos];
    let st = to_rust_string(env, left);

    // Parse float: [+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?
    let mut end = 0;
    let mut found_digit = false;
    let mut found_dot = false;
    let chars: Vec<char> = st.chars().collect();

    // Handle optional sign
    if end < chars.len() && (chars[end] == '+' || chars[end] == '-') {
        end += 1;
    }

    // Scan digits and optional decimal point
    while end < chars.len() {
        let c = chars[end];
        if c.is_ascii_digit() {
            found_digit = true;
            end += 1;
        } else if c == '.' && !found_dot {
            found_dot = true;
            end += 1;
        } else {
            break;
        }
    }

    // Handle exponent part (e.g., 1.5e10)
    if end < chars.len() && found_digit && (chars[end] == 'e' || chars[end] == 'E') {
        let exp_start = end;
        end += 1;
        // Optional exponent sign
        if end < chars.len() && (chars[end] == '+' || chars[end] == '-') {
            end += 1;
        }
        // Exponent digits
        let mut exp_digits = false;
        while end < chars.len() && chars[end].is_ascii_digit() {
            exp_digits = true;
            end += 1;
        }
        // If no exponent digits, revert to before 'e'
        if !exp_digits {
            end = exp_start;
        }
    }

    if !found_digit {
        log!("[DIAG-SCANFLOAT] no float found in '{}'", &st[..20.min(st.len())]);
        *env.objc.borrow_mut::<NSScannerHostObject>(this) =
            NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    let parsed: f32 = st[..end].parse().unwrap_or(0.0);
    log!("[DIAG-SCANFLOAT] parsed {} from '{}'", parsed, &st[..end]);

    if !result.is_null() {
        env.mem.write(result, parsed);
    }

    *env.objc.borrow_mut::<NSScannerHostObject>(this) =
        NSScannerHostObject { to_be_skipped, string, len, pos: pos + end as NSUInteger };
    true
}

// [DIAG-SCANDOUBLE] Implementation per Apple documentation
// https://developer.apple.com/documentation/foundation/nsscanner/1411893-scandouble
// Available since iOS 2.0, mirrors scanFloat: but uses f64 (double precision)
- (bool)scanDouble:(MutPtr<f64>)result {
    log!("[DIAG-SCANDOUBLE] scanDouble: called at pos {}",
         env.objc.borrow::<NSScannerHostObject>(this).pos);

    skip_characters(env, this);

    let NSScannerHostObject { to_be_skipped, string, len, pos } =
        std::mem::take(env.objc.borrow_mut::<NSScannerHostObject>(this));

    if pos >= len {
        log!("[DIAG-SCANDOUBLE] at end of string, returning false");
        *env.objc.borrow_mut::<NSScannerHostObject>(this) =
            NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    let left: id = msg![env; string substringFromIndex:pos];
    let st = to_rust_string(env, left);

    // Parse double: [+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?
    // Same algorithm as scanFloat:, just with f64 output
    let mut end = 0;
    let mut found_digit = false;
    let mut found_dot = false;
    let chars: Vec<char> = st.chars().collect();

    // Handle optional sign
    if end < chars.len() && (chars[end] == '+' || chars[end] == '-') {
        end += 1;
    }

    // Scan digits and optional decimal point
    while end < chars.len() {
        let c = chars[end];
        if c.is_ascii_digit() {
            found_digit = true;
            end += 1;
        } else if c == '.' && !found_dot {
            found_dot = true;
            end += 1;
        } else {
            break;
        }
    }

    // Handle exponent part (e.g., 1.5e10)
    if end < chars.len() && found_digit && (chars[end] == 'e' || chars[end] == 'E') {
        let exp_start = end;
        end += 1;
        // Optional exponent sign
        if end < chars.len() && (chars[end] == '+' || chars[end] == '-') {
            end += 1;
        }
        // Exponent digits
        let mut exp_digits = false;
        while end < chars.len() && chars[end].is_ascii_digit() {
            exp_digits = true;
            end += 1;
        }
        // If no exponent digits, revert to before 'e'
        if !exp_digits {
            end = exp_start;
        }
    }

    if !found_digit {
        log!("[DIAG-SCANDOUBLE] no double found in '{}'", &st[..20.min(st.len())]);
        *env.objc.borrow_mut::<NSScannerHostObject>(this) =
            NSScannerHostObject { to_be_skipped, string, len, pos };
        return false;
    }

    let parsed: f64 = st[..end].parse().unwrap_or(0.0);
    log!("[DIAG-SCANDOUBLE] parsed {} from '{}'", parsed, &st[..end]);

    if !result.is_null() {
        env.mem.write(result, parsed);
    }

    *env.objc.borrow_mut::<NSScannerHostObject>(this) =
        NSScannerHostObject { to_be_skipped, string, len, pos: pos + end as NSUInteger };
    true
}

@end

};

// Helper functions, skips characters from `charactersToBeSkipped` set
fn skip_characters(env: &mut Environment, scanner: id) {
    let &NSScannerHostObject {
        to_be_skipped,
        string,
        len,
        mut pos,
    } = env.objc.borrow::<NSScannerHostObject>(scanner);
    loop {
        if pos >= len {
            break;
        }
        let c: unichar = msg![env; string characterAtIndex:pos];
        if msg![env; to_be_skipped characterIsMember:c] {
            pos += 1;
        } else {
            break;
        }
    }
    env.objc.borrow_mut::<NSScannerHostObject>(scanner).pos = pos;
}
