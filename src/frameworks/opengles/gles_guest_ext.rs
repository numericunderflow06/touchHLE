/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! OpenGL ES extension stubs

use crate::dyld::{export_c_func, FunctionExports};
use crate::gles::gles11_raw::types::*;
use crate::mem::ConstPtr;
use crate::Environment;

/// glDiscardFramebufferEXT - hints that framebuffer attachments can be discarded
/// This is a performance hint and can be safely stubbed as a no-op
fn glDiscardFramebufferEXT(
    _env: &mut Environment,
    target: GLenum,
    num_attachments: GLsizei,
    _attachments: ConstPtr<GLenum>,
) {
    log!("glDiscardFramebufferEXT(target={:#x}, numAttachments={}) - stubbed as no-op", target, num_attachments);
}

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(glDiscardFramebufferEXT(_, _, _)),
];
