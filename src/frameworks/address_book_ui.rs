/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! AddressBookUI.framework stubs
//!
//! The AddressBookUI framework provides UI components for displaying and
//! selecting contacts. Most games use this for "invite friends" features
//! which can be safely stubbed.

use crate::dyld::{ConstantExports, HostDylib};
use crate::objc::{id, nil, objc_classes, ClassExports, TrivialHostObject};

pub const DYLIB: HostDylib = HostDylib {
    path: "/System/Library/Frameworks/AddressBookUI.framework/AddressBookUI",
    aliases: &[],
    class_exports: &[CLASSES],
    constant_exports: &[CONSTANTS],
    function_exports: &[],
};

const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

// ABPeoplePickerNavigationController - lets user select contacts
@implementation ABPeoplePickerNavigationController: UINavigationController

+ (id)alloc {
    log!("Warning: ABPeoplePickerNavigationController alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    log!("Warning: ABPeoplePickerNavigationController init - stubbed");
    this
}

- (())setPeoplePickerDelegate:(id)_delegate {
    log!("Warning: ABPeoplePickerNavigationController setPeoplePickerDelegate: - stubbed");
}

- (id)peoplePickerDelegate {
    log!("Warning: ABPeoplePickerNavigationController peoplePickerDelegate - stubbed");
    nil
}

- (())setDisplayedProperties:(id)_properties {
    log!("Warning: ABPeoplePickerNavigationController setDisplayedProperties: - stubbed");
}

- (id)displayedProperties {
    log!("Warning: ABPeoplePickerNavigationController displayedProperties - stubbed");
    nil
}

@end

// ABPersonViewController - displays a single contact
@implementation ABPersonViewController: UIViewController

+ (id)alloc {
    log!("Warning: ABPersonViewController alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    log!("Warning: ABPersonViewController init - stubbed");
    this
}

- (())setPersonViewDelegate:(id)_delegate {
    log!("Warning: ABPersonViewController setPersonViewDelegate: - stubbed");
}

- (())setDisplayedPerson:(id)_person {
    log!("Warning: ABPersonViewController setDisplayedPerson: - stubbed");
}

- (())setAllowsEditing:(bool)_allows {
    log!("Warning: ABPersonViewController setAllowsEditing: - stubbed");
}

- (())setDisplayedProperties:(id)_properties {
    log!("Warning: ABPersonViewController setDisplayedProperties: - stubbed");
}

@end

// ABNewPersonViewController - creates new contacts
@implementation ABNewPersonViewController: UIViewController

+ (id)alloc {
    log!("Warning: ABNewPersonViewController alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    log!("Warning: ABNewPersonViewController init - stubbed");
    this
}

- (())setNewPersonViewDelegate:(id)_delegate {
    log!("Warning: ABNewPersonViewController setNewPersonViewDelegate: - stubbed");
}

- (())setDisplayedPerson:(id)_person {
    log!("Warning: ABNewPersonViewController setDisplayedPerson: - stubbed");
}

@end

// ABUnknownPersonViewController - for unknown contacts
@implementation ABUnknownPersonViewController: UIViewController

+ (id)alloc {
    log!("Warning: ABUnknownPersonViewController alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    log!("Warning: ABUnknownPersonViewController init - stubbed");
    this
}

- (())setUnknownPersonViewDelegate:(id)_delegate {
    log!("Warning: ABUnknownPersonViewController setUnknownPersonViewDelegate: - stubbed");
}

- (())setDisplayedPerson:(id)_person {
    log!("Warning: ABUnknownPersonViewController setDisplayedPerson: - stubbed");
}

- (())setAllowsAddingToAddressBook:(bool)_allows {
    log!("Warning: ABUnknownPersonViewController setAllowsAddingToAddressBook: - stubbed");
}

- (())setAllowsActions:(bool)_allows {
    log!("Warning: ABUnknownPersonViewController setAllowsActions: - stubbed");
}

@end

};

const CONSTANTS: ConstantExports = &[];
