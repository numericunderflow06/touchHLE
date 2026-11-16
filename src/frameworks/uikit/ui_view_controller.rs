/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIViewController`.
//!
//! Resources:
//! - [View Controller Programming Guide for iOS (Legacy)](https://developer.apple.com/library/archive/documentation/WindowsViews/Conceptual/ViewControllerPGforiOSLegacy/BasicViewControllers/BasicViewControllers.html)

use crate::frameworks::core_graphics::CGRect;
use crate::frameworks::foundation::ns_objc_runtime::NSStringFromClass;
use crate::frameworks::foundation::ns_string::{from_rust_string, get_static_str, to_rust_string};
use crate::frameworks::foundation::{NSInteger, NSTimeInterval};
use crate::frameworks::uikit::ui_application::{
    UIInterfaceOrientation, UIInterfaceOrientationPortrait,
};
use crate::frameworks::uikit::ui_view::set_view_controller;
use crate::objc::{
    autorelease, id, msg, msg_class, nil, objc_classes, release, retain, todo_objc_setter, Class,
    ClassExports, HostObject, NSZonePtr,
};
use crate::Environment;

pub mod ui_navigation_controller;

#[derive(Default)]
pub struct UIViewControllerHostObject {
    /// The root view.
    /// `UIView*`
    view: id,
    /// Nib name to be used at the load
    /// of the root view, may be nil.
    /// `NSString*`
    nib_name: id,
    /// Bundle to be used for load
    /// of the nib by name, may be nil.
    /// `NSBundle*`
    bundle: id,
    /// The view controller this one is presenting modally, if any.
    /// `UIViewController*`, strong.
    modal_view_controller: id,
    /// The view controller that is presenting this one modally, if any.
    /// `UIViewController*`, weak.
    parent_view_controller: id,
}
impl HostObject for UIViewControllerHostObject {}

type UIModalTransitionStyle = NSInteger;

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation UIViewController: UIResponder

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::<UIViewControllerHostObject>::default();
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

// TODO: this should be a designated initializer
- (id)initWithNibName:(id)nib_name // NSString *
               bundle:(id)bundle { // NSBundle *
    retain(env, nib_name);
    retain(env, bundle);

    log_dbg!("[(UIViewController*){:?} initWithNibName:{:?} bundle:{:?}]", this, nib_name, bundle);

    env.objc.borrow_mut::<UIViewControllerHostObject>(this).nib_name = nib_name;
    env.objc.borrow_mut::<UIViewControllerHostObject>(this).bundle = bundle;

    this
}

- (id)initWithCoder:(id)coder {
    let key_ns_string = get_static_str(env, "UIView");
    let view: id = msg![env; coder decodeObjectForKey:key_ns_string];

    () = msg![env; this setView:view];

    this
}

- (())dealloc {
    let &UIViewControllerHostObject {
        view,
        nib_name,
        bundle,
        modal_view_controller,
        ..
    } = env.objc.borrow(this);

    if view != nil {
        set_view_controller(env, view, nil);
    }
    release(env, view);
    release(env, nib_name);
    release(env, bundle);
    if modal_view_controller != nil {
        env.objc
            .borrow_mut::<UIViewControllerHostObject>(modal_view_controller)
            .parent_view_controller = nil;
        release(env, modal_view_controller);
    }

    env.objc.dealloc_object(this, &mut env.mem);
}

- (())loadView {
    let bundle: id = env.objc.borrow::<UIViewControllerHostObject>(this).bundle;
    let bundle: id = if bundle == nil {
        msg_class![env; NSBundle mainBundle]
    } else {
        bundle
    };

    let nib_name: id = get_nib_name(env, this, bundle);
    if nib_name != nil {
        // If we do have nib name, try to load it!
        log_dbg!(
            "Load {:?} view controller's view by nib, using name {}", this, to_rust_string(env, nib_name)
        );

        let nib: id = msg_class![env; UINib nibWithNibName:nib_name bundle:bundle];
        release(env, nib_name);

        // The NIB's File's Owner will be substituted by `this`,
        // implicitly loading the view as well
        let _: id = msg![env; nib instantiateWithOwner:this options:nil];

        let view = env.objc.borrow::<UIViewControllerHostObject>(this).view;
        // Having nil view at this point probably mean that
        // out nib's parsing is wrong.
        // Also we assume here the case of a "detached nib file"
        // TODO: support "integrated nib file"
        assert!(view != nil);

        return;
    };

    // As a last resort, use plain UIVIew for the root view
    let class: Class = msg![env; this class];
    log!("Unable to load {:?} {} view controller's view by nib, using plain UIView", this, env.objc.get_class_name(class).to_string());
    let view: id = msg_class![env; UIView alloc];
    // Docs are saying that "an empty UIView" is created,
    // but testing reveals that frame matches the screen one
    // (at least on the simulator)
    let screen: id = msg_class![env; UIScreen mainScreen];
    let app_frame: CGRect = msg![env; screen applicationFrame];
    let view: id = msg![env; view initWithFrame:app_frame];
    () = msg![env; this setView:view];
}

- (())setView:(id)new_view { // UIView*
    let host_obj = env.objc.borrow_mut::<UIViewControllerHostObject>(this);
    let old_view = std::mem::replace(&mut host_obj.view, new_view);
    if old_view != nil {
        set_view_controller(env, old_view, nil);
    }
    if new_view != nil {
        set_view_controller(env, new_view, this);
    }
    retain(env, new_view);
    release(env, old_view);
}
- (id)view {
    let view = env.objc.borrow_mut::<UIViewControllerHostObject>(this).view;
    if view == nil {
        () = msg![env; this loadView];
        let view = env.objc.borrow_mut::<UIViewControllerHostObject>(this).view;
        () = msg![env; this viewDidLoad];
        view
    } else {
        view
    }
}

// Usually overridden by the application
- (())viewDidLoad {
    log_dbg!("[(UIViewController*){:?} viewDidLoad]", this);
}
- (())viewWillAppear:(bool)animated {
    log_dbg!("[(UIViewController*){:?} viewWillAppear:{}]", this, animated);
}
- (())viewDidAppear:(bool)animated {
    log_dbg!("[(UIViewController*){:?} viewDidAppear:{}]", this, animated);
}
- (())viewWillDisappear:(bool)animated {
    log_dbg!("[(UIViewController*){:?} viewWillDisappear:{}]", this, animated);
}
- (())viewDidDisappear:(bool)animated {
    log_dbg!("[(UIViewController*){:?} viewDidDisappear:{}]", this, animated);
}

- (())setTitle:(id)title { // NSString *
    todo_objc_setter!(this, to_rust_string(env, title));
}
- (())setEditing:(bool)editing {
    todo_objc_setter!(this, editing);
}
- (())setWantsFullScreenLayout:(bool)wants {
    todo_objc_setter!(this, wants);
}
- (())setHidesBottomBarWhenPushed:(bool)hides {
    todo_objc_setter!(this, hides);
}
- (())setModalTransitionStyle:(UIModalTransitionStyle)style {
    todo_objc_setter!(this, style);
}

// Modal presentation (the API before iOS 5).
// TODO: animations and transition styles; the change is immediate.

- (())presentModalViewController:(id)modal // UIViewController*
                        animated:(bool)animated {
    assert!(modal != nil && modal != this);
    if env.objc.borrow::<UIViewControllerHostObject>(this).modal_view_controller != nil {
        log!(
            "Warning: [(UIViewController*){:?} presentModalViewController:{:?} animated:{}] while already presenting one, ignoring.",
            this,
            modal,
            animated,
        );
        return;
    }
    log_dbg!(
        "[(UIViewController*){:?} presentModalViewController:{:?} animated:{}]",
        this,
        modal,
        animated,
    );

    retain(env, modal);
    env.objc
        .borrow_mut::<UIViewControllerHostObject>(this)
        .modal_view_controller = modal;
    env.objc
        .borrow_mut::<UIViewControllerHostObject>(modal)
        .parent_view_controller = this;

    // The presented view covers the screen: it goes into the window, on top
    // of the presenting view controller's view. -[UIWindow addSubview:] sends
    // the appearance messages and gives the new view the interface
    // orientation, as it does for any view controller's view.
    let this_view: id = msg![env; this view];
    let window: id = msg![env; this_view window];
    let modal_view: id = msg![env; modal view];
    if window == nil {
        log!(
            "Warning: [(UIViewController*){:?} presentModalViewController:{:?} animated:{}]: the presenting view is not in a window, so nothing is shown.",
            this,
            modal,
            animated,
        );
        return;
    }
    () = msg![env; this viewWillDisappear:animated];
    () = msg![env; window addSubview:modal_view];
    () = msg![env; this viewDidDisappear:animated];
}

- (())dismissModalViewControllerAnimated:(bool)animated {
    let &UIViewControllerHostObject {
        modal_view_controller: modal,
        parent_view_controller: parent,
        ..
    } = env.objc.borrow(this);
    if modal == nil {
        // Sent to the presented view controller itself, this is passed on
        // to the one that presented it.
        if parent != nil {
            () = msg![env; parent dismissModalViewControllerAnimated:animated];
        }
        return;
    }
    log_dbg!(
        "[(UIViewController*){:?} dismissModalViewControllerAnimated:{}], dismissing {:?}",
        this,
        animated,
        modal,
    );

    () = msg![env; modal viewWillDisappear:animated];
    () = msg![env; this viewWillAppear:animated];
    let modal_view = env.objc.borrow::<UIViewControllerHostObject>(modal).view;
    if modal_view != nil {
        () = msg![env; modal_view removeFromSuperview];
    }
    () = msg![env; modal viewDidDisappear:animated];
    () = msg![env; this viewDidAppear:animated];

    env.objc
        .borrow_mut::<UIViewControllerHostObject>(this)
        .modal_view_controller = nil;
    env.objc
        .borrow_mut::<UIViewControllerHostObject>(modal)
        .parent_view_controller = nil;
    // This is usually reached from inside one of the presented view
    // controller's own methods (the action of one of its buttons, a call to
    // its delegate), so it has to outlive this call.
    autorelease(env, modal);
}

- (id)modalViewController {
    env.objc.borrow::<UIViewControllerHostObject>(this).modal_view_controller
}
// Before iOS 5, a modally presented view controller's parent is the view
// controller that presented it.
- (id)parentViewController {
    env.objc.borrow::<UIViewControllerHostObject>(this).parent_view_controller
}
- (())dismissMoviePlayerViewControllerAnimated {
    log!("TODO: [(UIViewController*){:?} dismissMoviePlayerViewControllerAnimated]", this); // TODO
}

- (bool)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interface_orientation {
    interface_orientation == UIInterfaceOrientationPortrait
}

// Rotation callbacks, sent by UIKit around an interface rotation (see
// `-[UIWindow addSubview:]`). The default implementations do nothing;
// subclasses override them to adjust their views.
- (())willRotateToInterfaceOrientation:(UIInterfaceOrientation)_to_orientation
                              duration:(NSTimeInterval)_duration {
}
- (())willAnimateRotationToInterfaceOrientation:(UIInterfaceOrientation)_to_orientation
                                       duration:(NSTimeInterval)_duration {
}
- (())didRotateFromInterfaceOrientation:(UIInterfaceOrientation)_from_orientation {
}

// UIResponder implementation
// From the Apple UIView docs regarding [UIResponder nextResponder]:
// "UIViewController similarly implements the method
// and returns its view’s superview."
// https://developer.apple.com/documentation/uikit/uiresponder/next?language=objc
- (id)nextResponder {
    let view = msg![env; this view];
    let next_responder = msg![env; view superview];
    log_dbg!("[(UIView*){:?} nextResponder] => {:?}", this, next_responder);
    next_responder
}

@end

};

/// A helper function to resolve suitable NIB name for a `view_controller`
/// in the `bundle`. Returns nil if fails.
///
/// Note: It's a responsibility of a caller to release the returned name
/// if not-nil!
fn get_nib_name(env: &mut Environment, view_controller: id, bundle: id) -> id {
    let provider_nib_name: id = env
        .objc
        .borrow::<UIViewControllerHostObject>(view_controller)
        .nib_name;
    if provider_nib_name != nil {
        // TODO: it's not clear how to handle situation when
        // provided nib name do not exist in the bundle.
        // It probably means that our bundle resource loading
        // is faulty, to check
        assert!(check_nib_exists(env, bundle, provider_nib_name));

        retain(env, provider_nib_name);
        return provider_nib_name;
    };

    let class: Class = msg![env; view_controller class];
    let class_name: id = NSStringFromClass(env, class);
    let class_name_str = to_rust_string(env, class_name);

    if let Some(name) = class_name_str.strip_suffix("Controller") {
        let ns_name: id = from_rust_string(env, name.to_string());
        if check_nib_exists(env, bundle, ns_name) {
            release(env, class_name);
            return ns_name;
        }
    }

    if check_nib_exists(env, bundle, class_name) {
        class_name
    } else {
        release(env, class_name);
        nil
    }
}

/// A helper function to check if `nib_name` NIB actually
/// existing in the `bundle`
fn check_nib_exists(env: &mut Environment, bundle: id, nib_name: id) -> bool {
    let type_: id = get_static_str(env, "nib");
    let res: id = msg![env; bundle pathForResource:nib_name ofType:type_];
    res != nil
}
