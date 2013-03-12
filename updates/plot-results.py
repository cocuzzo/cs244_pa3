#!/usr/bin/env python

#from util.helper import *
import glob
import os
import sys
from collections import defaultdict
import matplotlib.pyplot as plt
from pylab import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--out',
                    help="Save plot to output file, e.g.: --out plot.png",
                    dest="out",
                    default=None)

parser.add_argument('--dir',
                    dest="dir",
                    help="Directory from which outputs of the sweep are read.",
                    required=True)

args = parser.parse_args()
data = defaultdict(list)
nedata = defaultdict(list)
RTT = 85.0 # ms
BW = 62.5 # Mbps
nruns = 10 # Number of runs for your experiment
nflows = 800
nfiles = 0

def first(lst):
    return map(lambda e: e[0], lst)

def second(lst):
    return map(lambda e: e[1], lst)

def avg(lst):
    return sum(lst)/len(lst)

def median(lst):
    l = len(lst)
    lst.sort()
    return lst[l/2]

# Convert the number of switches to hosts
def nodes_to_hosts(nodes, topo):

  if 'fattree' in topo:
    return nodes * 6
  elif 'waxman' in topo or 'smallworld' in topo:
    return nodes * 4
  else:
    print "Unknown topo: %s" % topo


# Parse data
def parse_data(filename, results):
    '''
      {flavor: {'fattree': [[nodes, total, overhead], ...],
                'waxman':  [[nodes, total, overhead], ...]
      },
      ...,
      }
    '''

    lines = open(filename).read().split("\n")
    topo = lines[0].split('=')[1].strip()
    nodes = int(lines[1].split('=')[1].strip())
    flavor = lines[2].split('=')[1].strip()
  
    if 'multicast' in topo:
      flavor = 'multicast_%s' % flavor
  

    opts = lines[3].split('=')[1].strip()
    lines = lines[3:]
    print topo, nodes, flavor, opts
  
    hosts = nodes_to_hosts(nodes, topo)

    for line in lines:
      if 0 == line.find('total'):

        totals = line.split()
        overhead = int(totals[-1][:-1])
        total = int(totals[-2])
        if flavor not in results:
          results[flavor] = {}
      
        if topo not in results[flavor]:
          results[flavor][topo] = []

        results[flavor][topo].append((hosts, total, overhead))

results = {}
for f in glob.glob("%s/*/*.txt" % args.dir):
    print "Parsing %s" % f
    parse_data(f, results)
    print "results = ", results
    nfiles += 1

if nfiles == 0:
    print "Result files not found.   Did you pass the directory correctly?"
    sys.exit(0)

# Plot data
for flavor, topologies in results.items():
    plt.figure()
  
    for topo, data in topologies.items():
      
      nodes = [d[0] for d in data]
      totals = [d[1] for d in data]
      overheads = [d[2] for d in data]

      print "Plotting, nodes = %s, totals = %s" % (nodes, totals)
      
      fit = polyfit(nodes,totals,1)
      fit_fn = poly1d(fit) # fit_fn is now a function which takes in x and returns an estimate for y

      plt.plot(nodes, totals, 'o', nodes, fit_fn(nodes), '-', label=topo)
      plt.title("Flavor %s" % flavor)

    plt.legend()
    plt.ylabel("# of Update Messages")
    plt.xlabel("Total #Hosts")

    if args.out:
        print "Saving to %s" % args.out
        fname = "flavor_%s" % flavor
        plt.savefig(os.path.join(args.out, fname))
    else:
        plt.show()
