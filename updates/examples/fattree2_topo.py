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
# /updates/examples/routing_topo.py                                            #
# Shortest-path routing topology                                               #
# $Id$ #
################################################################################

from nxtopo import *

# 4 hosts on each edge switch
# N/2 core switches

class FattreeTopology(NXTopo):

    def __init__(self, numEdgeSwitches=2):

        super(FattreeTopology, self).__init__()

        # add switches
        numHosts = 6*numEdgeSwitches
        numInternalSwitches = numEdgeSwitches/2
        numCoreSwitches = numInternalSwitches/2
        hosts = range(1, numHosts+1)
        firstSwitch = max(101, numHosts+1)
        edgeSwitches = range(firstSwitch, numEdgeSwitches + firstSwitch)
        self.edgeSwitches = edgeSwitches
        internalSwitches = range(numEdgeSwitches + firstSwitch, 
                                 numInternalSwitches + numEdgeSwitches + firstSwitch)        
        self.internalSwitches = internalSwitches
        coreSwitches = range(numInternalSwitches + numEdgeSwitches + firstSwitch,
                             numCoreSwitches + numInternalSwitches + numEdgeSwitches + firstSwitch)
        self.coreSwitches = coreSwitches

        # Add switches
        for s in edgeSwitches:
            self.add_switch(s)
        for s in internalSwitches:
            self.add_switch(s)            
        for s in coreSwitches:
            self.add_switch(s)
                         
        # Add hosts
        for h in hosts:
            self.add_host(h)

        # Each edge switch is connected to half of the internal switches, each internal switch is connected to every core switch
        # Add links
        for s1 in coreSwitches:
            for s2 in internalSwitches:
                self.add_link(s1, s2)

        for s1 in edgeSwitches:
            for s2 in internalSwitches:
                if (s1 + s2) % 2:
                    self.add_link(s1, s2)
                
        for h in hosts:
            self.add_link(h, firstSwitch + (h%numEdgeSwitches))
        self.finalize()

Topology = FattreeTopology
# topos = { 'routing_fattree': ( lambda: Topology().mininet_topo() ) }
