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

source config.sh

start=`date`
exptid=`date +%b%d-%H%M`
rootdir=cupdates-results-$exptid

mn -c

for nodes in 24 36 ; do

    dir=$rootdir/n$nodes/
    mkdir -vp $dir

    for topo in fattree waxman smallworld fattree_multicast \
                waxman_multicast smallworld_multicast ; do
        for flavor in 1 2 3; do
           
            [ "$topo" = "fattree" ] && let "switches=$nodes/6"
            [ "$topo" = "waxman" ] && let "switches=$nodes/4" 
            [ "$topo" = "smallworld" ] && let "switches=$nodes/4"

            mn -c 2> /dev/null
            cmd="./run.py -e -n $switches -m $topo $topo $flavor none"
            echo $cmd
            $cmd > $dir/cu-n$nodes-t$topo-f$flavor.txt

        done
        echo "Started at" $start
        echo "Ended at" `date`
    done
done
#python plot-results.py --dir $rootdir -o $rootdir/result-$run.png
