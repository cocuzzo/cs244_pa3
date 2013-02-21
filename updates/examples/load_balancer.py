
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
# /updates/examples/load_balancer.py                                           #
# Load balancer example                                                        #
################################################################################

import sys
from collections import defaultdict
import networkx as nx

import update_lib
from policy import *
from run import send_signal 
from load_balancer_topo import * 

from nox.lib.packet.packet_utils import octstr_to_array


DELAY=3

def ip(h):
    return "10.0.0." + str(h)

def mac(h):
    x = hex(h)[2:]
    return octstr_to_array("00:00:00:00:00:" + ("0" if h < 16 else "") + str(x))

##############
# TOPOLOGIES #
##############

#    {h1,h3,h5,h7}
#          |
#        s101
#       /    \
#      /      \
#   s102      s103
#     |         | 
# {h21,h22} {h31,h32}
# 
# {hDummy}--sDummy (only here to prime ARP caches)

def topology0():
    return Topology().nx_graph()

def topology1():
    return Topology().nx_graph()

topologies = \
  [ topology0,
    topology1 ]

############
# POLICIES #
############

ip0 = "10.0.0.0" # 001 and 011
ip1 = "10.0.0.4" # 101 and 111

ip00 = "10.0.0.1" # 001
ip01 = "10.0.0.3" # 011
ip10 = "10.0.0.5" # 101
ip11 = "10.0.0.7" # 111

def policy0(graph):
    port = lambda x,y:graph.node[x]['ports'][y]
    raw = { s101: [ ({ NW_SRC:ip0, NW_SRC_N_WILD:2, NW_DST:ip(hDummy), DL_TYPE:0x800 }, [ modify(("dstip", ip(h21))), modify(("dstmac", mac(h21))), forward(port(s101,s102))])
                  , ({ NW_SRC:ip1, NW_SRC_N_WILD:2, NW_DST:ip(hDummy), DL_TYPE:0x800 }, [ modify(("dstip", ip(h31))), modify(("dstmac", mac(h31))), forward(port(s101,s103))])
                  , ({ NW_SRC:ip(h21), NW_DST:ip(h1), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h1))])
                  , ({ NW_SRC:ip(h21), NW_DST:ip(h3), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h3))])
                  , ({ NW_SRC:ip(h31), NW_DST:ip(h5), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h5))])
                  , ({ NW_SRC:ip(h31), NW_DST:ip(h7), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h7))]) ]
          , s102: [ ({ NW_DST:ip(h21), DL_TYPE:0x800 }, [ forward(port(s102,h21)) ])
                  , ({ NW_SRC:ip(h21), DL_TYPE:0x800 }, [ forward(port(s102,s101)) ]) ]
          , s103: [ ({ NW_DST:ip(h31), DL_TYPE:0x800 }, [ forward(port(s103,h31)) ])
                  , ({ NW_SRC:ip(h31), DL_TYPE:0x800 }, [ forward(port(s103,s101)) ]) ] }
    return policy_of_dict(raw)

def policy1(graph):
    port = lambda x,y:graph.node[x]['ports'][y]
    raw = { s101: [ ({ NW_SRC:ip00, NW_DST:ip(hDummy), DL_TYPE:0x800 }, [ modify(("dstip", ip(h21))), modify(("dstmac", mac(h21))), forward(port(s101,s102))])
                  , ({ NW_SRC:ip01, NW_DST:ip(hDummy), DL_TYPE:0x800 }, [ modify(("dstip", ip(h22))), modify(("dstmac", mac(h22))), forward(port(s101,s102))])
                  , ({ NW_SRC:ip10, NW_DST:ip(hDummy), DL_TYPE:0x800 }, [ modify(("dstip", ip(h31))), modify(("dstmac", mac(h31))), forward(port(s101,s103))])
                  , ({ NW_SRC:ip11, NW_DST:ip(hDummy), DL_TYPE:0x800 }, [ modify(("dstip", ip(h32))), modify(("dstmac", mac(h32))), forward(port(s101,s103))])
                  , ({ NW_SRC:ip(h21), NW_DST:ip(h1), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h1))])
                  , ({ NW_SRC:ip(h22), NW_DST:ip(h3), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h3))])
                  , ({ NW_SRC:ip(h31), NW_DST:ip(h5), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h5))])
                  , ({ NW_SRC:ip(h32), NW_DST:ip(h7), DL_TYPE:0x800 }, [ modify(("srcip", ip(hDummy))), modify(("srcmac", mac(hDummy))), forward(port(s101,h7))]) ]
          , s102: [ ({ NW_DST:ip(h21), DL_TYPE:0x800 }, [ forward(port(s102,h21)) ])
                  , ({ NW_DST:ip(h22), DL_TYPE:0x800 }, [ forward(port(s102,h22)) ])
                  , ({ NW_SRC:ip(h21), DL_TYPE:0x800 }, [ forward(port(s102,s101)) ]) 
                  , ({ NW_SRC:ip(h22), DL_TYPE:0x800 }, [ forward(port(s102,s101)) ]) ]
          , s103: [ ({ NW_DST:ip(h31), DL_TYPE:0x800 }, [ forward(port(s103,h31)) ])
                  , ({ NW_DST:ip(h32), DL_TYPE:0x800 }, [ forward(port(s103,h32)) ])
                  , ({ NW_SRC:ip(h31), DL_TYPE:0x800 }, [ forward(port(s103,s101)) ]) 
                  , ({ NW_SRC:ip(h32), DL_TYPE:0x800 }, [ forward(port(s103,s101)) ]) ] }
    return policy_of_dict(raw)

policies = \
  [ policy0, 
    policy1 ]

##############
# PROPERTIES #
##############

properties = \
  [ True, 
    True ]

###########
# SCRIPTS #
###########

def mk_cb(f):
    return lambda:update_lib.inst.post_callback(DELAY,f)

def all_done():
    s = str(update_lib.inst.stats)
    send_signal(s)
    return

def run_version(version,cont,update_mechanism):
    topology = topologies[version]()
    policy = policies[version](topology)
    print "Updating to %s\n%s" % (version,policy)
    sys.stdout.flush()
    update_mechanism(topology, policy)
    cont()

def main_flows():
    per_flow = lambda topology,policy: update_lib.per_flow_update(topology,policy,60,lambda pattern:pattern,300)
    version1_cont = all_done
    version0_cont = mk_cb(lambda:run_version(1, version1_cont, per_flow))
    run_version(0,version0_cont, per_flow)

def main_run(update):
    version1_cont = all_done
    version0_cont = mk_cb(lambda:run_version(1, version1_cont, update))
    run_version(0,version0_cont, update)
    
def main():
    update = update_lib.per_packet_update
    main_run(update)

def main_naive():
    update = update_lib.per_packet_naive_update
    main_run(update)
