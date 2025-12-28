/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! libsqlite3 stubs
//!
//! SQLite is commonly used by iOS apps for local storage. This module provides
//! stub implementations that return appropriate error codes to allow apps to
//! handle the "no database" case gracefully.

use crate::dyld::{export_c_func, ConstantExports, FunctionExports, HostConstant, HostDylib};
use crate::mem::{ConstPtr, MutPtr, ConstVoidPtr, MutVoidPtr};
use crate::Environment;

pub const DYLIB: HostDylib = HostDylib {
    path: "/usr/lib/libsqlite3.dylib",
    aliases: &[],
    class_exports: &[],
    constant_exports: &[CONSTANTS],
    function_exports: &[FUNCTIONS],
};

// SQLite result codes
const SQLITE_OK: i32 = 0;
const SQLITE_ERROR: i32 = 1;
const SQLITE_CANTOPEN: i32 = 14;
const SQLITE_MISUSE: i32 = 21;

// Opaque pointer types
type sqlite3 = MutVoidPtr;
type sqlite3_stmt = MutVoidPtr;

fn sqlite3_open(
    _env: &mut Environment,
    filename: ConstPtr<u8>,
    ppdb: MutPtr<sqlite3>,
) -> i32 {
    log!("Warning: sqlite3_open({:?}) - stubbed, returning SQLITE_CANTOPEN", filename);
    // Write null to the database handle pointer
    if !ppdb.is_null() {
        _env.mem.write(ppdb, MutVoidPtr::null());
    }
    SQLITE_CANTOPEN
}

fn sqlite3_open_v2(
    _env: &mut Environment,
    filename: ConstPtr<u8>,
    ppdb: MutPtr<sqlite3>,
    _flags: i32,
    _z_vfs: ConstPtr<u8>,
) -> i32 {
    log!("Warning: sqlite3_open_v2({:?}) - stubbed, returning SQLITE_CANTOPEN", filename);
    if !ppdb.is_null() {
        _env.mem.write(ppdb, MutVoidPtr::null());
    }
    SQLITE_CANTOPEN
}

fn sqlite3_close(_env: &mut Environment, db: sqlite3) -> i32 {
    log!("Warning: sqlite3_close({:?}) - stubbed", db);
    SQLITE_OK
}

fn sqlite3_close_v2(_env: &mut Environment, db: sqlite3) -> i32 {
    log!("Warning: sqlite3_close_v2({:?}) - stubbed", db);
    SQLITE_OK
}

fn sqlite3_exec(
    _env: &mut Environment,
    db: sqlite3,
    _sql: ConstPtr<u8>,
    _callback: ConstVoidPtr,
    _callback_arg: MutVoidPtr,
    _errmsg: MutPtr<MutPtr<u8>>,
) -> i32 {
    log!("Warning: sqlite3_exec({:?}) - stubbed, returning SQLITE_MISUSE", db);
    SQLITE_MISUSE
}

fn sqlite3_prepare_v2(
    _env: &mut Environment,
    db: sqlite3,
    _sql: ConstPtr<u8>,
    _nbyte: i32,
    ppstmt: MutPtr<sqlite3_stmt>,
    _pztail: MutPtr<ConstPtr<u8>>,
) -> i32 {
    log!("Warning: sqlite3_prepare_v2({:?}) - stubbed, returning SQLITE_MISUSE", db);
    if !ppstmt.is_null() {
        _env.mem.write(ppstmt, MutVoidPtr::null());
    }
    SQLITE_MISUSE
}

fn sqlite3_step(_env: &mut Environment, stmt: sqlite3_stmt) -> i32 {
    log!("Warning: sqlite3_step({:?}) - stubbed, returning SQLITE_MISUSE", stmt);
    SQLITE_MISUSE
}

fn sqlite3_finalize(_env: &mut Environment, stmt: sqlite3_stmt) -> i32 {
    log!("Warning: sqlite3_finalize({:?}) - stubbed", stmt);
    SQLITE_OK
}

fn sqlite3_reset(_env: &mut Environment, stmt: sqlite3_stmt) -> i32 {
    log!("Warning: sqlite3_reset({:?}) - stubbed", stmt);
    SQLITE_OK
}

fn sqlite3_errmsg(_env: &mut Environment, _db: sqlite3) -> ConstPtr<u8> {
    // Return a static error message
    log!("Warning: sqlite3_errmsg - stubbed");
    ConstPtr::null()
}

fn sqlite3_errcode(_env: &mut Environment, _db: sqlite3) -> i32 {
    log!("Warning: sqlite3_errcode - stubbed");
    SQLITE_MISUSE
}

fn sqlite3_last_insert_rowid(_env: &mut Environment, _db: sqlite3) -> i64 {
    log!("Warning: sqlite3_last_insert_rowid - stubbed");
    0
}

fn sqlite3_changes(_env: &mut Environment, _db: sqlite3) -> i32 {
    log!("Warning: sqlite3_changes - stubbed");
    0
}

fn sqlite3_bind_int(_env: &mut Environment, _stmt: sqlite3_stmt, _idx: i32, _value: i32) -> i32 {
    log!("Warning: sqlite3_bind_int - stubbed");
    SQLITE_MISUSE
}

fn sqlite3_bind_int64(_env: &mut Environment, _stmt: sqlite3_stmt, _idx: i32, _value: i64) -> i32 {
    log!("Warning: sqlite3_bind_int64 - stubbed");
    SQLITE_MISUSE
}

fn sqlite3_bind_double(_env: &mut Environment, _stmt: sqlite3_stmt, _idx: i32, _value: f64) -> i32 {
    log!("Warning: sqlite3_bind_double - stubbed");
    SQLITE_MISUSE
}

fn sqlite3_bind_text(
    _env: &mut Environment,
    _stmt: sqlite3_stmt,
    _idx: i32,
    _text: ConstPtr<u8>,
    _nbyte: i32,
    _destructor: ConstVoidPtr,
) -> i32 {
    log!("Warning: sqlite3_bind_text - stubbed");
    SQLITE_MISUSE
}

fn sqlite3_bind_blob(
    _env: &mut Environment,
    _stmt: sqlite3_stmt,
    _idx: i32,
    _blob: ConstVoidPtr,
    _nbyte: i32,
    _destructor: ConstVoidPtr,
) -> i32 {
    log!("Warning: sqlite3_bind_blob - stubbed");
    SQLITE_MISUSE
}

fn sqlite3_bind_null(_env: &mut Environment, _stmt: sqlite3_stmt, _idx: i32) -> i32 {
    log!("Warning: sqlite3_bind_null - stubbed");
    SQLITE_MISUSE
}

fn sqlite3_column_int(_env: &mut Environment, _stmt: sqlite3_stmt, _icol: i32) -> i32 {
    log!("Warning: sqlite3_column_int - stubbed");
    0
}

fn sqlite3_column_int64(_env: &mut Environment, _stmt: sqlite3_stmt, _icol: i32) -> i64 {
    log!("Warning: sqlite3_column_int64 - stubbed");
    0
}

fn sqlite3_column_double(_env: &mut Environment, _stmt: sqlite3_stmt, _icol: i32) -> f64 {
    log!("Warning: sqlite3_column_double - stubbed");
    0.0
}

fn sqlite3_column_text(_env: &mut Environment, _stmt: sqlite3_stmt, _icol: i32) -> ConstPtr<u8> {
    log!("Warning: sqlite3_column_text - stubbed");
    ConstPtr::null()
}

fn sqlite3_column_blob(_env: &mut Environment, _stmt: sqlite3_stmt, _icol: i32) -> ConstVoidPtr {
    log!("Warning: sqlite3_column_blob - stubbed");
    ConstVoidPtr::null()
}

fn sqlite3_column_bytes(_env: &mut Environment, _stmt: sqlite3_stmt, _icol: i32) -> i32 {
    log!("Warning: sqlite3_column_bytes - stubbed");
    0
}

fn sqlite3_column_type(_env: &mut Environment, _stmt: sqlite3_stmt, _icol: i32) -> i32 {
    log!("Warning: sqlite3_column_type - stubbed");
    5 // SQLITE_NULL
}

fn sqlite3_column_count(_env: &mut Environment, _stmt: sqlite3_stmt) -> i32 {
    log!("Warning: sqlite3_column_count - stubbed");
    0
}

fn sqlite3_free(_env: &mut Environment, ptr: MutVoidPtr) {
    log!("Warning: sqlite3_free({:?}) - stubbed", ptr);
}

fn sqlite3_libversion(_env: &mut Environment) -> ConstPtr<u8> {
    log!("Warning: sqlite3_libversion - stubbed");
    ConstPtr::null()
}

fn sqlite3_libversion_number(_env: &mut Environment) -> i32 {
    log!("Warning: sqlite3_libversion_number - stubbed");
    3008000 // Pretend to be SQLite 3.8.0
}

const CONSTANTS: ConstantExports = &[];

pub const FUNCTIONS: FunctionExports = &[
    export_c_func!(sqlite3_open(_, _)),
    export_c_func!(sqlite3_open_v2(_, _, _, _)),
    export_c_func!(sqlite3_close(_)),
    export_c_func!(sqlite3_close_v2(_)),
    export_c_func!(sqlite3_exec(_, _, _, _, _)),
    export_c_func!(sqlite3_prepare_v2(_, _, _, _, _)),
    export_c_func!(sqlite3_step(_)),
    export_c_func!(sqlite3_finalize(_)),
    export_c_func!(sqlite3_reset(_)),
    export_c_func!(sqlite3_errmsg(_)),
    export_c_func!(sqlite3_errcode(_)),
    export_c_func!(sqlite3_last_insert_rowid(_)),
    export_c_func!(sqlite3_changes(_)),
    export_c_func!(sqlite3_bind_int(_, _, _)),
    export_c_func!(sqlite3_bind_int64(_, _, _)),
    export_c_func!(sqlite3_bind_double(_, _, _)),
    export_c_func!(sqlite3_bind_text(_, _, _, _, _)),
    export_c_func!(sqlite3_bind_blob(_, _, _, _, _)),
    export_c_func!(sqlite3_bind_null(_, _)),
    export_c_func!(sqlite3_column_int(_, _)),
    export_c_func!(sqlite3_column_int64(_, _)),
    export_c_func!(sqlite3_column_double(_, _)),
    export_c_func!(sqlite3_column_text(_, _)),
    export_c_func!(sqlite3_column_blob(_, _)),
    export_c_func!(sqlite3_column_bytes(_, _)),
    export_c_func!(sqlite3_column_type(_, _)),
    export_c_func!(sqlite3_column_count(_)),
    export_c_func!(sqlite3_free(_)),
    export_c_func!(sqlite3_libversion()),
    export_c_func!(sqlite3_libversion_number()),
];
