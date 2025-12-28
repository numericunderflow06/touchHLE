/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! AddressBook.framework stubs
//!
//! The AddressBook framework provides access to the user's contacts.
//! Most games use this for "invite friends" or social features which can
//! be safely stubbed.

use crate::dyld::{export_c_func, ConstantExports, FunctionExports, HostConstant, HostDylib};
use crate::mem::{ConstPtr, MutPtr, ConstVoidPtr, MutVoidPtr};
use crate::Environment;

pub const DYLIB: HostDylib = HostDylib {
    path: "/System/Library/Frameworks/AddressBook.framework/AddressBook",
    aliases: &[],
    class_exports: &[],
    constant_exports: &[CONSTANTS],
    function_exports: &[FUNCTIONS],
};

// Address Book error codes
const kABOperationNotPermittedByStoreError: i32 = 0;

// Opaque types
type ABAddressBookRef = MutVoidPtr;
type ABRecordRef = MutVoidPtr;
type ABMultiValueRef = MutVoidPtr;
type CFArrayRef = ConstVoidPtr;
type CFStringRef = ConstVoidPtr;
type CFErrorRef = MutPtr<ConstVoidPtr>;

// Property IDs
type ABPropertyID = i32;
type ABRecordID = i32;

fn ABAddressBookCreate(_env: &mut Environment) -> ABAddressBookRef {
    log!("Warning: ABAddressBookCreate - stubbed, returning NULL (no contacts access)");
    MutVoidPtr::null()
}

fn ABAddressBookCreateWithOptions(
    _env: &mut Environment,
    _options: ConstVoidPtr, // CFDictionaryRef
    _error: CFErrorRef,
) -> ABAddressBookRef {
    log!("Warning: ABAddressBookCreateWithOptions - stubbed, returning NULL");
    MutVoidPtr::null()
}

fn ABAddressBookGetAuthorizationStatus(_env: &mut Environment) -> i32 {
    log!("Warning: ABAddressBookGetAuthorizationStatus - returning kABAuthorizationStatusDenied (2)");
    2 // kABAuthorizationStatusDenied
}

fn ABAddressBookRequestAccessWithCompletion(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
    _completion: ConstVoidPtr, // block
) {
    log!("Warning: ABAddressBookRequestAccessWithCompletion - stubbed (access denied)");
    // The completion block should be called with (false, error) but we can't easily do that
}

fn ABAddressBookCopyArrayOfAllPeople(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
) -> CFArrayRef {
    log!("Warning: ABAddressBookCopyArrayOfAllPeople - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn ABAddressBookCopyArrayOfAllGroups(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
) -> CFArrayRef {
    log!("Warning: ABAddressBookCopyArrayOfAllGroups - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn ABAddressBookGetPersonCount(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
) -> i32 {
    log!("Warning: ABAddressBookGetPersonCount - stubbed, returning 0");
    0
}

fn ABAddressBookGetGroupCount(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
) -> i32 {
    log!("Warning: ABAddressBookGetGroupCount - stubbed, returning 0");
    0
}

fn ABAddressBookGetPersonWithRecordID(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
    _record_id: ABRecordID,
) -> ABRecordRef {
    log!("Warning: ABAddressBookGetPersonWithRecordID - stubbed, returning NULL");
    MutVoidPtr::null()
}

fn ABAddressBookSave(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
    _error: CFErrorRef,
) -> bool {
    log!("Warning: ABAddressBookSave - stubbed, returning false");
    false
}

fn ABAddressBookHasUnsavedChanges(
    _env: &mut Environment,
    _address_book: ABAddressBookRef,
) -> bool {
    log!("Warning: ABAddressBookHasUnsavedChanges - stubbed, returning false");
    false
}

fn ABAddressBookRevert(_env: &mut Environment, _address_book: ABAddressBookRef) {
    log!("Warning: ABAddressBookRevert - stubbed");
}

fn ABRecordCopyValue(
    _env: &mut Environment,
    _record: ABRecordRef,
    _property: ABPropertyID,
) -> ConstVoidPtr { // CFTypeRef
    log!("Warning: ABRecordCopyValue - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn ABRecordSetValue(
    _env: &mut Environment,
    _record: ABRecordRef,
    _property: ABPropertyID,
    _value: ConstVoidPtr, // CFTypeRef
    _error: CFErrorRef,
) -> bool {
    log!("Warning: ABRecordSetValue - stubbed, returning false");
    false
}

fn ABRecordCopyCompositeName(
    _env: &mut Environment,
    _record: ABRecordRef,
) -> CFStringRef {
    log!("Warning: ABRecordCopyCompositeName - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn ABRecordGetRecordID(
    _env: &mut Environment,
    _record: ABRecordRef,
) -> ABRecordID {
    log!("Warning: ABRecordGetRecordID - stubbed, returning -1");
    -1 // kABRecordInvalidID
}

fn ABPersonCreate(_env: &mut Environment) -> ABRecordRef {
    log!("Warning: ABPersonCreate - stubbed, returning NULL");
    MutVoidPtr::null()
}

fn ABMultiValueGetCount(
    _env: &mut Environment,
    _multi_value: ABMultiValueRef,
) -> i32 {
    log!("Warning: ABMultiValueGetCount - stubbed, returning 0");
    0
}

fn ABMultiValueCopyValueAtIndex(
    _env: &mut Environment,
    _multi_value: ABMultiValueRef,
    _index: i32,
) -> ConstVoidPtr { // CFTypeRef
    log!("Warning: ABMultiValueCopyValueAtIndex - stubbed, returning NULL");
    ConstVoidPtr::null()
}

fn ABMultiValueCopyLabelAtIndex(
    _env: &mut Environment,
    _multi_value: ABMultiValueRef,
    _index: i32,
) -> CFStringRef {
    log!("Warning: ABMultiValueCopyLabelAtIndex - stubbed, returning NULL");
    ConstVoidPtr::null()
}

const CONSTANTS: ConstantExports = &[
    // Property constants
    ("_kABPersonFirstNameProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(0))),
    ("_kABPersonLastNameProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(1))),
    ("_kABPersonMiddleNameProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(2))),
    ("_kABPersonPrefixProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(3))),
    ("_kABPersonSuffixProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(4))),
    ("_kABPersonNicknameProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(5))),
    ("_kABPersonOrganizationProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(6))),
    ("_kABPersonJobTitleProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(7))),
    ("_kABPersonDepartmentProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(8))),
    ("_kABPersonEmailProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(9))),
    ("_kABPersonPhoneProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(10))),
    ("_kABPersonAddressProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(11))),
    ("_kABPersonBirthdayProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(12))),
    ("_kABPersonNoteProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(13))),
    ("_kABPersonURLProperty", HostConstant::Custom(|_| ConstVoidPtr::from_bits(14))),

    // Label constants
    ("_kABHomeLabel", HostConstant::NSString("_$!<Home>!$_")),
    ("_kABWorkLabel", HostConstant::NSString("_$!<Work>!$_")),
    ("_kABOtherLabel", HostConstant::NSString("_$!<Other>!$_")),

    // Phone labels
    ("_kABPersonPhoneMobileLabel", HostConstant::NSString("_$!<Mobile>!$_")),
    ("_kABPersonPhoneMainLabel", HostConstant::NSString("_$!<Main>!$_")),
    ("_kABPersonPhoneHomeFAXLabel", HostConstant::NSString("_$!<HomeFAX>!$_")),
    ("_kABPersonPhoneWorkFAXLabel", HostConstant::NSString("_$!<WorkFAX>!$_")),
    ("_kABPersonPhonePagerLabel", HostConstant::NSString("_$!<Pager>!$_")),
];

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(ABAddressBookCreate()),
    export_c_func!(ABAddressBookCreateWithOptions(_, _)),
    export_c_func!(ABAddressBookGetAuthorizationStatus()),
    export_c_func!(ABAddressBookRequestAccessWithCompletion(_, _)),
    export_c_func!(ABAddressBookCopyArrayOfAllPeople(_)),
    export_c_func!(ABAddressBookCopyArrayOfAllGroups(_)),
    export_c_func!(ABAddressBookGetPersonCount(_)),
    export_c_func!(ABAddressBookGetGroupCount(_)),
    export_c_func!(ABAddressBookGetPersonWithRecordID(_, _)),
    export_c_func!(ABAddressBookSave(_, _)),
    export_c_func!(ABAddressBookHasUnsavedChanges(_)),
    export_c_func!(ABAddressBookRevert(_)),
    export_c_func!(ABRecordCopyValue(_, _)),
    export_c_func!(ABRecordSetValue(_, _, _, _)),
    export_c_func!(ABRecordCopyCompositeName(_)),
    export_c_func!(ABRecordGetRecordID(_)),
    export_c_func!(ABPersonCreate()),
    export_c_func!(ABMultiValueGetCount(_)),
    export_c_func!(ABMultiValueCopyValueAtIndex(_, _)),
    export_c_func!(ABMultiValueCopyLabelAtIndex(_, _)),
];
