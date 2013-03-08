#!/bin/bash

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

start=`date`
exptid=`date +%b%d-%H:%M`

rootdir=cupdates-$exptid
plotpath=util
iperf=~/iperf-patched/src/iperf

# Change the interface name for which queue size is adjusted
# Links are numbered as switchname-eth1,2,etc in the order they are
# added to the topology.
iface=s1-eth1

export NOX_CORE_DIR=/home/mininet/nox-classic/build/src 
export LD_PRELOAD=/home/mininet/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:/home/mininet/nox-classic/build/src/lib/.libs/libnoxcore.so:/home/mininet/nox-classic/build/src/builtin/.libs/libbuiltin.so:/usr/lib/libboost_filesystem.so 

for run in {1..1}; do
	for num_hosts in 1 5 ; do
		dir=$rootdir/nf$num_hosts-r$run

		cmd="python run.py -n $num_hosts -m fattree fattree 1 none > $dir"
	    echo $cmd
	    $cmd

	done
    #cat $rootdir/*/result.txt | sort -n -k 1
    #python plot-results.py --dir $rootdir -o $rootdir/result-$run.png
    echo "Started at" $start
    echo "Ended at" `date`
done

