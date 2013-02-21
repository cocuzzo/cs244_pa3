################################################################################
# The Frenetic Project                                                         #
# frenetic@frenetic-lang.org                                                   #
################################################################################
# Licensed to the Frenetic Project by one or more contributors. See the        #
# NOTICE file distributed with this work for additional information            #
# regarding copyright and ownership. The Frenetic Project licenses this        #
# file to you under the following license.                                     #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided the following conditions are met:       #
# - Redistributions of source code must retain the above copyright             #
#   notice, this list of conditions and the following disclaimer.              #
# - Redistributions in binary form must reproduce the above copyright          #
#   notice, this list of conditions and the following disclaimer in            #
#   the documentation or other materials provided with the distribution.       #
# - The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################
# /updates/examples/hub.py                                                     #
# Shortest-path routing example over a single switch                           #
################################################################################

import sys
from collections import defaultdict
import networkx as nx
import verification

import update_lib
from policy import *
from run import send_signal 
from hub_topo import Topology
from routing_policies import shortest_path_policy

def topology1():
    graph = Topology(size).nx_graph()
    graph.remove_nodes_from([5,6])
    return graph

def topology2():
    return Topology(size).nx_graph()

def topology3():
    graph = Topology(size).nx_graph()
    graph.remove_nodes_from([1,2,5,6])
    return graph

topologies = \
  [ topology1,
    topology2,
    topology3 ]

policies = \
  [ shortest_path_policy,
    shortest_path_policy,
    shortest_path_policy ]
  
properties = \
  [ True, 
    True,
    True ]

def run_version(version,cont,update_mechanism):
    topology = topologies[version]()
    policy = policies[version](topology)
    print "Updating to %s" % version
    update_mechanism(topology, policy)
    cont()

def mk_cb(f):
    return lambda:update_lib.inst.post_callback(3,f)

def all_done():
    s = str(update_lib.inst.stats)
    # sys.stdout.flush()    
    send_signal(s)
    return

def main_run(update):
    version2_cont = all_done    
    version1_cont = mk_cb(lambda:run_version(2, version2_cont, update))
    version0_cont = mk_cb(lambda:run_version(1, version1_cont, update))
    run_version(0,version0_cont, update)
    
def main_flows():
    per_flow = lambda topology,policy: update_lib.per_flow_update(topology,policy,60,lambda pattern:pattern,300)
    version1_cont = all_done
    version0_cont = mk_cb(lambda:run_version(1, version1_cont, per_flow))
    run_version(0,version0_cont, per_flow)
    
def main(_size):
    global size
    size = _size
    per_packet = update_lib.per_packet_update
    main_run(per_packet)
