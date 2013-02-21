# import sys

# sys.path.append('/home/openflow/frenetic/updates/examples')

from nxtopo import NetworkXTopo
from mininet.topo import Node
import networkx as nx

class MyTopo( NetworkXTopo ):

    def __init__( self, enable_all = True ):
        
        ingressSwitch = 1
        egressSwitch = 2
        leftFilter = 10
        middleFilter = 11
        rightFilter = 12

        host1 = 20
        host2 = 21
        host3 = 22
        host4 = 23
        server = 30

        switches = [ ingressSwitch,
                     egressSwitch,
                     leftFilter,
                     middleFilter,
                     rightFilter]
        
       
        graph = nx.Graph()
        
        host_location = { host1 : (ingressSwitch, 1),
                          host2 : (ingressSwitch, 2),
                          host3 : (ingressSwitch, 3),
                          host4 : (ingressSwitch, 4),
                          server : (egressSwitch, 1)
                        }
        
        # Add switches
        for switch in switches:
            graph.add_node( switch )
                         
        # Add edges
        graph.add_edge( ingressSwitch, leftFilter )
        graph.add_edge( ingressSwitch, middleFilter )
        graph.add_edge( ingressSwitch, rightFilter )
        graph.add_edge( leftFilter, egressSwitch )
        graph.add_edge( middleFilter, egressSwitch )
        graph.add_edge( rightFilter, egressSwitch )
        
        super( MyTopo, self ).__init__(graph, host_location)        

topos = { 'mytopo': ( lambda: MyTopo() ) } 
