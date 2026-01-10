/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIScreen`.

use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};
use crate::objc::{id, msg, objc_classes, ClassExports, TrivialHostObject};

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
    // TODO: once rotation is supported, this must change with the rotation!
    let bounds = CGRect {
        origin: CGPoint { x: 0.0, y: 0.0 },
        size: CGSize { width: 320.0, height: 480.0 },
    };
    // Copy to local vars to avoid packed struct field reference issues
    let (w, h) = (bounds.size.width, bounds.size.height);
    log!("[DIAG-DEV] UIScreen.bounds queried, returning: {}x{}", w, h);
    bounds
}

- (CGRect)applicationFrame {
    let mut bounds: CGRect = msg![env; this bounds];
    const STATUS_BAR_HEIGHT: f32 = 20.0;
    if !env.framework_state.uikit.ui_application.status_bar_hidden {
        bounds.origin.y += STATUS_BAR_HEIGHT;
        bounds.size.height -= STATUS_BAR_HEIGHT;
    }
    // Copy to local vars to avoid packed struct field reference issues
    let (w, h, x, y) = (bounds.size.width, bounds.size.height, bounds.origin.x, bounds.origin.y);
    log!("[DIAG-DEV] UIScreen.applicationFrame queried, returning: {}x{} at ({},{})", w, h, x, y);
    bounds
}

@end

};
