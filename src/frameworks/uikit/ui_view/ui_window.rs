/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIWindow`.

use super::UIViewHostObject;
use crate::dyld::{ConstantExports, HostConstant};
use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};
use crate::frameworks::foundation::ns_string;
use crate::objc::{id, msg, msg_class, msg_super, nil, objc_classes, ClassExports};
use crate::window::DeviceOrientation;

#[derive(Default)]
pub struct State {
    /// List of visible windows for internal purposes. Non-retaining!
    ///
    /// This is public because Core Animation also uses it.
    pub windows: Vec<id>,
    /// The most recent window which received `makeKeyAndVisible` message.
    /// Non-retaining!
    pub key_window: Option<id>,
}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation UIWindow: UIView

// TODO: more?

- (id)initWithFrame:(CGRect)frame {
    let this = msg_super![env; this initWithFrame:frame];
    // Undocumented: windows seem to be hidden by default on iOS, unlike views.
    // Super call to bypass the overriden setter on this class, which would post
    // a notification.
    () = msg_super![env; this setHidden:true];

    let list = &mut env.framework_state.uikit.ui_view.ui_window.windows;
    list.push(this);
    log_dbg!(
        "New window: {:?}. New list of all windows: {:?}",
        this,
        list,
    );

    this
}

// NSCoding implementation
- (id)initWithCoder:(id)coder {
    let this = msg_super![env; this initWithCoder:coder];
    // Undocumented: windows seem to be hidden by default on iOS, unlike views.
    // Super call to bypass the overriden setter on this class, which would post
    // a notification.
    () = msg_super![env; this setHidden:true];

    let list = &mut env.framework_state.uikit.ui_view.ui_window.windows;
    list.push(this);
    log_dbg!(
        "New window: {:?}. New list of all windows: {:?}",
        this,
        list,
    );

    this
}

- (())dealloc {
    if let Some(key_window) = env.framework_state.uikit.ui_view.ui_window.key_window {
        if key_window == this {
            env.framework_state.uikit.ui_view.ui_window.key_window = None;
        }
    }
    let list = &mut env.framework_state.uikit.ui_view.ui_window.windows;
    let idx = list.iter().position(|&w| w == this).unwrap();
    list.remove(idx);
    log_dbg!(
        "Deallocating window {:?}. New list of all windows: {:?}",
        this,
        list,
    );
    msg_super![env; this dealloc]
}

- (())setHidden:(bool)is_hidden {
    () = msg_super![env; this setHidden:is_hidden];

    // TODO: post UIWindowDidBecomeVisibleNotification,
    //            UIWindowDidBecomeHiddenNotification
    log_dbg!("[(UIWindow*){:?} setHidden:{:?}]", this, is_hidden);
}

- (())makeKeyWindow {
    // TODO: post UIWindowDidResignKeyNotification for previous key window
    env.framework_state.uikit.ui_view.ui_window.key_window = Some(this);

    let center: id = msg_class![env; NSNotificationCenter defaultCenter];
    let notif_name = ns_string::get_static_str(env, UIWindowDidBecomeKeyNotification);
    () = msg![env; center postNotificationName:notif_name object:this userInfo:nil];
}

- (())makeKeyAndVisible {
    // TODO: We don't currently have send any non-touch events to windows,
    // so there's no meaning in it yet.

    // FIXME: This should also bump the window to the top of the list.

    () = msg![env; this makeKeyWindow];

    // When the device is in landscape orientation, resize the window and all
    // its subviews to landscape dimensions. This simulates what UIKit does
    // on real iOS when the view controller supports landscape: it applies a
    // rotation transform and resizes the view hierarchy.
    let orientation = env.window().current_rotation();
    if matches!(orientation, DeviceOrientation::LandscapeLeft | DeviceOrientation::LandscapeRight) {
        let screen: id = msg_class![env; UIScreen mainScreen];
        let screen_bounds: CGRect = msg![env; screen bounds];
        let (sw, sh) = (screen_bounds.size.width, screen_bounds.size.height);
        log!("makeKeyAndVisible: landscape mode, resizing window to {}x{}", sw, sh);
        () = msg![env; this setFrame:screen_bounds];
        // Resize all subviews to fill the window (simulating autoresizing)
        let subviews: Vec<id> = env.objc.borrow::<UIViewHostObject>(this).subviews.clone();
        log!("makeKeyAndVisible: window has {} subviews", subviews.len());
        for subview in subviews {
            let sub_frame: CGRect = msg![env; subview frame];
            // Only resize views that were fullscreen in portrait
            if sub_frame.size.width >= 319.0 && sub_frame.size.height >= 479.0 {
                let new_frame = CGRect {
                    origin: sub_frame.origin,
                    size: screen_bounds.size,
                };
                () = msg![env; subview setFrame:new_frame];
                // Also resize grandchildren (e.g. EAGLView inside a container)
                let grandchildren: Vec<id> = env.objc.borrow::<UIViewHostObject>(subview).subviews.clone();
                for grandchild in grandchildren {
                    let gc_frame: CGRect = msg![env; grandchild frame];
                    if gc_frame.size.width >= 319.0 && gc_frame.size.height >= 479.0 {
                        let new_gc_frame = CGRect {
                            origin: gc_frame.origin,
                            size: screen_bounds.size,
                        };
                        () = msg![env; grandchild setFrame:new_gc_frame];
                    }
                }
            }
        }
    }

    // TODO: post UIWindowDidBecomeVisibleNotification
    () = msg![env; this setHidden:false];
}

// UIResponder implementation
// From the Apple UIView docs regarding [UIResponder nextResponder]:
// "UIWindow returns the application object."
- (id)nextResponder {
    msg_class![env; UIApplication sharedApplication]
}

- (())addSubview:(id)view {
    log_dbg!("[(UIWindow*){:?} addSubview:{:?}] => ()", this, view);

    // When in landscape mode, resize fullscreen subviews to landscape dimensions
    let orientation = env.window().current_rotation();
    if view != nil && matches!(orientation, DeviceOrientation::LandscapeLeft | DeviceOrientation::LandscapeRight) {
        let view_frame: CGRect = msg![env; view frame];
        let (vw, vh) = (view_frame.size.width, view_frame.size.height);
        // If the view was sized for portrait (width < height), resize to landscape
        if vh > vw && vw >= 319.0 && vh >= 479.0 {
            let screen: id = msg_class![env; UIScreen mainScreen];
            let screen_bounds: CGRect = msg![env; screen bounds];
            let new_frame = CGRect {
                origin: view_frame.origin,
                size: screen_bounds.size,
            };
            () = msg![env; view setFrame:new_frame];
            let (nw, nh) = (screen_bounds.size.width, screen_bounds.size.height);
            log!("UIWindow.addSubview: resized view to {}x{} for landscape", nw, nh);
        }
    }

    if view == nil || env.objc.borrow::<UIViewHostObject>(view).view_controller == nil {
        () = msg_super![env; this addSubview:view];
        return;
    }

    // Below we treat a special case of adding view controller's view
    // to a window, in order to generate display related notifications

    if env.objc.borrow::<UIViewHostObject>(this).subviews.contains(&view) {
        // For the case of existing view hidden by another view,
        // we need to delay a below sequence up until obstructions are removed
        log!("TODO: case of existing view hidden by another view for sending view[Will,Did]Appear");
    }

    let vc = env.objc.borrow::<UIViewHostObject>(view).view_controller;
    () = msg![env; vc viewWillAppear:false];
    () = msg_super![env; this addSubview:view];
    () = msg![env; vc viewDidAppear:false];
}

- (CGPoint)convertPoint:(CGPoint)point
             fromWindow:(id)other { // UIWindow*
    let this_layer: id = msg![env; this layer];
    // Resolves to nil if other is nil.
    let other_layer: id = msg![env; other layer];
    msg![env; this_layer convertPoint:point fromLayer:other_layer]
}
- (CGPoint)convertPoint:(CGPoint)point
               toWindow:(id)other { // UIWindow*
    let this_layer: id = msg![env; this layer];
    // Resolves to nil if other is nil.
    let other_layer: id = msg![env; other layer];
    msg![env; this_layer convertPoint:point toLayer:other_layer]
}

@end

};

/// Window life-cycle notifications
/// TODO: more notifications
const UIWindowDidBecomeKeyNotification: &str = "UIWindowDidBecomeKeyNotification";
/// Keyboard notifications
/// TODO: more keyboard notifications
pub const UIKeyboardWillShowNotification: &str = "UIKeyboardWillShowNotification";
pub const UIKeyboardDidShowNotification: &str = "UIKeyboardDidShowNotification";
pub const UIKeyboardWillHideNotification: &str = "UIKeyboardWillHideNotification";
pub const UIKeyboardDidHideNotification: &str = "UIKeyboardDidHideNotification";
pub const UIKeyboardBoundsUserInfoKey: &str = "UIKeyboardBoundsUserInfoKey";

pub const CONSTANTS: ConstantExports = &[
    (
        "_UIWindowDidBecomeKeyNotification",
        HostConstant::NSString(UIWindowDidBecomeKeyNotification),
    ),
    (
        "_UIKeyboardWillShowNotification",
        HostConstant::NSString(UIKeyboardWillShowNotification),
    ),
    (
        "_UIKeyboardDidShowNotification",
        HostConstant::NSString(UIKeyboardDidShowNotification),
    ),
    (
        "_UIKeyboardWillHideNotification",
        HostConstant::NSString(UIKeyboardWillHideNotification),
    ),
    (
        "_UIKeyboardDidHideNotification",
        HostConstant::NSString(UIKeyboardDidHideNotification),
    ),
    (
        "_UIKeyboardBoundsUserInfoKey",
        HostConstant::NSString(UIKeyboardBoundsUserInfoKey),
    ),
];
