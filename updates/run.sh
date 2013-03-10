#!/bin/bash
# run a simple test. 
# args = topo, num switches, flavor
# example: 'sudo ./run.sh fattree 4 1'
source config.sh

echo "NOX_CORE_DIR = $NOX_CORE_DIR"
echo "LD_PRELOAD = $LD_PRELOAD"
echo "UPDATES_DIR = $UPDATES_DIR"

./run.py -v -n $2 -m $1 $1 $3 none
