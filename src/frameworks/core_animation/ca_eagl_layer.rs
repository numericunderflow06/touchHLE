/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `CAEAGLLayer`.

use super::ca_layer::CALayerHostObject;
use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};
use crate::objc::{id, msg, msg_class, nil, objc_classes, Class, ClassExports};
use crate::Environment;

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation CAEAGLLayer: CALayer

- (id)drawableProperties {
    env.objc.borrow::<CALayerHostObject>(this).drawable_properties
}

- (())setDrawableProperties:(id)props {
    let props: id = msg![env; props copy];
    env.objc.borrow_mut::<CALayerHostObject>(this).drawable_properties = props;
}

@end

};

/// Check if a layer matches fullscreen requirements
fn layer_matches_fullscreen(layer_host_obj: &CALayerHostObject, screen_bounds: &CGRect) -> bool {
    // Check bounds - either exact match or rotated match
    let bounds_match = layer_host_obj.bounds.size == screen_bounds.size;
    let rotated_bounds = CGSize {
        width: screen_bounds.size.height,
        height: screen_bounds.size.width
    };
    let bounds_match_rotated = layer_host_obj.bounds.size == rotated_bounds;

    if !(bounds_match || bounds_match_rotated) {
        return false;
    }

    // Position should be center of layer's own bounds
    let expected_position = CGPoint {
        x: layer_host_obj.bounds.size.width / 2.0,
        y: layer_host_obj.bounds.size.height / 2.0,
    };

    layer_host_obj.bounds.origin == (CGPoint { x: 0.0, y: 0.0 })
        && layer_host_obj.anchor_point == (CGPoint { x: 0.5, y: 0.5 })
        && layer_host_obj.position == expected_position
        && !layer_host_obj.hidden
        && layer_host_obj.opacity == 1.0
        && layer_host_obj.affine_transform.is_identity()
}

pub fn find_fullscreen_eagl_layer(env: &mut Environment) -> id {
    if env.options.force_composition {
        return nil;
    }

    let windows = env.framework_state.uikit.ui_view.ui_window.windows.clone();
    
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

    let ca_eagl_layer_class: Class = msg_class![env; CAEAGLLayer class];

    // Recursive function to find fullscreen CAEAGLLayer
    fn find_in_layer(env: &mut Environment, layer: id, screen_bounds: &CGRect, ca_eagl_layer_class: Class) -> id {
        if layer == nil {
            return nil;
        }

        let layer_host_obj: &CALayerHostObject = env.objc.borrow(layer);

        // Check if this layer could be fullscreen
        if !layer_matches_fullscreen(layer_host_obj, screen_bounds) {
            return nil;
        }

        // Get sublayers
        let sublayers = layer_host_obj.sublayers.clone();

        // If no sublayers, check if this is an opaque CAEAGLLayer
        if sublayers.is_empty() {
            if !env.objc.borrow::<CALayerHostObject>(layer).opaque {
                return nil;
            }
            if msg![env; layer isKindOfClass:ca_eagl_layer_class] {
                return layer;
            }
            return nil;
        }

        // Check sublayers from back to front (last to first)
        // Skip layers with 0x0 bounds (overlays like activity indicators)
        for &sublayer in sublayers.iter().rev() {
            let sub_host_obj: &CALayerHostObject = env.objc.borrow(sublayer);
            
            // Skip empty layers (like activity indicator overlays)
            if sub_host_obj.bounds.size.width == 0.0 && sub_host_obj.bounds.size.height == 0.0 {
                continue;
            }

            let result = find_in_layer(env, sublayer, screen_bounds, ca_eagl_layer_class);
            if result != nil {
                return result;
            }
        }

        nil
    }

    let layer: id = msg![env; top_window layer];
    find_in_layer(env, layer, &screen_bounds, ca_eagl_layer_class)
}

pub fn get_pixels_vec_for_presenting(env: &mut Environment, layer: id) -> Vec<u8> {
    env.objc
        .borrow_mut::<CALayerHostObject>(layer)
        .presented_pixels
        .take()
        .map(|(vec, _width, _height)| vec)
        .unwrap_or_default()
}

pub fn present_pixels(env: &mut Environment, layer: id, pixels: Vec<u8>, width: u32, height: u32) {
    let host_obj = env.objc.borrow_mut::<CALayerHostObject>(layer);
    host_obj.presented_pixels = Some((pixels, width, height));
    host_obj.gles_texture_is_up_to_date = false;
}
