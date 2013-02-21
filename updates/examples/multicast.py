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
# /updates/examples/routing.py                                                 #
# Shortest-path routing example                                                #
# Static hosts, dynamic network                                                #
################################################################################

import sys
from collections import defaultdict
import networkx as nx
import verification

import update_lib
from policy import *
from run import send_signal 
from experiment_base import *

MULTICAST_ADDRESS = "239.0.0.1"

DELAY = 5

def spanning_tree_policy(graph):
    raw = defaultdict(lambda:[])
    # This assumes NetworkX 1.6, but 1.2 is installed by default. Upgrade if this line causes a problem
    tree = nx.minimum_spanning_tree(graph)
    switches = [ n for n in tree.nodes() if tree.node[n]['isSwitch'] ]
    for switch in switches:
        neighbors = tree.neighbors(switch)
        all_ports_assoc = tree.node[switch]['ports'].items()
        tree_ports = [ p for (s,p) in all_ports_assoc if s in neighbors ]
        for p in tree_ports:
            pattern = {DL_TYPE:0x800,NW_DST:MULTICAST_ADDRESS, IN_PORT:p}
            actions = [forward(q) for q in tree_ports if q != p]
            raw[switch].append((pattern,actions))
    return policy_of_dict(raw)

def ip(h):
    return "10.0.0." + str(h)

policies = \
  [ spanning_tree_policy,
    spanning_tree_policy,
    spanning_tree_policy ]
  
def run_version(version, cont, update_mechanism, flavor, ext, subspace, island, Topology):
    topology = topologies[flavor](version, Topology)
    policy = policies[version](topology)
    print "Updating to %s" % version
    # sys.stdout.flush()        
    update_mechanism(topology, policy, use_extension=ext, use_subspace=subspace, use_island=island)
    cont()

def mk_cb(f):
    return lambda:update_lib.inst.post_callback(DELAY,f)

def all_done():
    s = str(update_lib.inst.stats)
    # sys.stdout.flush()    
    send_signal(s)
    return

def main_run(update, flavor, ext, subspace, island, Topology):
    version2_cont = all_done    
    version1_cont = mk_cb(lambda:run_version(2, version2_cont, update, flavor, ext, subspace, island, Topology))
    version0_cont = mk_cb(lambda:run_version(1, version1_cont, update, flavor, ext, subspace, island, Topology))
    run_version(0,version0_cont, update, flavor, ext, subspace, island, Topology)
    
def main_flows():
    per_flow = lambda topology,policy: update_lib.per_flow_update(topology,policy,60,lambda pattern:pattern,300)
    main_run(per_flow)

def main(Topology, size, flavor, opt):
    # if topology == "fattree":
    #     from fattree_topo import FattreeTopology as Topology
    # elif topology == "waxman":
    #     from waxman_topo import WaxmanTopology as Topology
    if opt == "all":
        ext = True
        subspace = True
        island = False
    elif opt == "ext":
        ext = True
        subspace = False
        island = False
    elif opt == "subspace":
        ext = False
        subspace = True
        island = False
    # elif opt == "island":
    #     ext = False
    #     subspace = False
    #     island = True
    else:
        ext = False
        subspace = False
        island = False

    set_size(int(size))
    per_packet = update_lib.per_packet_update
    main_run(per_packet, int(flavor) - 1, ext, subspace, island, Topology)
