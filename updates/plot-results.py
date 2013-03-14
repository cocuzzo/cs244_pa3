#!/usr/bin/env python

#from util.helper import *
import glob
import os
import sys
from collections import defaultdict
import argparse
import numpy
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from pylab import *

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--out',
                    help="Save plot to output file, e.g.: --out plot.png",
                    dest="out",
                    default=None)

parser.add_argument('--dir',
                    dest="dir",
                    help="Directory from which outputs of the sweep are read.",
                    required=True)

parser.add_argument('--type',
                    help="Type of plot (ops or time).",
                    required=True)

parser.add_argument('-v', '--verbose',
                    help="Type of plot (ops or time).",
		    action='store_true',
		    default=None)

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

def flavor_name(flavor):
  if flavor == 1:
    return 'Hosts'
  elif flavor == 2:
    return 'Routes'
  else:
    return 'Both'


# Convert the number of switches to hosts
def nodes_to_hosts(nodes, topo):

  if 'fattree_multicast' in topo:
    return nodes * 4
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
  while n < len(lines):
    
    # Search for the phrase "Update Statistics"
    if 0 != lines[n].find('Opts ='):
      n += 1
      continue
    else:
      n -= 3

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
  
    hosts = nodes_to_hosts(nodes, topo)

    while 0 != lines[n].find('total') and n < len(lines):
      n += 1
    
    totals = lines[n].split()
    n += 1
  
    time = None
    if '%' in totals[-1]:
      # No timing
      overhead = int(totals[-1][:-1])
      total = int(totals[-2])
    
    else:
      # With times
      time = float(totals[-1])
      overhead = int(totals[-2][:-1])
      total = int(totals[-3])
      
    if graph_type not in results:
      results[graph_type] = {}
    
    if topo not in results[graph_type]:
      results[graph_type][topo] = []

    if args.verbose:
	print "Adding graph_type=%s, topo=%s, %d %d %d %d" \
		% (graph_type, topo, hosts, total, overhead, time)
    results[graph_type][topo].append((hosts, total, overhead, time))

results = {}
for f in glob.glob("%s/*/*.txt" % args.dir):
  print "Parsing %s" % f
  parse_file(f, results)
           
  nfiles += 1

if nfiles == 0:
    print "Result files not found.   Did you pass the directory correctly?"
    sys.exit(0)

def r_squared(fit, x, y):
  yhat =  fit(x)                         # or [p(z) for z in x]
  ybar =  numpy.sum(y)/len(y)          # or sum(y)/len(y)
  ssreg = numpy.sum((yhat-ybar)**2)   # or sum([ (yihat - ybar)**2 for yihat in yhat])
  sstot = numpy.sum((y - ybar)**2)    # or sum([ (yi - ybar)**2 for yi in y])
  r_squared = ssreg / sstot
  return r_squared

if args.type == 'ops':
  # Plot # of ops
  for graph_type, topologies in results.items():
    
      plt.figure()
      has_plot = False
      for topo, data in topologies.items():
        
        A = array([(d[0], d[1]) for d in data],
                      dtype=[('x',int), ('y',int)])
        A.sort(order='x')
        
        X = A['x']
        Y = A['y']
    
        if len(X) < 3:
          print "Skipping %s %s, #=%d" % (graph_type, topo, len(X))
          continue
            
        else:
          has_plot = True
          print "Plotting %s %s, #=%d" % (graph_type, topo, len(X))

        
        fit = polyfit(X,Y,2)
        fit_fn = poly1d(fit) # fit_fn is now a function which takes in x and returns an estimate for y
        
        plt.plot(X, Y, 'o', label=topo)
        X_plot = linspace(0,max(X))
        plt.plot(X_plot, fit_fn(X_plot), '-', label='%s-polyfit (r^2=%.3f)' % \
           (topo, r_squared(fit_fn, X, Y)))
        application = graph_type.split('_')[0]
        fname = flavor_name(int(graph_type.split('_')[1]))
        plt.title("Total Ops to update %s/%s" %
                  (application, fname))

      if has_plot:
        plt.legend(loc='upper left')
        plt.ylabel("# of Update Messages")
        plt.xlabel("Number of Hosts")
        plt.ylim(0, max(Y))

        if args.out:
            print "Saving to %s" % args.out
            fname = "ops_%s" % graph_type
            plt.savefig(os.path.join(args.out, fname))
        else:
            plt.show()

if args.type == 'time':

  # Plot amount of time
  for graph_type, topologies in results.items():
    
    plt.figure()
    has_plot = False
    for topo, data in topologies.items():
      
      data = [d for d in data if d[3]]
    
      A = array([(d[0], d[3]) for d in data],
                dtype=[('x',int), ('y',float)])
      A.sort(order='x')
      
      X = A['x']
      Y = A['y']
      
      if len(X) < 3:
        print "Skipping %s %s, #=%d" % (graph_type, topo, len(X))
        continue
      
      else:
        has_plot = True
        print "Plotting %s %s, #=%d" % (graph_type, topo, len(X))
    
    
      fit = polyfit(X,Y,2)
      fit_fn = poly1d(fit) # fit_fn is now a function which takes in x and returns an estimate for y
      
      plt.plot(X, Y, 'o', label=topo)
      X_plot = linspace(0,max(X))
      plt.plot(X_plot, fit_fn(X_plot), '-', label='%s-polyfit (r^2=%.3f)' % \
               (topo, r_squared(fit_fn, X, Y)))
      application = graph_type.split('_')[0]
      fname = flavor_name(int(graph_type.split('_')[1]))
      plt.title("Time to update %s/%s" %
                (application, fname))
  
    if has_plot:
      plt.legend(loc='upper left')
      plt.ylabel("Time (sec)")
      plt.xlabel("Number of Hosts")
      plt.ylim(0, max(Y))


      if args.out:
        fname = os.path.join(args.out, "time_%s" % graph_type)
        print "Saving to %s" % fname
        plt.savefig(fname)
      else:
        plt.show()

if args.type == 'ops_per_time':
  
  # Plot amount of time
  for graph_type, topologies in results.items():
    
    plt.figure()
    has_plot = False
    for topo, data in topologies.items():
      
      data = [d for d in data if d[3]]
      
      A = array([(d[0], d[1]/d[3]) for d in data],
                dtype=[('x',int), ('y',float)])
      A.sort(order='x')
      
      X = A['x']
      Y = A['y']
      
      if len(X) < 2:
        print "Skipping %s %s, #=%d" % (graph_type, topo, len(X))
        continue
      
      else:
        has_plot = True
        print "Plotting %s %s, #=%d" % (graph_type, topo, len(X))
    
      
      fit = polyfit(X,Y,1)
      fit_fn = poly1d(fit) # fit_fn is now a function which takes in x and returns an estimate for y
      
      plt.plot(X, Y, 'o', label=topo)
      plt.plot(X, fit_fn(X), '-', label='%s-polyfit (r^2=%.3f)' % \
                  (topo, r_squared(fit_fn, X, Y)))
      application = graph_type.split('_')[0]
      fname = flavor_name(int(graph_type.split('_')[1]))
      plt.title("Ops per second to update %s/%s" %
                (application, fname))
  
    if has_plot:
      plt.legend(loc='lower right')
      plt.ylabel("Ops per sec")
      plt.xlabel("Number of Hosts")
      plt.ylim(0, max(Y))
      
      
      if args.out:
        fname = os.path.join(args.out, "ops_per_time_%s" % graph_type)
        print "Saving to %s" % fname
        plt.savefig(fname)
      else:
        plt.show()

if args.type == 'table':
  
  fname = os.path.join(args.out, "table.html")
  print "Writing to %s" % fname
  f = open(fname, 'w')
  
  result_table = []
        
  for graph_type, topologies in results.items():
    
    plt.figure()
    has_plot = False
    for topo, data in topologies.items():
              
      application, flavor, opts = graph_type.split('_')
      
      for d in data:
        result_table.append([application, topo, flavor_name(int(flavor)), opts,
                             d[0], d[1], d[2], d[3]])

  A = array([tuple(d) for d in result_table],
            dtype=[('application',np.str,16), ('topology', np.str, 20), \
                   ('update',np.str,16), ('opts',np.str,16), ('hosts',int), \
                   ('ops',int), ('overhead',int), ('time',float)])

  max_hosts = max(A['hosts'])
  A = A[A['hosts'] == max_hosts]

  for tab_application in ['routing', 'multicast']:
    
    f.write("<table border=\"1\">\n")
    f.write("<tr>\n")
    f.write("<th>Application</th>\n")
    f.write("<th>Topology</th>\n")
    f.write("<th>Update</th>\n")
    f.write("<th colspan=2>2PC</th>\n")
    f.write("<th colspan=3>Subset</th>\n")
    f.write("</tr>\n")

    f.write("<tr>\n")
    f.write("<th colspan=3></th>")
    f.write("<th>Ops</th>")
    f.write("<th>Max Overhead</th>")
    f.write("<th>Ops</th>")
    f.write("<th>Ops %</th>")
    f.write("<th>Max Overhead</th>")

    for tab_topo in ['fattree', 'waxman', 'smallworld']:

      for tab_update in ['Hosts', 'Routes', 'Both']:

        if tab_application == 'multicast':
          topo_str = '%s_%s' % (tab_topo, tab_application)
        else:
          topo_str = tab_topo

	# Check if at least one point
	if len(A[(A['application'] == tab_application) & \
                      (A['topology'] == topo_str) & \
                      (A['update'] == tab_update) & \
                      (A['opts'] == 'none')]) < 1:
	  print "Skipping %s %s %s none, insufficient results" % \
		 (tab_application, topo, tab_update)
	  continue
	else:
           print "Plotting %s %s %s none" % \
		 (tab_application, topo, tab_update)

        vals_2pc = A[((A['application'] == tab_application) & \
                      (A['topology'] == topo_str) & \
                      (A['update'] == tab_update) & \
                      (A['opts'] == 'none'))][0]

        vals_opt = A[((A['application'] == tab_application) & \
                      (A['topology'] == topo_str) & \
                      (A['update'] == tab_update) & \
                      (A['opts'] == 'subspace'))][0]

        f.write('<tr>')
        f.write('<td>%s</td>' % tab_application)
        f.write('<td>%s</td>' % tab_topo)
        f.write('<td>%s</td>' % tab_update)
        f.write('<td>%s</td>' % vals_2pc[5])        # Number of ops
        f.write('<td>%s%%</td>' % vals_2pc[6])        # Max verhead
        f.write('<td>%s</td>' % vals_opt[5])
        f.write('<td>%d%%</td>' % (float(vals_opt[5])/float(vals_2pc[5])*100))
        f.write('<td>%s%%</td>' % vals_opt[6])
        f.write('</tr>')

    f.write("</table>\n")
    f.write("<p>\n")



