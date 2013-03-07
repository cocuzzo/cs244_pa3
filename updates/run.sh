export NOX_CORE_DIR=/home/ubuntu/nox-classic/build/src 
export LD_PRELOAD=/home/ubuntu/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:/home/ubuntu/nox-classic/build/src/lib/.libs/libnoxcore.so:/home/ubuntu/nox-classic/build/src/builtin/.libs/libbuiltin.so:/usr/lib/libboost_filesystem.so 
./run.py -m fattree fattree 1 none
