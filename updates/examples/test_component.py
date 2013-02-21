
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
# /src/frenetic_app.py                                                         #
# Testing Harness for Nox                                                      #
# $Id$                                                                         #
################################################################################


import sys as sys
import logging as logging
import os

import nox.lib.core as nox_core
# import nox.lib.packet.packet_utils as nox_packet_utils
import nox.lib.openflow as openflow
# import nox.coreapps.examples.frenetic_net as net
# import nox.coreapps.examples.frenetic_lib as lib
# import nox.coreapps.examples.frenetic_util as util
# import nox.coreapps.examples.frenetic_rts as rts
# import nox.coreapps.examples.frenetic_frp as frp
import nox.coreapps.examples.frenetic_run as run
import test_topo

# from nox.coreapps.examples.frenetic_rts import SIZES,COUNTS

log = logging.getLogger("testing-harness")

# front-end initialization
# run.import_directories(os.getenv("FRENETIC_LIBS").rsplit())
frenetic_app = run.get_function_by_name(os.getenv("FRENETIC_APPLICATION"),
                                        os.getenv("FRENETIC_FUNCTION"))

l = os.getenv("FRENETIC_PARAMETERS")
args = []
if l != "":
    args = l.split(",")

inst = None

def datapath_join_callback(switch, stats):
    inst.switches_up.add(switch)
    if inst.switches_up == set(inst.topo.switches()):
        frenetic_app(inst)

    return nox_core.CONTINUE


class TestHarness(nox_core.Component):
    def __init__(self, ctxt):
        global inst
        nox_core.Component.__init__(self, ctxt)
        inst = self
        update.set_update_inst(self)

    def install(self):
        inst.register_for_datapath_join(datapath_join_callback)
        inst.topo = test_topo.get_topo(os.getenv("FRENETIC_TOPO"))

    def getInterface(self):
        return str(TestHarness)

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return TestHarness(ctxt)
    return Factory()

