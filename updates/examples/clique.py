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
# /updates/examples/clique.py                                                  #
# Shortest-path routing example over a clique                                  #
################################################################################

import sys
from collections import defaultdict
import networkx as nx
import verification

import update_lib
from policy import *
from run import send_signal 
from clique_topo import Topology 

def ip(h):
    return "10.0.0." + str(h)

def shortest_path_policy(graph):
    raw = defaultdict(lambda:[])
    for src in graph.hosts():
        for dst in graph.hosts():
            if src != dst:
                path = nx.shortest_path(graph,src,dst)[1:]
                curr = path.pop(0)
                for next in path:
                    port = graph.node[curr]['ports'][next]
                    pat = { DL_TYPE:0x800, NW_SRC:ip(src), NW_DST:ip(dst) }
                    acts = [forward(port)]
                    raw[curr].append((pat,acts))
                    curr = next
    return policy_of_dict(raw)                    

#  {h1,h2,h3}
#       |
#     s101 - s106 clique
#      |
#  {h4,h4,h6}
#
def topology1():
    graph = Topology().nx_graph()
    graph.remove_nodes_from([1,2])
    return graph

#  {h1,h2,h3,h4}
#       |
#     s101
#      |
#  {h5,h6,h7,h8}
#
def topology2():
    return Topology().nx_graph()

#  {h1,h2}
#       |
#     s101
#      |
#  {h3,h4}
def topology3():
    graph = Topology().nx_graph()
    graph.remove_nodes_from([1,2,3,4])
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
    # sys.stdout.flush()        
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
    
def main():
    per_packet = update_lib.per_packet_update
    main_run(per_packet)

def main_naive():    
    main_run(update_lib.per_packet_naive_update)

def main_verification():
    net_policies = [ verification.NO_LOOPS,
        verification.MATCH_EGRESS(Pattern({'NW_SRC' : '127.0.0.1'}),ingress='dl_type = 0ud16_2048 & nw_src = 0ud32_1547 & nw_dst = 0ud32_1550 & switch = 101'),
        verification.WAYPOINT_SWITCHES(Pattern({}), ['106'], ingress='dl_type = 0ud16_2048 & nw_src = 0ud32_1547 & nw_dst = 0ud32_1550 & switch = 101') ]
    sig = ""
    for i in xrange(0, len(topologies)):
        topo = topologies[i]()
        policy = policies[i](topo)
        model = verification.KripkeModel(topo, policy)
        for net_policy in net_policies:
            result,msg = model.verify(net_policy)
            if not result:
                sig += '%d - Verification: %s\n%s\n' % (i,result,msg)
            else:
                sig += '%d - Verification: %s\n' % (i,result)
    send_signal(sig)
    return


