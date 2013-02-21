# import sys

# sys.path.append('/home/openflow/frenetic/updates/examples')

from nxtopo import NXTopo
from mininet.topo import Node
import networkx as nx

class Topology( NXTopo ):

    def __init__(self):

        super( Topology, self ).__init__()        
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
                     rightFilter
                   ]

        hosts = [ host1,
                  host2,
                  host3,
                  host4,
                  server
                ]
        
       
        host_location = { host1 : ingressSwitch,
                          host2 : ingressSwitch,
                          host3 : ingressSwitch,
                          host4 : ingressSwitch,
                          server : egressSwitch
                        }
        
        # Add switches
        for switch in switches:
            self.add_switch(switch)

        for host in hosts:
            self.add_host(host)
                         
        # Add edges
        self.add_link( ingressSwitch, leftFilter )
        self.add_link( ingressSwitch, middleFilter )
        self.add_link( ingressSwitch, rightFilter )
        self.add_link( leftFilter, egressSwitch )
        self.add_link( middleFilter, egressSwitch )
        self.add_link( rightFilter, egressSwitch )

        # add host edges
        for host,switch in host_location.iteritems():
            self.add_link(host,switch)

        self.finalize()
        

topos = { 'acl': ( lambda: Topology().mininet_topo() ) } 
