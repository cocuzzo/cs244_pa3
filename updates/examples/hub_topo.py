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
# /updates/examples/hub_topo.py                                                #
# Single-switch topology                                                       #
# $Id$ #
################################################################################

from nxtopo import *

#
#  {h1,h2,h3}
#       |
#     s101
#      |
#  {h3,h4,h5}
#
##

numSwitches=1

class Topology(NXTopo):

    def __init__(self, numHosts=6):

        super(Topology, self).__init__()

        # add switches
        hosts = range(1,numHosts+1)
        switches=range(101,numSwitches+101)

        # Add switches
        for s in switches:
            self.add_switch(s)
                         
        # Add hosts
        for h in hosts:
            self.add_host(h)
        
        # Add links
        for h in hosts:
            self.add_link(h,101)

        self.finalize()

topos = { 'hub': ( lambda: Topology().mininet_topo() ) }
