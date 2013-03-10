# run a simple test. 
# args = topo, num switches, flavor
# example: 'sudo ./run.sh fattree 4 1'
export NOX_CORE_DIR=/home/ubuntu/nox-classic/build/src 
export LD_PRELOAD=/home/ubuntu/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:/home/ubuntu/nox-classic/build/src/lib/.libs/libnoxcore.so:/home/ubuntu/nox-classic/build/src/builtin/.libs/libbuiltin.so:/usr/lib/libboost_filesystem.so        
export UPDATES_DIR=/home/ubuntu/cs244_pa3/updates
./run.py -v -n $2 -m $1 $1 $3 none
