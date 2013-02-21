from mininet.topo import Topo, Node
import networkx as nx
from nox.lib.packet.packet_utils import ipstr_to_int

def host_to_ip(hostid):
    return ipstr_to_int("10.0.0." + str(hostid))

class MyTopo( Topo ):
    "Simple topology example."


    def __init__( self, enable_all = True ):
        "Create custom topo."

        ingressSwitch = 1
        egressSwitch = 2
        leftFilter = 10
        middleFilter = 11
        rightFilter = 12
        host1 = host_to_ip(20)
        host2 = host_to_ip(21)                      
        host3 = host_to_ip(22)
        host4 = host_to_ip(23)
        server = host_to_ip(30)

        # Add default members to class.
        super( MyTopo, self ).__init__()
        self.graph = nx.Graph()
        self.port_to = {}
        
        # Set Node IDs for hosts and switches
        self._switches = [ingressSwitch,
                          egressSwitch,
                          leftFilter,
                          middleFilter,
                          rightFilter]

        self._edge_switches = [ingressSwitch,
                               egressSwitch]
        self._hosts = [host1,
                       host2,                      
                       host3,
                       host4,
                       server]
        self._host_location = {}
        
        self.port_to[ingressSwitch] = {}
        self.port_to[egressSwitch] = {}
        self.port_to[leftFilter] = {}
        self.port_to[middleFilter] = {}
        self.port_to[rightFilter] = {}
        self.port_to[host1] = {}
        self.port_to[host2] = {}
        self.port_to[host3] = {}
        self.port_to[host4] = {}
        self.port_to[server] = {}

        # Add nodes
        self.add_node( ingressSwitch, Node( is_switch=True ) )
        self.graph.add_node( ingressSwitch, switch=True )
        self.add_node( egressSwitch, Node( is_switch=True ) )
        self.graph.add_node( egressSwitch, switch=True )
        self.add_node( rightFilter, Node( is_switch=True ) )
        self.graph.add_node( rightFilter, switch=True )        
        self.add_node( leftFilter, Node( is_switch=True ) )
        self.graph.add_node( leftFilter, switch=True )        
        self.add_node( middleFilter, Node( is_switch=True ) )
        self.graph.add_node( middleFilter, switch=True )        
        self.add_node( host1, Node( is_switch=False ) )
        self.graph.add_node( host1, switch=False )
        self.add_node( host2, Node( is_switch=False ) )
        self.graph.add_node( host2, switch=False )        
        self.add_node( host3, Node( is_switch=False ) )
        self.graph.add_node( host3, switch=False )        
        self.add_node( host4, Node( is_switch=False ) )
        self.graph.add_node( host4, switch=False )                        
        self.add_node( server, Node( is_switch=False ) )
        self.graph.add_node( server, switch=False )	        

        # Add edges
        self.add_edge( host1, ingressSwitch )
        self.graph.add_edge( host1, ingressSwitch )
        self._host_location[host1]=ingressSwitch
        self.port_to[host1][ingressSwitch] = 1
        self.port_to[ingressSwitch][host1] = 1        
        self.add_edge( host2, ingressSwitch )
        self.graph.add_edge( host2, ingressSwitch )
        self._host_location[host2]=ingressSwitch                
        self.port_to[host2][ingressSwitch] = 1
        self.port_to[ingressSwitch][host2] = 2
        self.add_edge( host3, ingressSwitch )
        self.graph.add_edge( host3, ingressSwitch )
        self._host_location[host3]=ingressSwitch                        
        self.port_to[host3][ingressSwitch] = 1
        self.port_to[ingressSwitch][host3] = 3
        self.add_edge( host4, ingressSwitch )
        self.graph.add_edge( host4, ingressSwitch )
        self._host_location[host4]=ingressSwitch                                
        self.port_to[host4][ingressSwitch] = 1
        self.port_to[ingressSwitch][host4] = 4
        self.add_edge( ingressSwitch, leftFilter )
        self.graph.add_edge( ingressSwitch, leftFilter )
        self.port_to[ingressSwitch][leftFilter] = 5
        self.port_to[leftFilter][ingressSwitch] = 1        
        self.add_edge( ingressSwitch, middleFilter )
        self.graph.add_edge( ingressSwitch, middleFilter )
        self.port_to[ingressSwitch][middleFilter] = 6
        self.port_to[middleFilter][ingressSwitch] = 1
        self.add_edge( ingressSwitch, rightFilter )
        self.graph.add_edge( ingressSwitch, rightFilter )
        self.port_to[ingressSwitch][rightFilter] = 7
        self.port_to[rightFilter][ingressSwitch] = 1        
        self.add_edge( leftFilter, egressSwitch )
        self.graph.add_edge( leftFilter, egressSwitch )
        self.port_to[leftFilter][egressSwitch] = 2
        self.port_to[egressSwitch][leftFilter] = 1        
        self.add_edge( middleFilter, egressSwitch )
        self.graph.add_edge( middleFilter, egressSwitch )
        self.port_to[middleFilter][egressSwitch] = 2
        self.port_to[egressSwitch][middleFilter] = 2        
        self.add_edge( rightFilter, egressSwitch )
        self.graph.add_edge( rightFilter, egressSwitch )
        self.port_to[rightFilter][egressSwitch] = 2
        self.port_to[egressSwitch][rightFilter] = 3
	self.add_edge( egressSwitch, server )
	self.graph.add_edge( egressSwitch, server )
        self._host_location[server]=egressSwitch                                        
        self.port_to[egressSwitch][server] = 4
        self.port_to[server][egressSwitch] = 1        

        # Consider all switches and hosts 'on'
        self.enable_all()

topos = { 'mytopo': ( lambda: MyTopo() ) } 
