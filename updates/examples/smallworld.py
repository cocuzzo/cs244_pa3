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
# Dynamic hosts, static network                                                #
################################################################################

import sys

import networkx as nx
import string

import update_lib
from policy import *
from run import send_signal 
from routing_policies import shortest_path_policy, hosts_to_remove
from smallworld_topo import Topology

DELAY=0


policies = \
  [ shortest_path_policy,
    shortest_path_policy,
    shortest_path_policy ]

def switches_to_remove(version, graph):
    if version == 0:
        return []
    elif len(graph.switches()) < 2:
        return []
    else:
        scratch_graph = graph.copy()
        nodes = []
        hosts = scratch_graph.hosts()[::version * 2]
        for host1 in hosts:
            for host2 in hosts:
                if host1 == host2:
                    continue
                try:
                    path = nx.shortest_path(scratch_graph, host1, host2)
                except nx.exception.NetworkXNoPath:
                    continue
                # Pick a "middle" node
                node = path[len(path)/2]
                tmp_graph = scratch_graph.copy()
                tmp_graph.remove_node(node)
                try:
                    nx.shortest_path(tmp_graph, host1, host2)
                except nx.exception.NetworkXNoPath:
                    continue
                # If path still exists, toss node onto list
                scratch_graph.remove_node(node)
                nodes.append(node)
                
        return nodes
    
def topology1(version, topology):
    graph = topology.nx_graph()
    graph.remove_nodes_from(hosts_to_remove(version, graph))
    graph2 = graph.copy()
    graph2.remove_nodes_from(switches_to_remove(0, graph))
    return graph, graph2

def topology2(version, topology):
    graph = topology.nx_graph()
    graph.remove_nodes_from(hosts_to_remove(0, graph))
    graph2 = graph.copy()    
    graph2.remove_nodes_from(switches_to_remove(version, graph))
    return graph, graph2

def topology3(version, topology):
    graph = topology.nx_graph()
    graph.remove_nodes_from(hosts_to_remove(version, graph))
    graph2 = graph.copy()    
    graph2.remove_nodes_from(switches_to_remove(version, graph))
    return graph, graph2

topologies = [ topology1,
               topology2,
               topology3 ]

def run_version(version, cont, update_mechanism, flavor, ext, subspace, island, graph):
    topology1, topology2 = topologies[flavor](version, graph)
    policy = policies[version](topology1, topology2)
    print "Updating to %s" % version
    update_mechanism(topology1, policy, use_extension=ext, use_subspace=subspace, use_island=island)
    cont()

def mk_cb(f):
    return lambda:update_lib.inst.post_callback(DELAY,f)

def all_done():
    s = str(update_lib.inst.stats)
    # sys.stdout.flush()    
    send_signal(s)
    return

def main_run(update, flavor, ext, subspace, island, size):
    graph = Topology(size)
    version2_cont = all_done    
    version1_cont = mk_cb(lambda:run_version(2, version2_cont, update, flavor, ext, subspace, island, graph))
    version0_cont = mk_cb(lambda:run_version(1, version1_cont, update, flavor, ext, subspace, island, graph))
    run_version(0,version0_cont, update, flavor, ext, subspace, island, graph)
    
def main_flows():
    per_flow = lambda topology,policy: update_lib.per_flow_update(topology,policy,60,lambda pattern:pattern,300)
    main_run(per_flow)

def main(size, flavor, opt):
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

    per_packet = update_lib.per_packet_update
    main_run(per_packet, int(flavor) - 1, ext, subspace, island, size)
