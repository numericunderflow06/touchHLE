/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! MapKit.framework stubs
//!
//! MapKit provides map-related functionality. Most games don't actually need
//! maps to function - they may just link against it for ads or analytics SDKs.

use crate::dyld::{ConstantExports, HostConstant, HostDylib};
use crate::objc::{id, objc_classes, ClassExports, TrivialHostObject};

pub const DYLIB: HostDylib = HostDylib {
    path: "/System/Library/Frameworks/MapKit.framework/MapKit",
    aliases: &[],
    class_exports: &[CLASSES],
    constant_exports: &[CONSTANTS],
    function_exports: &[],
};

const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation MKMapView: UIView

+ (id)alloc {
    log!("Warning: MKMapView alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithFrame:(crate::frameworks::core_graphics::CGRect)_frame {
    log!("Warning: MKMapView initWithFrame: - stubbed");
    this
}

- (())setDelegate:(id)_delegate {
    log!("Warning: MKMapView setDelegate: - stubbed");
}

- (())setShowsUserLocation:(bool)_shows {
    log!("Warning: MKMapView setShowsUserLocation: - stubbed");
}

- (())setMapType:(i32)_map_type {
    log!("Warning: MKMapView setMapType: - stubbed");
}

- (())setScrollEnabled:(bool)_enabled {
    log!("Warning: MKMapView setScrollEnabled: - stubbed");
}

- (())setZoomEnabled:(bool)_enabled {
    log!("Warning: MKMapView setZoomEnabled: - stubbed");
}

@end

@implementation MKAnnotationView: UIView

+ (id)alloc {
    log!("Warning: MKAnnotationView alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithAnnotation:(id)_annotation reuseIdentifier:(id)_identifier {
    log!("Warning: MKAnnotationView initWithAnnotation:reuseIdentifier: - stubbed");
    this
}

@end

@implementation MKPinAnnotationView: MKAnnotationView

+ (id)alloc {
    log!("Warning: MKPinAnnotationView alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

@end

@implementation MKUserLocation: NSObject
// User's location - stubbed
@end

@implementation MKPlacemark: NSObject

+ (id)alloc {
    log!("Warning: MKPlacemark alloc - stubbed");
    let host_object = Box::new(TrivialHostObject);
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)init {
    log!("Warning: MKPlacemark init - stubbed");
    this
}

@end

};

const CONSTANTS: ConstantExports = &[
    // Error domain
    ("_MKErrorDomain", HostConstant::NSString("MKErrorDomain")),
];
