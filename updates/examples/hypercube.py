# import sys

# sys.path.append('/home/openflow/frenetic/updates/examples')

from nxtopo import NetworkXTopo
from mininet.topo import Node
import networkx as nx

class MyTopo( NetworkXTopo ):

    def __init__( self, enable_all = True ):
        
        comp_graph = nx.complete_graph(32)

        graph = nx.Graph()
        for node in comp_graph:
            graph.add_node(node+1)
        for edge in comp_graph.edges():
            (src,dst) = edge
            graph.add_edge(src+1,dst+1)

        host_location = {}
        for host in range(1,graph.order()+1):
            host_location[host+graph.order()] = (host, 4)
            
        super( MyTopo, self ).__init__(graph, host_location)        

topos = { 'mytopo': ( lambda: MyTopo() ) } 
