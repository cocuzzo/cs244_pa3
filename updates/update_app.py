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
# /updates/update_app.py                                                       #
# Update NOX Application                                                       #
################################################################################

import os
import sys
from nox.lib.core import *
from nox.lib.packet.ethernet import ethernet
UPDATES_DIR=os.environ["UPDATES_DIR"]
sys.path.append(UPDATES_DIR)
print "Adding UPDATES_DIR=%s" % UPDATES_DIR
import run

# front-end initialization
dirs = os.getenv("UPDATE_LIBS")
run.import_directories(dirs.rsplit())

print "Getting update application"
update_application = run.get_function_by_name(os.getenv("UPDATE_MODULE"),
                                                  os.getenv("UPDATE_FUNCTION"))
print "Getting got update application"

initial_topology = run.get_function_by_name(os.getenv("UPDATE_TOPOLOGY_MODULE"),
                                                os.getenv("UPDATE_TOPOLOGY"))

setup = run.get_function_by_name("update_lib", "setup")
end_flow = run.get_function_by_name("update_lib", "end_flow")

args = os.getenv("UPDATE_ARGS")
if args != "":
    args = args.split(",")
else:
    args = []

experiment_mode = os.getenv("UPDATE_EXPERIMENT_MODE")
num_nodes = int(os.getenv("UPDATE_NUM_NODES"))
log = logging.getLogger("frenetic.update.update_app")
inst = None

def datapath_join(switch,stats):
    inst.switches_up.add(switch)
    log.info("Switch %x just joined" % switch)
    if inst.switches_up == set(inst.initial_topology.switches()):
        update_application(num_nodes, *args)
    return

def flow_removed(cookie,sec,nsec,bytes,packets,switch,flow):
    end_flow(switch,flow)
    return

class Update(Component):
    def __init__(self, ctxt):
        global inst
        print "In __init__"
        Component.__init__(self, ctxt)

    def install(self):
        global inst
        print "In install"
        inst = self
        inst.switches_up = set()
        inst.initial_topology = initial_topology(num_nodes)
        if not experiment_mode:
            inst.register_for_datapath_join(datapath_join)
            inst.register_for_flow_removed(flow_removed)
            setup(inst, False)            
        else:
            setup(inst, True)
            update_application(num_nodes, *args)            
        
    def getInterface(self):
        return str(Update)

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return Update(ctxt)   
    return Factory()
