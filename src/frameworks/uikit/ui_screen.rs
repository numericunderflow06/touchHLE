/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIScreen`.

use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};
use crate::objc::{id, msg, objc_classes, ClassExports, TrivialHostObject};
use crate::window::DeviceOrientation;

#[derive(Default)]
pub struct State {
    main_screen: Option<id>,
}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

// For now this is a singleton (the only instance is returned by mainScreen),
// so there are hardcoded assumptions related to that.
@implementation UIScreen: NSObject

+ (id)mainScreen {
    if let Some(screen) = env.framework_state.uikit.ui_screen.main_screen {
        screen
    } else {
        let new = env.objc.alloc_static_object(
            this,
            Box::new(TrivialHostObject),
            &mut env.mem
        );
        env.framework_state.uikit.ui_screen.main_screen = Some(new);
        new
   }
}
- (id)retain { this }
- (())release {}
- (id)autorelease { this }

// TODO: more accessors

- (CGRect)bounds {
    // Return screen bounds based on current device orientation
    let (width, height) = match env.window().current_rotation() {
        DeviceOrientation::Portrait => (320.0, 480.0),
        DeviceOrientation::LandscapeLeft | DeviceOrientation::LandscapeRight => (480.0, 320.0),
    };
    CGRect {
        origin: CGPoint { x: 0.0, y: 0.0 },
        size: CGSize { width, height },
    }
}

- (CGRect)applicationFrame {
    let mut bounds: CGRect = msg![env; this bounds];
    const STATUS_BAR_HEIGHT: f32 = 20.0;
    if !env.framework_state.uikit.ui_application.status_bar_hidden {
        bounds.origin.y += STATUS_BAR_HEIGHT;
        bounds.size.height -= STATUS_BAR_HEIGHT;
    }
    bounds
}

@end

};
