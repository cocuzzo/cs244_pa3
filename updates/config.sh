#!/bin/bash

export HOME_DIR=$HOME
export NOX_CORE_DIR=$HOME_DIR/nox-classic/build/src

# Add shared objects for SWIG-code
export LD_PRELOAD=$HOME_DIR/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:$HOME_DIR/nox-classic/build/src/lib/.libs/libnoxcore.so:$HOME_DIR/nox-classic/build/src/builtin/.libs/libbuiltin.so:/usr/lib/libboost_filesystem.so

# Directory for update_app.py (usually, the same as run.py)
export UPDATES_DIR=`pwd`
