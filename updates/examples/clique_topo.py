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
# /updates/examples/clique_topo.py                                             #
# Clique topology                                                              #
# $Id$ #
################################################################################

from nxtopo import *

class Topology(NXTopo):

    def __init__(self, numHosts=8, numSwitches=6):

        super(Topology, self).__init__()

        # add switches
        hosts = range(1,numHosts+1)
        switches = range(101,numSwitches+101)

        # Add switches
        for s in switches:
            self.add_switch(s)
                         
        # Add hosts
        for h in hosts:
            self.add_host(h)

        # Add switch links
        for si in switches:
            for sj in switches:
                if si != sj:
                    self.add_link(si,sj)
        
        # Add host links
        i = 0
        for h in hosts:
            sw = 101 + (i % numSwitches)
            self.add_link(h,sw)
            i += 1

        self.finalize()

topos = { 'clique': ( lambda: Topology().mininet_topo() ) }
