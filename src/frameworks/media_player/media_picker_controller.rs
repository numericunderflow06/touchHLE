/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `MPMediaPickerController`.
//!
//! The emulated device has no music on it (see `MPMediaQuery`, which finds
//! nothing), so the picker is what it is on such a device: a title bar with
//! the button that closes it, and nothing to pick. Closing it tells the
//! delegate that the user cancelled.

use crate::frameworks::core_graphics::{CGFloat, CGPoint, CGRect, CGSize};
use crate::frameworks::foundation::ns_string::get_static_str;
use crate::frameworks::foundation::{NSInteger, NSUInteger};
use crate::frameworks::uikit::ui_application::UIInterfaceOrientation;
use crate::frameworks::uikit::ui_font::UITextAlignmentCenter;
use crate::frameworks::uikit::ui_view::ui_control::ui_button::UIButtonTypeRoundedRect;
use crate::frameworks::uikit::ui_view::ui_control::{
    UIControlEventTouchUpInside, UIControlStateNormal,
};
use crate::frameworks::uikit::ui_view_controller::UIViewControllerHostObject;
use crate::objc::{
    id, impl_HostObject_with_superclass, msg, msg_class, msg_super, nil, objc_classes, release,
    retain, ClassExports, NSZonePtr,
};

type MPMediaType = NSUInteger;
const MPMediaTypeAny: MPMediaType = !0;

#[derive(Default)]
struct MPMediaPickerControllerHostObject {
    superclass: UIViewControllerHostObject,
    /// `id<MPMediaPickerControllerDelegate>`, weak
    delegate: id,
    media_types: MPMediaType,
    allows_picking_multiple_items: bool,
    /// `NSString*`, strong
    prompt: id,
}
impl_HostObject_with_superclass!(MPMediaPickerControllerHostObject);

// Tags of the picker's subviews, for layout.
const TAG_BAR: NSInteger = 1;
const TAG_TITLE: NSInteger = 2;
const TAG_CLOSE: NSInteger = 3;
const TAG_HEADING: NSInteger = 4;
const TAG_DETAIL: NSInteger = 5;

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation MPMediaPickerController: UIViewController

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::<MPMediaPickerControllerHostObject>::default();
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    msg![env; this initWithMediaTypes:MPMediaTypeAny]
}
- (id)initWithMediaTypes:(MPMediaType)media_types {
    env.objc.borrow_mut::<MPMediaPickerControllerHostObject>(this).media_types = media_types;
    this
}

- (())dealloc {
    let prompt = env.objc.borrow::<MPMediaPickerControllerHostObject>(this).prompt;
    release(env, prompt);
    msg_super![env; this dealloc]
}

- (MPMediaType)mediaTypes {
    env.objc.borrow::<MPMediaPickerControllerHostObject>(this).media_types
}

- (id)delegate {
    env.objc.borrow::<MPMediaPickerControllerHostObject>(this).delegate
}
- (())setDelegate:(id)delegate { // id<MPMediaPickerControllerDelegate>, not retained
    env.objc.borrow_mut::<MPMediaPickerControllerHostObject>(this).delegate = delegate;
}

- (bool)allowsPickingMultipleItems {
    env.objc.borrow::<MPMediaPickerControllerHostObject>(this).allows_picking_multiple_items
}
- (())setAllowsPickingMultipleItems:(bool)allows {
    env.objc.borrow_mut::<MPMediaPickerControllerHostObject>(this).allows_picking_multiple_items = allows;
}

- (id)prompt {
    env.objc.borrow::<MPMediaPickerControllerHostObject>(this).prompt
}
- (())setPrompt:(id)prompt { // NSString*
    let prompt: id = msg![env; prompt copy];
    let old = std::mem::replace(
        &mut env.objc.borrow_mut::<MPMediaPickerControllerHostObject>(this).prompt,
        prompt
    );
    release(env, old);
}

// The picker is shown the way the app that presents it is held.
- (bool)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)_orientation {
    true
}

- (())loadView {
    let screen: id = msg_class![env; UIScreen mainScreen];
    let frame: CGRect = msg![env; screen bounds];
    let view: id = msg_class![env; _touchHLE_MPMediaPickerView alloc];
    let view: id = msg![env; view initWithFrame:frame];
    let white: id = msg_class![env; UIColor whiteColor];
    let clear: id = msg_class![env; UIColor clearColor];
    () = msg![env; view setBackgroundColor:white];

    let bar: id = msg_class![env; UIView alloc];
    let bar: id = msg![env; bar init];
    let bar_color: id = msg_class![env; UIColor colorWithRed:(0.43 as CGFloat)
                                                      green:(0.52 as CGFloat)
                                                       blue:(0.67 as CGFloat)
                                                      alpha:(1.0 as CGFloat)];
    () = msg![env; bar setBackgroundColor:bar_color];
    () = msg![env; bar setTag:TAG_BAR];
    () = msg![env; view addSubview:bar];
    release(env, bar);

    let gray: id = msg_class![env; UIColor grayColor];
    let bold: id = msg_class![env; UIFont boldSystemFontOfSize:(20.0 as CGFloat)];
    let small: id = msg_class![env; UIFont systemFontOfSize:(15.0 as CGFloat)];
    for (tag, text, font, color) in [
        (TAG_TITLE, "Music", bold, white),
        (TAG_HEADING, "No Music", bold, gray),
        (TAG_DETAIL, "There is no music on this device.", small, gray),
    ] {
        let label: id = msg_class![env; UILabel alloc];
        let label: id = msg![env; label init];
        let text = get_static_str(env, text);
        () = msg![env; label setText:text];
        () = msg![env; label setFont:font];
        () = msg![env; label setTextColor:color];
        () = msg![env; label setBackgroundColor:clear];
        () = msg![env; label setTextAlignment:UITextAlignmentCenter];
        () = msg![env; label setTag:tag];
        () = msg![env; view addSubview:label];
        release(env, label);
    }

    // The button that closes the picker: "Done" when several items can be
    // picked (there is no separate way to confirm a choice then), "Cancel"
    // otherwise.
    let allows_multiple = env.objc.borrow::<MPMediaPickerControllerHostObject>(this).allows_picking_multiple_items;
    let title = get_static_str(env, if allows_multiple { "Done" } else { "Cancel" });
    let button: id = msg_class![env; UIButton buttonWithType:UIButtonTypeRoundedRect];
    () = msg![env; button setTitle:title forState:UIControlStateNormal];
    () = msg![env; button setTag:TAG_CLOSE];
    let action = env.objc.register_host_selector("_touchHLE_close:".to_string(), &mut env.mem);
    () = msg![env; button addTarget:this
                             action:action
                   forControlEvents:UIControlEventTouchUpInside];
    () = msg![env; view addSubview:button];

    () = msg![env; view layoutSubviews];
    () = msg![env; this setView:view];
    release(env, view);
}

// Action of the closing button. Nothing can have been picked.
- (())_touchHLE_close:(id)_sender {
    let delegate = env.objc.borrow::<MPMediaPickerControllerHostObject>(this).delegate;
    if delegate == nil {
        return;
    }
    let sel = env.objc.register_host_selector("mediaPickerDidCancel:".to_string(), &mut env.mem);
    if env.objc.object_has_method(&env.mem, delegate, sel) {
        // The delegate normally dismisses the picker here, which can release
        // it.
        retain(env, this);
        () = msg![env; delegate mediaPickerDidCancel:this];
        release(env, this);
    }
}

@end

// The picker's root view. Its size changes when it is given the interface
// orientation, after it has been loaded, so its contents are placed here.
@implementation _touchHLE_MPMediaPickerView: UIView

- (())layoutSubviews {
    let bounds: CGRect = msg![env; this bounds];
    let (width, height) = (bounds.size.width, bounds.size.height);
    let bar_height: CGFloat = 44.0;
    let layout: [(NSInteger, CGRect); 5] = [
        (TAG_BAR, CGRect {
            origin: CGPoint { x: 0.0, y: 0.0 },
            size: CGSize { width, height: bar_height },
        }),
        (TAG_TITLE, CGRect {
            origin: CGPoint { x: 80.0, y: 0.0 },
            size: CGSize { width: (width - 160.0).max(0.0), height: bar_height },
        }),
        (TAG_CLOSE, CGRect {
            origin: CGPoint { x: width - 74.0, y: 7.0 },
            size: CGSize { width: 68.0, height: 30.0 },
        }),
        (TAG_HEADING, CGRect {
            origin: CGPoint { x: 0.0, y: ((height + bar_height) / 2.0 - 30.0).round() },
            size: CGSize { width, height: 26.0 },
        }),
        (TAG_DETAIL, CGRect {
            origin: CGPoint { x: 0.0, y: ((height + bar_height) / 2.0).round() },
            size: CGSize { width, height: 22.0 },
        }),
    ];
    for (tag, frame) in layout {
        let subview: id = msg![env; this viewWithTag:tag];
        if subview != nil {
            () = msg![env; subview setFrame:frame];
        }
    }
    // The button places its own label when asked.
    let button: id = msg![env; this viewWithTag:TAG_CLOSE];
    if button != nil {
        () = msg![env; button layoutSubviews];
    }
}

@end

};
