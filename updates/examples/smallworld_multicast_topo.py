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
# /updates/examples/smallworld_topo.py                                         #
# Shortest-path routing topology                                               #
# $Id$ #
################################################################################

import networkx as nx
from nxtopo import *
import math
import random
import logging

log = logging.getLogger("frenetic.update.examples.smallworld_topo")

class SmallWorldTopology(NXTopo):

    def __init__(self, num_switches=None):

        
        super(SmallWorldTopology, self).__init__()
        if not num_switches:
            num_switches = 8
        num_hosts=num_switches*4
        
        # build graphman graph
        graph = nx.connected_watts_strogatz_graph(num_switches, min(4, num_switches/3), float(0.3), seed=35)

        # Add switches
        for s in graph:
            log.debug("Added switch %x" % s)
            self.add_switch(s+1)

        # Add edges
        for s1, s2 in graph.edges():
            self.add_link(s1+1, s2+1)
                         
        # Add hosts
        hostoffset = num_switches+2
        for h in range(1,num_hosts+1):
            # Add host
            host = h + hostoffset
            self.add_host(host)

            # Connect to a "random" switch
            s = graph.nodes()[h % len(graph)]
            self.add_link(host,s+1)
        # Globally connected host
        # self.add_host(999)
        # for switch in graph:
        #     self.add_link(999, switch+1)


        self.finalize()

Topology = SmallWorldTopology
