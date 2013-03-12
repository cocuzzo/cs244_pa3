#!/usr/bin/env python

#from util.helper import *
import glob
import os
import sys
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')

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

RESULTS_DIR = 'results'
args = parser.parse_args()

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


def parse_file(filename, results):
  '''
    {flavor: {'fattree': [[nodes, total, overhead], ...],
    'waxman':  [[nodes, total, overhead], ...]
    },
    ...,
    }
    '''

  lines = open(filename).read().split("\n")

  n = 0
  while n < len(lines)-4:
    
    # Search for the phrase "Update Statistics"
    if -1 == lines[n+4].find('Update Statistics'):
      n += 1
      continue
    
    topo = lines[n].split('=')[1].strip()
    n += 1
    
    nodes = int(lines[n].split('=')[1].strip())
    n += 1
    
    flavor = lines[n].split('=')[1].strip()
    n += 1
    
    opts = lines[n].split('=')[1].strip()
    n += 1
      
    if 'multicast' in topo:
      rule = 'multicast'
    else:
      rule = 'routing'
    
    graph_type = '%s_%s_%s' % (rule, flavor, opts)
  
    print topo, nodes, flavor, opts
  
    hosts = nodes_to_hosts(nodes, topo)

    while 0 != lines[n].find('total'):
      n += 1
    
    totals = lines[n].split()
    n += 1
  
    overhead = int(totals[-1][:-1])
    total = int(totals[-2])
    if graph_type not in results:
      results[graph_type] = {}
    
    if topo not in results[graph_type]:
      results[graph_type][topo] = []
    
    results[graph_type][topo].append((hosts, total, overhead))

results = {}
for f in glob.glob("%s/*/*.txt" % args.dir) + \
         glob.glob("%s/*.txt" % RESULTS_DIR):
  print "Parsing %s" % f
  parse_file(f, results)
#    print "results = ", resultss
  nfiles += 1

if nfiles == 0:
    print "Result files not found.   Did you pass the directory correctly?"
    sys.exit(0)

# Plot data
for graph_type, topologies in results.items():
  
  
    plt.figure()
    for topo, data in topologies.items():
      
      A_ops = array([(d[0], d[1]) for d in data],
                    dtype=[('x',int), ('y',int)])
      A_ops.sort(order='x')
      
      nodes = A_ops['x']
      ops = A_ops['y']

      print "Plotting %s %s, #=%d" % (graph_type, topo, len(nodes))
      
      fit = polyfit(nodes,ops,2)
      fit_fn = poly1d(fit) # fit_fn is now a function which takes in x and returns an estimate for y

      plt.plot(nodes, ops, 'o', label=topo)
      plt.plot(nodes, fit_fn(nodes), '-', label='topo-polyfit')
      plt.title("%s" % graph_type.replace('_', ' '))

    plt.legend(loc='upper left')
    plt.ylabel("# of Update Messages")
    plt.xlabel("Total #Hosts")

    if args.out:
        print "Saving to %s" % args.out
        fname = "%s" % graph_type
        plt.savefig(os.path.join(args.out, fname))
    else:
        plt.show()
