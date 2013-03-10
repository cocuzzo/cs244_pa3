export NOX_CORE_DIR=/home/ubuntu/nox-classic/build/src 
export LD_PRELOAD=/home/ubuntu/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:/home/ubuntu/nox-classic/build/src/lib/.libs/libnoxcore.so:/home/ubuntu/nox-classic/build/src/builtin/.libs/libbuiltin.so:/usr/lib/libboost_filesystem.so 

mkdir results-n$1
for topo in fattree waxman smallworld; do
  for flavor in 1 2 3; do
    ./run.py -n $1 -m $topo $topo $flavor none > ./results-n$1/$topo-n$1-f$flavor.out
    mn -c
  done
done

