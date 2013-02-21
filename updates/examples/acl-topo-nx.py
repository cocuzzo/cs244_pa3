import networkx as nx

from mininet.topo import Topo, Node

# switches = [ingressSwitch = 1,
#             egressSwitch = 2, 
#             leftFilter = 10,
#             middleFilter = 11,
#             rightFilter = 12]
# hosts = [leftHost = 20,
#          rightHost = 21,
#          endHost = 30]

# G = nx.Graph()
# G.add_nodes(switches, is_switch=True)
# G.add_nodes(hosts, is_switch=False)

# # Add edges
# self.add_edge( leftHost, ingressSwitch )
# self.add_edge( rightHost, ingressSwitch )
# self.add_edge( ingressSwitch, leftFilter )
# self.add_edge( ingressSwitch, middleFilter )
# self.add_edge( ingressSwitch, rightFilter )
# self.add_edge( leftFilter, egressSwitch )                
# self.add_edge( middleFilter, egressSwitch )                
# self.add_edge( rightFilter, egressSwitch )
# self.add_edge( egressSwitch, endHost )        

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self, enable_all = True ):
        "Create custom topo."

        # Add default members to class.
        super( MyTopo, self ).__init__()

        # Set Node IDs for hosts and switches
        ingressSwitch = 1
        egressSwitch = 2
        leftFilter = 10
        middleFilter = 11
        rightFilter = 12
        leftHost = 20
        rightHost = 21
	endHost = 30

        # Add nodes
        self.add_node( ingressSwitch, Node( is_switch=True ) )
        self.add_node( egressSwitch, Node( is_switch=True ) )
        self.add_node( rightFilter, Node( is_switch=True ) )
        self.add_node( leftFilter, Node( is_switch=True ) )
        self.add_node( middleFilter, Node( is_switch=True ) )
        self.add_node( leftHost, Node( is_switch=False ) )
        self.add_node( rightHost, Node( is_switch=False ) )
        self.add_node( endHost, Node( is_switch=False ) )	

        # Add edges
        self.add_edge( leftHost, ingressSwitch )
        self.add_edge( rightHost, ingressSwitch )
        self.add_edge( ingressSwitch, leftFilter )
        self.add_edge( ingressSwitch, middleFilter )
        self.add_edge( ingressSwitch, rightFilter )
        self.add_edge( leftFilter, egressSwitch )                
        self.add_edge( middleFilter, egressSwitch )                
        self.add_edge( rightFilter, egressSwitch )
	self.add_edge( egressSwitch, endHost )        

        # Consider all switches and hosts 'on'
        self.enable_all()

topos = { 'mytopo': ( lambda: MyTopo() ) } 
