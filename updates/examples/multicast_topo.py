from nxtopo import *

##
# Multicast Topology
# Frenetic <frenetic-hackers@lists.frenetic-lang.org>
##
#
#            {h1}
#             |
#           s101
#          /   \
#         /     \
# {h2}--s102---s103--{h3}
#        |  \ /  |
#        |   X   |
#        | /  \  |
# {h4}--s104---s105--{h5}
#         \     / 
#          \   /
#          s106
#            |
#           {h6}
#
##

numSwitches=6

class Topology(NXTopo):

    def __init__(self):

        super(Topology, self).__init__()

        # add switches
        switches=range(101,numSwitches+101)

        # Add hosts and switches
        for s in switches:
            self.add_switch(s)
            h = s % 100
            self.add_host(h)
            self.add_link(h,s)
                         
        # Add switch links
        self.add_link(101,102)
        self.add_link(101,103)
        self.add_link(102,103)
        self.add_link(102,104)
        self.add_link(102,105)
        self.add_link(103,104)
        self.add_link(103,105)
        self.add_link(104,105)
        self.add_link(104,106)
        self.add_link(105,106)
        self.finalize()

topos = { 'multicast': ( lambda: Topology().mininet_topo() ) }
