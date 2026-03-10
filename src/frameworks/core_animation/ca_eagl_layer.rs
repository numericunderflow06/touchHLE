/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `CAEAGLLayer`.

use super::ca_layer::CALayerHostObject;
use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};
use crate::frameworks::foundation::ns_string::from_rust_string;
use crate::objc::{autorelease, id, msg, msg_class, nil, objc_classes, Class, ClassExports};
use crate::window::DeviceOrientation;
use crate::Environment;

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation CAEAGLLayer: CALayer

// Class method for description - used when calling [CAEAGLLayer description]
+ (id)description {
    let ns_string = from_rust_string(env, "CAEAGLLayer".to_string());
    autorelease(env, ns_string)
}

// EAGLDrawable implementation (the only one)

- (id)drawableProperties {
    // FIXME: do we need to return an empty dictionary rather than nil?
    env.objc.borrow::<CALayerHostObject>(this).drawable_properties
}

- (())setDrawableProperties:(id)props { // NSDictionary<NSString*, id>*
    let props: id = msg![env; props copy];
    env.objc.borrow_mut::<CALayerHostObject>(this).drawable_properties = props;
}

// Override bounds to return landscape dimensions when the device is in
// landscape orientation. This simulates UIKit's view rotation which would
// resize the EAGLView's layer to landscape on a real device.
- (CGRect)bounds {
    let mut bounds = env.objc.borrow::<CALayerHostObject>(this).bounds;
    let orientation = env.window().current_rotation();
    if matches!(orientation, DeviceOrientation::LandscapeLeft | DeviceOrientation::LandscapeRight) {
        let (w, h) = (bounds.size.width, bounds.size.height);
        // If bounds are portrait (height > width), swap to landscape
        if h > w {
            bounds.size = CGSize { width: h, height: w };
        }
    }
    let (w, h) = (bounds.size.width, bounds.size.height);
    log!("[CAEAGLLayer] bounds = {:.0}x{:.0}", w, h);
    bounds
}

// NSObject method - required for debugging/logging (instance method)
- (id)description {
    let desc = format!("<CAEAGLLayer: {:?}>", this);
    let ns_string = from_rust_string(env, desc);
    autorelease(env, ns_string)
}

@end

};

/// If there is an opaque `CAEAGLLayer` that covers the entire screen, this
/// returns a pointer to it. Otherwise, it returns [nil].
///
/// To avoid a state management nightmare, we want to have an internal OpenGL ES
/// context for compositing, separate from any OpenGL ES contexts the app uses
/// for its rendering. When we have a `CAEAGLLayer` though, we need to transfer
/// a rendered frame from the app's context to the compositor's context, and
/// unfortunately the most practical way to do this is `glReadPixels()`, which
/// is highly inefficient. To make things efficient, then, we have a shortcut:
/// if the result of composition would be identical to the rendered frame, i.e.
/// there's a single full-screen layer, we skip transferring between contexts
/// and present it directly from the app's context. This function is used to
/// determine when that will happen.
pub fn find_fullscreen_eagl_layer(env: &mut Environment) -> id {
    if env.options.force_composition {
        return nil;
    }

    let windows = env.framework_state.uikit.ui_view.ui_window.windows.clone();
    // Assumes the windows in the list are ordered back-to-front.
    // TODO: this may not be correct once we support windowLevel.
    let Some(top_window) = windows
        .into_iter()
        .rev()
        .find(|&window| !msg![env; window isHidden])
    else {
        return nil;
    };

    let screen_bounds: CGRect = {
        let screen: id = msg_class![env; UIScreen mainScreen];
        msg![env; screen bounds]
    };

    let mut layer: id = msg![env; top_window layer];

    // Descend through the hierarchy, looking only at the last layer in each
    // list of children, since that should be the one on top.
    // TODO: this is not correct once we support zPosition.
    loop {
        assert!(layer != nil);

        let layer_host_obj: &CALayerHostObject = env.objc.borrow(layer);

        // [DIAG-C1] Code-focused diagnostic: Log layer properties for debugging fullscreen checks
        log!("[DIAG-C1] find_fullscreen_eagl_layer checking layer {:?}:", layer);
        log!("[DIAG-C1]   bounds.size={:?} vs screen={:?}",
             layer_host_obj.bounds.size, screen_bounds.size);
        log!("[DIAG-C1]   bounds.origin={:?} (expect (0,0))", layer_host_obj.bounds.origin);
        log!("[DIAG-C1]   anchor_point={:?} (expect (0.5,0.5))", layer_host_obj.anchor_point);
        log!("[DIAG-C1]   position={:?} (expect ({}, {}))",
             layer_host_obj.position,
             screen_bounds.size.width / 2.0,
             screen_bounds.size.height / 2.0);
        log!("[DIAG-C1]   hidden={}, opacity={}, identity_transform={}",
             layer_host_obj.hidden, layer_host_obj.opacity, layer_host_obj.affine_transform.is_identity());

        // This is stricter than it should be. In theory we should accumulate
        // the transforms and handle different anchor points etc, but real apps
        // probably only use this common case.
        if layer_host_obj.bounds.size != screen_bounds.size
            || layer_host_obj.bounds.origin != (CGPoint { x: 0.0, y: 0.0 })
            || layer_host_obj.anchor_point != (CGPoint { x: 0.5, y: 0.5 })
            || layer_host_obj.position
                != (CGPoint {
                    x: screen_bounds.size.width / 2.0,
                    y: screen_bounds.size.height / 2.0,
                })
            || layer_host_obj.hidden
            || layer_host_obj.opacity != 1.0
            // TODO: support affine transforms that result in a full-screen
            //       layer (typical example is 90° rotation).
            || !layer_host_obj.affine_transform.is_identity()
        {
            // [DIAG-C2] Code-focused diagnostic: Log which check failed
            log!("[DIAG-C2] Layer {:?} FAILED fullscreen check - falling back to slow path", layer);
            return nil;
        }

        // Find the last visible sublayer (skip hidden ones)
        if let Some(&next) = layer_host_obj.sublayers.iter().rev().find(|&&l| {
            !env.objc.borrow::<CALayerHostObject>(l).hidden
        }) {
            layer = next;
        } else {
            break;
        }
    }

    if !env.objc.borrow::<CALayerHostObject>(layer).opaque {
        log!("[DIAG-C2] Layer {:?} is not opaque - falling back to slow path", layer);
        return nil;
    }

    let ca_eagl_layer_class: Class = msg_class![env; CAEAGLLayer class];
    if !msg![env; layer isKindOfClass:ca_eagl_layer_class] {
        log!("[DIAG-C2] Layer {:?} is not CAEAGLLayer - falling back to slow path", layer);
        return nil;
    }

    // [DIAG-C2] Code-focused diagnostic: Layer passed all checks
    log!("[DIAG-C2] Layer {:?} PASSED all fullscreen checks - using fast path", layer);
    layer
}

/// For use by `EAGLContext` when presenting to a `CAEAGLLayer`:
/// [std::mem::take]s the buffer used to hold the pixels. It should be passed
/// back to [present_pixels] once it has been filled.
pub fn get_pixels_vec_for_presenting(env: &mut Environment, layer: id) -> Vec<u8> {
    env.objc
        .borrow_mut::<CALayerHostObject>(layer)
        .presented_pixels
        .take()
        .map(|(vec, _width, _height)| vec)
        .unwrap_or_default()
}

/// For use by `EAGLContext` when presenting to a `CAEAGLLayer`: provide the new
/// frame rendered by the app, so it can be used when compositing. The buffer
/// should have been obtained with [get_pixels_vec_for_presenting] before
/// filling. The data must be in RGBA8 format.
pub fn present_pixels(env: &mut Environment, layer: id, pixels: Vec<u8>, width: u32, height: u32) {
    let host_obj = env.objc.borrow_mut::<CALayerHostObject>(layer);
    host_obj.presented_pixels = Some((pixels, width, height));
    host_obj.gles_texture_is_up_to_date = false;
}
