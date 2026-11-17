/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIAlertView`.
//!
//! The alert is built out of ordinary views: a dimmed layer over the whole
//! screen that swallows touches, and on it a box with the title, the message
//! and one `UIButton` per button title. Like the real thing it appears in the
//! orientation of the status bar, stays up until a button is tapped (or it is
//! dismissed in code), and reports to its delegate.

use crate::frameworks::core_graphics::cg_affine_transform::CGAffineTransform;
use crate::frameworks::core_graphics::{CGFloat, CGPoint, CGRect, CGSize};
use crate::frameworks::foundation::{ns_string, NSInteger};
use crate::frameworks::uikit::ui_font::UITextAlignmentCenter;
use crate::frameworks::uikit::ui_view::ui_control::ui_button::UIButtonTypeRoundedRect;
use crate::frameworks::uikit::ui_view::ui_control::{
    UIControlEventTouchUpInside, UIControlStateNormal,
};
use crate::objc::{
    id, impl_HostObject_with_superclass, msg, msg_class, msg_super, nil, objc_classes, release,
    retain, ClassExports, NSZonePtr,
};
use crate::window::DeviceOrientation;
use crate::Environment;

pub struct UIAlertViewHostObject {
    superclass: super::UIViewHostObject,
    /// `NSString*`, retained.
    title: id,
    /// `NSString*`, retained.
    message: id,
    /// `id<UIAlertViewDelegate>`, not retained.
    delegate: id,
    /// `NSString*`, retained.
    button_titles: Vec<id>,
    cancel_button_index: NSInteger,
    /// The full-screen view carrying the alert while it is shown.
    container: id,
}
impl_HostObject_with_superclass!(UIAlertViewHostObject);
impl Default for UIAlertViewHostObject {
    fn default() -> Self {
        UIAlertViewHostObject {
            superclass: Default::default(),
            title: nil,
            message: nil,
            delegate: nil,
            button_titles: Vec::new(),
            cancel_button_index: -1,
            container: nil,
        }
    }
}

fn add_button(env: &mut Environment, alert: id, title: id) -> NSInteger {
    retain(env, title);
    let host_object = env.objc.borrow_mut::<UIAlertViewHostObject>(alert);
    host_object.button_titles.push(title);
    (host_object.button_titles.len() - 1) as NSInteger
}

/// Send `[delegate <selector>alert]`-style messages only if the delegate
/// implements them: all `UIAlertViewDelegate` methods are optional.
fn delegate_responds(env: &mut Environment, delegate: id, selector: &str) -> bool {
    if delegate == nil {
        return false;
    }
    let sel = env
        .objc
        .register_host_selector(selector.to_string(), &mut env.mem);
    env.objc.object_has_method(&env.mem, delegate, sel)
}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation UIAlertView: UIView

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::<UIAlertViewHostObject>::default();
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithTitle:(id)title // NSString*
            message:(id)message // NSString*
           delegate:(id)delegate
  cancelButtonTitle:(id)cancel_button_title // NSString*
  otherButtonTitles:(id)first_other_button_title, ...args { // NSString*, nil-terminated
    let this: id = msg_super![env; this init];

    retain(env, title);
    retain(env, message);
    {
        let host_object = env.objc.borrow_mut::<UIAlertViewHostObject>(this);
        host_object.title = title;
        host_object.message = message;
        host_object.delegate = delegate;
    }
    if cancel_button_title != nil {
        let index = add_button(env, this, cancel_button_title);
        env.objc.borrow_mut::<UIAlertViewHostObject>(this).cancel_button_index = index;
    }
    if first_other_button_title != nil {
        add_button(env, this, first_other_button_title);
        let mut varargs = args.start();
        loop {
            let next_title: id = varargs.next(env);
            if next_title == nil {
                break;
            }
            add_button(env, this, next_title);
        }
    }

    this
}

- (())dealloc {
    let UIAlertViewHostObject {
        title,
        message,
        ref button_titles,
        ..
    } = *env.objc.borrow::<UIAlertViewHostObject>(this);
    let button_titles = button_titles.clone();
    release(env, title);
    release(env, message);
    for button_title in button_titles {
        release(env, button_title);
    }
    msg_super![env; this dealloc]
}

- (id)delegate {
    env.objc.borrow::<UIAlertViewHostObject>(this).delegate
}
- (())setDelegate:(id)delegate {
    env.objc.borrow_mut::<UIAlertViewHostObject>(this).delegate = delegate;
}

- (id)title {
    env.objc.borrow::<UIAlertViewHostObject>(this).title
}
- (())setTitle:(id)title { // NSString*
    retain(env, title);
    let old = std::mem::replace(
        &mut env.objc.borrow_mut::<UIAlertViewHostObject>(this).title,
        title
    );
    release(env, old);
}
- (id)message {
    env.objc.borrow::<UIAlertViewHostObject>(this).message
}
- (())setMessage:(id)message { // NSString*
    retain(env, message);
    let old = std::mem::replace(
        &mut env.objc.borrow_mut::<UIAlertViewHostObject>(this).message,
        message
    );
    release(env, old);
}

- (NSInteger)addButtonWithTitle:(id)title { // NSString*
    add_button(env, this, title)
}
- (NSInteger)numberOfButtons {
    env.objc.borrow::<UIAlertViewHostObject>(this).button_titles.len() as NSInteger
}
- (id)buttonTitleAtIndex:(NSInteger)index {
    env.objc.borrow::<UIAlertViewHostObject>(this).button_titles[index as usize]
}
- (NSInteger)cancelButtonIndex {
    env.objc.borrow::<UIAlertViewHostObject>(this).cancel_button_index
}
- (())setCancelButtonIndex:(NSInteger)index {
    env.objc.borrow_mut::<UIAlertViewHostObject>(this).cancel_button_index = index;
}
- (NSInteger)firstOtherButtonIndex {
    let host_object = env.objc.borrow::<UIAlertViewHostObject>(this);
    let count = host_object.button_titles.len() as NSInteger;
    let first = if host_object.cancel_button_index == 0 { 1 } else { 0 };
    if first < count { first } else { -1 }
}
- (bool)isVisible {
    env.objc.borrow::<UIAlertViewHostObject>(this).container != nil
}

- (())show {
    if env.objc.borrow::<UIAlertViewHostObject>(this).container != nil {
        return;
    }
    let application: id = msg_class![env; UIApplication sharedApplication];
    let window: id = msg![env; application keyWindow];
    if window == nil {
        log!("Warning: [(UIAlertView*){:?} show] without a key window, not showing it.", this);
        return;
    }

    let &UIAlertViewHostObject {
        title,
        message,
        delegate,
        ref button_titles,
        cancel_button_index,
        ..
    } = env.objc.borrow::<UIAlertViewHostObject>(this);
    let button_titles = button_titles.clone();
    log_dbg!("[(UIAlertView*){:?} show]: {} button(s)", this, button_titles.len());

    if delegate_responds(env, delegate, "willPresentAlertView:") {
        () = msg![env; delegate willPresentAlertView:this];
    }

    // The dimmed layer covers the screen in the status bar's orientation,
    // so the alert reads upright whichever way the app has rotated itself.
    let window_frame: CGRect = msg![env; window frame];
    let (transform, sideways) = match env.window().current_rotation() {
        DeviceOrientation::Portrait => (CGAffineTransform::make_rotation(0.0), false),
        DeviceOrientation::PortraitUpsideDown => {
            (CGAffineTransform::make_rotation(std::f32::consts::PI), false)
        }
        DeviceOrientation::LandscapeLeft => {
            (CGAffineTransform::make_rotation(std::f32::consts::FRAC_PI_2), true)
        }
        DeviceOrientation::LandscapeRight => {
            (CGAffineTransform::make_rotation(-std::f32::consts::FRAC_PI_2), true)
        }
    };
    let screen_size = if sideways {
        CGSize { width: window_frame.size.height, height: window_frame.size.width }
    } else {
        window_frame.size
    };

    let container: id = msg_class![env; UIView alloc];
    let container: id = msg![env; container initWithFrame:(CGRect {
        origin: CGPoint { x: 0.0, y: 0.0 },
        size: screen_size,
    })];
    let dim: id = msg_class![env; UIColor colorWithWhite:(0.0 as CGFloat) alpha:(0.5 as CGFloat)];
    () = msg![env; container setBackgroundColor:dim];
    () = msg![env; container setTransform:transform];
    () = msg![env; container setCenter:(CGPoint {
        x: window_frame.size.width / 2.0,
        y: window_frame.size.height / 2.0,
    })];

    // Lay out the box: title, message, then the buttons (two side by side,
    // any other number stacked).
    let margin: CGFloat = 12.0;
    let box_width: CGFloat = 284.0;
    let text_width = box_width - margin * 2.0;
    let title_font: id = msg_class![env; UIFont boldSystemFontOfSize:(17.0 as CGFloat)];
    let message_font: id = msg_class![env; UIFont systemFontOfSize:(15.0 as CGFloat)];
    let limit = CGSize { width: text_width, height: 1000.0 };
    let title_height: CGFloat = if title == nil {
        0.0
    } else {
        let size: CGSize = msg![env; title sizeWithFont:title_font constrainedToSize:limit];
        size.height.ceil()
    };
    let message_height: CGFloat = if message == nil {
        0.0
    } else {
        let size: CGSize = msg![env; message sizeWithFont:message_font constrainedToSize:limit];
        size.height.ceil()
    };
    let button_height: CGFloat = 36.0;
    let side_by_side = button_titles.len() == 2;
    let button_rows = if side_by_side { 1 } else { button_titles.len() };
    let mut y = margin;
    let title_y = y;
    if title != nil {
        y += title_height + margin * 0.75;
    }
    let message_y = y;
    if message != nil {
        y += message_height + margin;
    }
    let buttons_y = y;
    y += button_rows as CGFloat * (button_height + margin * 0.5);
    let box_height = (y + margin * 0.5).min(screen_size.height - 8.0);

    let panel: id = msg_class![env; UIView alloc];
    let panel: id = msg![env; panel initWithFrame:(CGRect {
        origin: CGPoint {
            x: ((screen_size.width - box_width) / 2.0).round(),
            y: ((screen_size.height - box_height) / 2.0).round(),
        },
        size: CGSize { width: box_width, height: box_height },
    })];
    let panel_color: id = msg_class![env; UIColor colorWithRed:(0.08 as CGFloat)
                                                        green:(0.14 as CGFloat)
                                                         blue:(0.32 as CGFloat)
                                                        alpha:(0.95 as CGFloat)];
    () = msg![env; panel setBackgroundColor:panel_color];
    () = msg![env; container addSubview:panel];
    release(env, panel);

    let white: id = msg_class![env; UIColor whiteColor];
    let clear: id = msg_class![env; UIColor clearColor];
    for (text, font, text_y, height) in [
        (title, title_font, title_y, title_height),
        (message, message_font, message_y, message_height),
    ] {
        if text == nil {
            continue;
        }
        let label: id = msg_class![env; UILabel alloc];
        let label: id = msg![env; label initWithFrame:(CGRect {
            origin: CGPoint { x: margin, y: text_y },
            size: CGSize { width: text_width, height },
        })];
        () = msg![env; label setText:text];
        () = msg![env; label setFont:font];
        () = msg![env; label setTextColor:white];
        () = msg![env; label setBackgroundColor:clear];
        () = msg![env; label setTextAlignment:UITextAlignmentCenter];
        () = msg![env; label setNumberOfLines:(0 as NSInteger)];
        () = msg![env; panel addSubview:label];
        release(env, label);
    }

    let action = env
        .objc
        .register_host_selector("_touchHLE_buttonTapped:".to_string(), &mut env.mem);
    // Where each button goes. Side by side they are in the order of their
    // indices (the cancel button, normally the first, on the left). Stacked,
    // the cancel button is at the bottom whatever its index.
    let mut order: Vec<usize> = (0..button_titles.len()).collect();
    if !side_by_side {
        if let Some(position) = order
            .iter()
            .position(|&index| index as NSInteger == cancel_button_index)
        {
            let cancel = order.remove(position);
            order.push(cancel);
        }
    }
    for (place, &index) in order.iter().enumerate() {
        let button_title = button_titles[index];
        let frame = if side_by_side {
            let width = (text_width - margin) / 2.0;
            CGRect {
                origin: CGPoint { x: margin + place as CGFloat * (width + margin), y: buttons_y },
                size: CGSize { width, height: button_height },
            }
        } else {
            CGRect {
                origin: CGPoint {
                    x: margin,
                    y: buttons_y + place as CGFloat * (button_height + margin * 0.5),
                },
                size: CGSize { width: text_width, height: button_height },
            }
        };
        let button: id = msg_class![env; UIButton buttonWithType:UIButtonTypeRoundedRect];
        () = msg![env; button setTitle:button_title forState:UIControlStateNormal];
        () = msg![env; button setFrame:frame];
        () = msg![env; button layoutSubviews];
        () = msg![env; button setTag:(index as NSInteger)];
        () = msg![env; button addTarget:this
                                 action:action
                       forControlEvents:UIControlEventTouchUpInside];
        () = msg![env; panel addSubview:button];
    }

    () = msg![env; window addSubview:container];
    release(env, container);
    env.objc.borrow_mut::<UIAlertViewHostObject>(this).container = container;
    // A visible alert keeps itself alive: apps routinely release (or
    // autorelease) the alert right after showing it.
    retain(env, this);

    if delegate_responds(env, delegate, "didPresentAlertView:") {
        () = msg![env; delegate didPresentAlertView:this];
    }
}

// Action of the alert's buttons.
- (())_touchHLE_buttonTapped:(id)button { // UIButton*
    let index: NSInteger = msg![env; button tag];
    let delegate = env.objc.borrow::<UIAlertViewHostObject>(this).delegate;
    if delegate_responds(env, delegate, "alertView:clickedButtonAtIndex:") {
        () = msg![env; delegate alertView:this clickedButtonAtIndex:index];
    }
    () = msg![env; this dismissWithClickedButtonIndex:index animated:true];
}

- (())dismissWithClickedButtonIndex:(NSInteger)index
                           animated:(bool)_animated {
    let &UIAlertViewHostObject { container, delegate, .. } = env.objc.borrow(this);
    if container == nil {
        return;
    }
    if delegate_responds(env, delegate, "alertView:willDismissWithButtonIndex:") {
        () = msg![env; delegate alertView:this willDismissWithButtonIndex:index];
    }
    env.objc.borrow_mut::<UIAlertViewHostObject>(this).container = nil;
    () = msg![env; container removeFromSuperview];
    let delegate = env.objc.borrow::<UIAlertViewHostObject>(this).delegate;
    if delegate_responds(env, delegate, "alertView:didDismissWithButtonIndex:") {
        () = msg![env; delegate alertView:this didDismissWithButtonIndex:index];
    }
    // Balances the retain in `show`.
    release(env, this);
}

@end

};
