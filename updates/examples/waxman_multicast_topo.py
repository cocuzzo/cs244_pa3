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
# /updates/examples/waxman_topo.py                                             #
# Shortest-path routing topology                                               #
# $Id$ #
################################################################################

import networkx as nx
from nxtopo import *
import math
import random

def waxman_graph(n, alpha=0.8, beta=0.1, L=None, domain=(0,0,1,1)):
    r"""Return a Waxman random graph.

    The Waxman random graph models place n nodes uniformly at random
    in a rectangular domain. Two nodes u,v are connected with an edge
    with probability

    .. math::
            p = \alpha*exp(d/(\beta*L)).

    This function implements both Waxman models.            

    Waxman-1:  `L` not specified
       The distance `d` is the Euclidean distance between the nodes u and v.
       `L` is the maximum distance between all nodes in the graph.

    Waxman-2: `L` specified
       The distance `d` is chosen randomly in `[0,L]`.

    Parameters
    ----------
    n : int
        Number of nodes
    alpha: float
        Model parameter
    beta: float
        Model parameter
    L : float, optional
        Maximum distance between nodes.  If not specified the actual distance
        is calculated.
    domain : tuple of numbers, optional
         Domain size (xmin, ymin, xmax, ymax)

    Returns
    -------
    G: Graph

    References
    ----------
    .. [1]  B. M. Waxman, Routing of multipoint connections. 
       IEEE J. Select. Areas Commun. 6(9),(1988) 1617-1622. 
    """
    # build graph of n nodes with random positions in the unit square
    G = nx.Graph()
    G.add_nodes_from(range(1,n+1))
    (xmin,ymin,xmax,ymax)=domain
    for n in G:
        G.node[n]['pos']=((xmin + (xmax-xmin))*random.random(),
                          (ymin + (ymax-ymin))*random.random())
    if L is None:
        # find maximum distance L between two nodes
        l = 0
        pos = [G.node[node]['pos'] for node in G]
        while pos:
            x1,y1 = pos.pop()
            for x2,y2 in pos:
                r2 = (x1-x2)**2 + (y1-y2)**2
                if r2 > l:
                    l = r2
        l=math.sqrt(l)
    else: 
        # user specified maximum distance
        l = L

    nodes=G.nodes()
    if L is None:
        # Waxman-1 model
        # try all pairs, connect randomly based on euclidean distance
        while nodes:
            u = nodes.pop()
            x1,y1 = G.node[u]['pos']
            for v in nodes:
                x2,y2 = G.node[v]['pos']
                r = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                if random.random() < alpha*math.exp(-r/(beta*l)):
                    G.add_edge(u,v)
    else:
        # Waxman-2 model
        # try all pairs, connect randomly based on randomly chosen l
        while nodes:
            u = nodes.pop()
            for v in nodes:
                r = random.random()*l
                if random.random() < alpha*math.exp(-r/(beta*l)):
                    G.add_edge(u,v)
    return G

class WaxmanTopology(NXTopo):

    def __init__(self, num_switches=None):

        super(Topology, self).__init__()
        
        num_hosts_per_switch = 4
        # Needed so that subsequent calls will generate the same graph
        random.seed(100)
        if not num_switches:
            num_switches = 5
        num_hosts = num_switches*num_hosts_per_switch
        # build waxman graph
        wax = waxman_graph(num_switches)

        # Add switches
        for s in wax:
            self.add_switch(s)

        # Add edges
        for s1, s2 in wax.edges():
            self.add_link(s1, s2)
                         
        # Add hosts
        hostoffset = num_switches+2
        for s in wax:
            # Add host
            host_base = num_hosts_per_switch*s + hostoffset
            for host in range(0, num_hosts_per_switch):
                self.add_host(host_base + host)
                self.add_link(host_base + host, s)
                
        # # Globally connected host
        # self.add_host(9999)
        # for switch in wax:
        #     self.add_link(9999, switch)


        # f = open('/home/openflow/workspace/foo.log', 'w')
        # f.write('hosts: %d\n' % len(self.hosts()))
        # f.close()
        # assert(False)
        self.finalize()

Topology=WaxmanTopology
topos = { 'waxman': ( lambda: WaxmanTopology().mininet_topo() ) }
