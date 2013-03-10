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

for hosts in 12 ; do

    dir=$rootdir
    mkdir -vp $dir

    for topo in fattree waxman smallworld ; do
        for flavor in 1 2 3; do
           
            [ "$topo" = "fattree" ] && let "switches=$hosts/6"
            [ "$topo" = "waxman" ] && let "switches=$hosts/4" 
            [ "$topo" = "smallworld" ] && let "switches=$hosts/4"

            cmd="./run.py -n $switches -m $topo $topo $flavor none"
            echo $cmd
            $cmd > $dir/cu-h$hosts-t$topo-f$flavor.txt       
            mn -c

        done
        echo "Started at" $start
        echo "Ended at" `date`
    done
done
#python plot-results.py --dir $rootdir -o $rootdir/result-$run.png
