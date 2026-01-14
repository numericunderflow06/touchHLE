/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIActivityIndicatorView`.

use crate::frameworks::foundation::NSInteger;
use crate::objc::{
    id, impl_HostObject_with_superclass, msg, msg_super, objc_classes, ClassExports, NSZonePtr,
};

use super::ui_view::UIViewHostObject;

type UIActivityIndicatorViewStyle = NSInteger;

/// Host object for UIActivityIndicatorView state
#[derive(Default)]
struct UIActivityIndicatorViewHostObject {
    superclass: UIViewHostObject,
    /// Whether the view should hide when stopAnimating is called
    hides_when_stopped: bool,
    /// Whether the indicator is currently animating
    animating: bool,
}
impl_HostObject_with_superclass!(UIActivityIndicatorViewHostObject);

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation UIActivityIndicatorView: UIView

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::<UIActivityIndicatorViewHostObject>::default();
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithActivityIndicatorStyle:(UIActivityIndicatorViewStyle)_style {
    // TODO: proper init with style
    msg_super![env; this init]
}

- (())startAnimating {
    log!("[DIAG-E1] UIActivityIndicatorView {:?} startAnimating", this);
    env.objc.borrow_mut::<UIActivityIndicatorViewHostObject>(this).animating = true;
}

- (())stopAnimating {
    let host_obj = env.objc.borrow_mut::<UIActivityIndicatorViewHostObject>(this);
    host_obj.animating = false;
    let hides_when_stopped = host_obj.hides_when_stopped;
    log!("[DIAG-E1] UIActivityIndicatorView {:?} stopAnimating (hides_when_stopped={})", this, hides_when_stopped);
    if hides_when_stopped {
        // Hide the view when stopAnimating is called and hidesWhenStopped is true
        () = msg![env; this setHidden:true];
    }
}

- (bool)isAnimating {
    env.objc.borrow::<UIActivityIndicatorViewHostObject>(this).animating
}

- (())setHidesWhenStopped:(bool)hides {
    log!("[DIAG-E1] UIActivityIndicatorView {:?} setHidesWhenStopped:{}", this, hides);
    env.objc.borrow_mut::<UIActivityIndicatorViewHostObject>(this).hides_when_stopped = hides;
}

- (bool)hidesWhenStopped {
    env.objc.borrow::<UIActivityIndicatorViewHostObject>(this).hides_when_stopped
}

@end

};
