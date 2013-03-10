#!/bin/bash
# Code for reproducing statistics for making consistent updates

# Exit on any failure
set -e

# Check for uninitialized variables
set -o nounset

ctrlc() {
	killall -9 python
	mn -c
	exit
}

trap ctrlc SIGINT

export HOME_DIR=/home/ubuntu
export NOX_CORE_DIR=$HOME_DIR/nox-classic/build/src 

# Add shared objects for SWIG-code
export LD_PRELOAD=$HOME_DIR/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:$HOME_DIR/nox-classic/build/src/lib/.libs/libnoxcore.so:$HOME_DIR/nox-classic/build/src/builtin/.libs/libbuiltin.so:/usr/lib/libboost_filesystem.so 

#NOX_CORE_DIR=/home/ubuntu/nox-classic/build/src 
#LD_PRELOAD=/home/ubuntu/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:
#/home/ubuntu/nox-classic/build/src/lib/.libs/libnoxcore.so:
#/home/ubuntu/nox-classic/build/src/builtin/.libs/libbuiltin.so:
#/usr/lib/libboost_filesystem.so

start=`date`
exptid=`date +%b%d-%H%M`
rootdir=cupdates-$exptid

for run in {1..1}; do
	for num_hosts in 4 ; do
		dir=$rootdir/nf$num_hosts-r$run
        mkdir -vp $dir

        mn -c
        date
		cmd="./run.py -v -n $num_hosts -m waxman waxman 1 none"
	    echo $cmd
	    $cmd > $dir/result.txt
        date

	done
    cat $rootdir/*/result.txt | sort -n -k 1
    #python plot-results.py --dir $rootdir -o $rootdir/result-$run.png
    echo "Started at" $start
    echo "Ended at" `date`
done
