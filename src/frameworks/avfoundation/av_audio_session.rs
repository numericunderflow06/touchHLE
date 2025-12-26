/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! AVAudioSession stub implementation

use crate::dyld::{ConstantExports, HostConstant};
use crate::mem::MutPtr;
use crate::objc::{id, msg, msg_class, nil, objc_classes, retain, ClassExports, HostObject, NSZonePtr};

pub const CONSTANTS: ConstantExports = &[
    ("_AVAudioSessionCategoryAmbient", HostConstant::NSString("AVAudioSessionCategoryAmbient")),
    ("_AVAudioSessionCategoryPlayback", HostConstant::NSString("AVAudioSessionCategoryPlayback")),
    ("_AVAudioSessionCategorySoloAmbient", HostConstant::NSString("AVAudioSessionCategorySoloAmbient")),
    ("_AVAudioSessionCategoryPlayAndRecord", HostConstant::NSString("AVAudioSessionCategoryPlayAndRecord")),
];

struct AVAudioSessionHostObject {
    category: id,
    delegate: id,
}
impl HostObject for AVAudioSessionHostObject {}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation AVAudioSession: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::new(AVAudioSessionHostObject {
        category: nil,
        delegate: nil,
    });
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

+ (id)sharedInstance {
    // Return a singleton instance
    // For simplicity, we create a new instance each time (the app should cache it)
    // A proper implementation would store this in framework state
    log!("AVAudioSession sharedInstance called");
    let instance: id = msg_class![env; AVAudioSession alloc];
    let instance: id = msg![env; instance init];
    // Note: In a real implementation, this would be retained and stored as a singleton
    instance
}

- (id)init {
    this
}

- (bool)setCategory:(id)category
               error:(MutPtr<id>)outError {
    log!("AVAudioSession setCategory:{:?} error:{:?} - stubbed", category, outError);
    retain(env, category);
    let host = env.objc.borrow_mut::<AVAudioSessionHostObject>(this);
    host.category = category;
    // No error
    if !outError.is_null() {
        env.mem.write(outError, nil);
    }
    true
}

- (bool)setActive:(bool)active
            error:(MutPtr<id>)outError {
    log!("AVAudioSession setActive:{} error:{:?} - stubbed", active, outError);
    // No error
    if !outError.is_null() {
        env.mem.write(outError, nil);
    }
    true
}

- (bool)setActive:(bool)active
      withOptions:(u32)options
            error:(MutPtr<id>)outError {
    log!("AVAudioSession setActive:{} withOptions:{} error:{:?} - stubbed", active, options, outError);
    // No error
    if !outError.is_null() {
        env.mem.write(outError, nil);
    }
    true
}

- (id)category {
    env.objc.borrow::<AVAudioSessionHostObject>(this).category
}

- (())setDelegate:(id)delegate {
    log!("AVAudioSession setDelegate:{:?} - stubbed", delegate);
    env.objc.borrow_mut::<AVAudioSessionHostObject>(this).delegate = delegate;
}

- (id)delegate {
    env.objc.borrow::<AVAudioSessionHostObject>(this).delegate
}

- (f64)currentHardwareSampleRate {
    log!("AVAudioSession currentHardwareSampleRate - returning 44100.0");
    44100.0
}

- (i32)currentHardwareInputNumberOfChannels {
    log!("AVAudioSession currentHardwareInputNumberOfChannels - returning 0");
    0
}

- (i32)currentHardwareOutputNumberOfChannels {
    log!("AVAudioSession currentHardwareOutputNumberOfChannels - returning 2");
    2
}

- (bool)inputIsAvailable {
    log!("AVAudioSession inputIsAvailable - returning false");
    false
}

- (f32)preferredHardwareSampleRate {
    log!("AVAudioSession preferredHardwareSampleRate - returning 44100.0");
    44100.0
}

- (bool)setPreferredHardwareSampleRate:(f64)sampleRate
                                 error:(MutPtr<id>)outError {
    log!("AVAudioSession setPreferredHardwareSampleRate:{} error:{:?} - stubbed", sampleRate, outError);
    if !outError.is_null() {
        env.mem.write(outError, nil);
    }
    true
}

@end

};
