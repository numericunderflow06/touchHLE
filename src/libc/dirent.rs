/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `dirent.h`

use crate::abi::GuestFunction;
use crate::dyld::FunctionExports;
use crate::fs::GuestPath;
use crate::libc::errno::set_errno;
use crate::mem::{guest_size_of, ConstPtr, MutPtr, Ptr, SafeRead};
use crate::{export_c_func, impl_GuestRet_for_large_struct, Environment};
use std::collections::HashMap;

/// This is an opaque struct and doesn't necessary
/// corresponds the Apple's one
/// TODO: match struct sizes
#[allow(clippy::upper_case_acronyms)]
struct DIR {
    idx: usize,
    /// Store the directory path to determine d_type for entries
    path: String,
}
unsafe impl SafeRead for DIR {}

// While early iOS is 32-bit system, underling file system uses 64-bit inodes!
pub const MAXPATHLEN: usize = 1024;

// BSD d_type values (from sys/dirent.h)
// On Darwin/iOS, HFS+/APFS filesystems always populate d_type correctly
pub const DT_UNKNOWN: u8 = 0;
pub const DT_DIR: u8 = 4;
pub const DT_REG: u8 = 8;

#[allow(non_camel_case_types)]
#[derive(Debug)]
#[repr(C, packed)]
struct dirent {
    d_ino: u64,
    d_seekoff: u64,
    d_reclen: u16,
    d_namlen: u16,
    d_type: u8,
    d_name: [u8; MAXPATHLEN],
}
unsafe impl SafeRead for dirent {}
impl_GuestRet_for_large_struct!(dirent);

#[derive(Default)]
pub struct State {
    open_dirs: HashMap<MutPtr<DIR>, Vec<String>>,
    read_dirs: HashMap<MutPtr<DIR>, Vec<MutPtr<dirent>>>,
}
impl State {
    fn get_mut(env: &mut Environment) -> &mut Self {
        &mut env.libc_state.dirent
    }
}

fn opendir(env: &mut Environment, filename: ConstPtr<u8>) -> MutPtr<DIR> {
    // TODO: handle errno properly
    set_errno(env, 0);

    let path_string = env.mem.cstr_at_utf8(filename).unwrap().to_owned();
    log_dbg!("opendir: filename {}", path_string);
    // [DIAG-C1] Log directory open attempts for asset enumeration debugging
    log!("[DIAG-C1] opendir: path={}", path_string);
    let guest_path = GuestPath::new(&path_string);
    let is_dir = env.fs.is_dir(guest_path);
    if is_dir {
        let dir = env.mem.alloc_and_write(DIR { idx: 0, path: path_string.clone() });
        log_dbg!("opendir: new DIR ptr: {:?}", dir);
        let iter = env.fs.enumerate(guest_path).unwrap();
        let vec: Vec<String> = iter.map(|str| str.to_string()).collect();
        // [DIAG-C1] Log number of entries found
        log!("[DIAG-C1] opendir: path={} found {} entries", path_string, vec.len());
        assert!(!State::get_mut(env).open_dirs.contains_key(&dir));
        State::get_mut(env).open_dirs.insert(dir, vec);
        assert!(!State::get_mut(env).read_dirs.contains_key(&dir));
        State::get_mut(env).read_dirs.insert(dir, Vec::new());
        dir
    } else {
        Ptr::null()
    }
}

// TODO: return '.' and '..' entries as well
fn readdir(env: &mut Environment, dirp: MutPtr<DIR>) -> MutPtr<dirent> {
    // TODO: handle errno properly
    set_errno(env, 0);

    let mut dir = env.mem.read(dirp);
    let vec = env.libc_state.dirent.open_dirs.get(&dirp).unwrap();
    log_dbg!(
        "readdir: dirp {:?}, idx {}, entry '{:?}'",
        dirp,
        dir.idx,
        vec.get(dir.idx)
    );
    if let Some(str) = vec.get(dir.idx) {
        // Get the directory path to determine d_type for this entry
        let dir_path = dir.path.clone();
        dir.idx += 1;
        env.mem.write(dirp, dir);

        let len = str.len();

        // Determine d_type: check if entry is a directory or regular file
        // iOS/Darwin applications expect correct d_type values (DT_DIR=4, DT_REG=8)
        let full_path = format!("{}/{}", dir_path, str);
        let d_type = if env.fs.is_dir(GuestPath::new(&full_path)) {
            DT_DIR  // 4 = directory
        } else {
            DT_REG  // 8 = regular file
        };

        let mut dirent = dirent {
            d_ino: 0,
            d_seekoff: 0,
            d_reclen: 0,
            d_namlen: len as u16,
            d_type,
            d_name: [b'\0'; MAXPATHLEN],
        };
        dirent.d_name[..len].copy_from_slice(str.as_bytes());
        // [DIAG-C2] Log each directory entry with d_type for file type filtering debugging
        log!("[DIAG-C2] readdir: entry='{}' d_type={}", str, dirent.d_type);
        let res = env.mem.alloc_and_write(dirent);
        env.libc_state
            .dirent
            .read_dirs
            .get_mut(&dirp)
            .unwrap()
            .push(res);
        res
    } else {
        Ptr::null()
    }
}

fn closedir(env: &mut Environment, dirp: MutPtr<DIR>) -> i32 {
    // TODO: handle errno properly
    set_errno(env, 0);

    log_dbg!("closedir: dirp {:?}", dirp);
    // [DIAG-C3] Log directory close for complete enumeration tracing
    log!("[DIAG-C3] closedir: dirp={:?}", dirp);
    if let Some(vec) = env.libc_state.dirent.read_dirs.remove(&dirp) {
        for dirent in vec {
            env.mem.free(dirent.cast());
        }
    }
    if env.libc_state.dirent.open_dirs.remove(&dirp).is_some() {
        // this avoid double free if closedir() is called twice
        env.mem.free(dirp.cast());
    }
    0 // Success
}

fn scandir(
    env: &mut Environment,
    dirname: ConstPtr<u8>,
    list: MutPtr<MutPtr<MutPtr<dirent>>>,
    select: GuestFunction, // int (*select)(const struct dirent *)
    compar: GuestFunction, // int (*compar)(const struct dirent **, const struct dirent **)
) -> i32 {
    // TODO: handle errno properly
    set_errno(env, 0);

    assert!(select.to_ptr().is_null());
    assert!(compar.to_ptr().is_null());

    let dirp = opendir(env, dirname);
    if dirp.is_null() {
        // TODO: set errno
        return -1;
    }
    let mut next_dir_entry = readdir(env, dirp);
    let mut tmp_vec: Vec<MutPtr<dirent>> = vec![];
    while !next_dir_entry.is_null() {
        tmp_vec.push(next_dir_entry);
        next_dir_entry = readdir(env, dirp);
    }
    // we want to free dirp, but not entries themselves
    // so, we're not calling closedir() here
    env.libc_state.dirent.read_dirs.remove(&dirp);
    env.libc_state.dirent.open_dirs.remove(&dirp);
    env.mem.free(dirp.cast());

    let count: i32 = tmp_vec.len() as i32;
    let size = guest_size_of::<MutPtr<dirent>>() * count as u32;
    let mut output: MutPtr<MutPtr<dirent>> = env.mem.alloc(size).cast();
    env.mem.write(list, output);

    for entry in tmp_vec {
        env.mem.write(output, entry);
        output += 1;
    }

    count
}

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(opendir(_)),
    export_c_func!(readdir(_)),
    export_c_func!(closedir(_)),
    export_c_func!(scandir(_, _, _, _)),
];
