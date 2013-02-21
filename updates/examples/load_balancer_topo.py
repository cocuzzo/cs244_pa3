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
# /updates/examples/load_balcner_topo.py                                       #
# Load balancer topology                                                       #
################################################################################

from nxtopo import *

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

h1 = 1
h3 = 3
h5 = 5
h7 = 7
h21 = 21
h22 = 22
h31 = 31
h32 = 32

s101 = 101
s102 = 102
s103 = 103

hDummy = 99
sDummy = 199

class Topology(NXTopo):
    def __init__(self):

        super(Topology, self).__init__()

        self.add_host(h1)
        self.add_host(h3)
        self.add_host(h5)
        self.add_host(h7)
        self.add_host(h21)
        self.add_host(h22)
        self.add_host(h31)
        self.add_host(h32)
        self.add_host(hDummy)

        self.add_switch(s101)
        self.add_switch(s102)
        self.add_switch(s103)
        self.add_switch(sDummy)
                         
        self.add_link(s101,s102)
        self.add_link(s101,s103)

        self.add_link(h1,s101)
        self.add_link(h3,s101)
        self.add_link(h5,s101)
        self.add_link(h7,s101)

        self.add_link(h21,s102)
        self.add_link(h22,s102)

        self.add_link(h31,s103)
        self.add_link(h32,s103)
        
        self.add_link(hDummy,sDummy)

        self.finalize()
        return

topos = { 'load_balancer': ( lambda: Topology().mininet_topo() ) }
