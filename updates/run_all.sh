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

EXPERIMENT=1
# For experiment rode (can run quickly)
if [ $EXPERIMENT -ne 0 ] ;
    then
    echo "Running in experiment mode."
    range="24 36 48 60 72 84 96 108 120 132 144 156 168 180 192";
else
    # For Mininet rode (full setup)
    echo "Running in non-experiment mode."
    range="24 36 48 60 72 84 96";
fi

for nodes in $(echo $range) ; do

    dir=$rootdir/n$nodes/
    mkdir -vp $dir

    for topo in fattree waxman smallworld
#                fattree_multicast waxman_multicast smallworld_multicast
      do

      for opts in none subspace ; do

        #for flavor in 1 2 3; do
        for flavor in 1 ; do

          [ "$topo" = "fattree" ] && let "switches=$nodes/6"
          [ "$topo" = "waxman" ] && let "switches=$nodes/4"
          [ "$topo" = "smallworld" ] && let "switches=$nodes/4"

          mn -c 2> /dev/null

          if [ $EXPERIMENT -ne 0 ] ; then
            # Experiment mode
            cmd="./run.py -e -n $switches -m $topo $topo $flavor $opts"
          else
            # Non-experiment mode
            cmd="./run.py -n $switches -m $topo $topo $flavor $opts"
          fi

          echo $cmd
          $cmd > $dir/cu-n$nodes-t$topo-f$flavor-$opts.txt
          chmod -R +w $dir/cu-n$nodes-t$topo-f$flavor-$opts.txt

          echo "Started at" $start
          echo "Ended at" `date`

        done

      done

    done
    python plot-results.py --dir $rootdir -o $rootdir --type ops
    python plot-results.py --dir $rootdir -o $rootdir --type time
    python plot-results.py --dir $rootdir -o $rootdir --type ops_per_time
    python plot-results.py --dir $rootdir -o $rootdir --type table
done
