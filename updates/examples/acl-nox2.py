from nox.lib.core import *
from nox.lib.netinet.netinet import datapathid
from nox.lib.packet.ethernet     import ethernet

from twisted.python import log

import logging

logger = logging.getLogger('nox.coreapps.examples.acl-nox')

# TODO Need to re-install rules as they expire, then switch ACLs and install those rules

""" Simple ACL example w/ three filter switches, an ingress and an egress switch. The interior switches filter based on static addresses. Initially, only two switches are used. Then, another switch is brought online and the filter space is rebalanced. The ingress switch should route incoming packets appropriately. """

""" Eventual (awesome) application: give me a simple network wide ACL. I run the topology and automagically place the filtering. As load increases, I automagically adjust the ACL distribution to rebalance. """

def host_to_ip(hostid):
    return "10.0.0." + str(hostid)

class ACL(Component):

    def __init__(self, ctxt):
        global inst
        inst = self
        Component.__init__(self, ctxt)
       

    def install(self):
        inst.register_for_datapath_leave(datapath_leave_callback)
        inst.register_for_datapath_join(datapath_join_callback)
        inst.register_for_packet_in(packet_in_callback)

        # Topology crap
  
    def getInterface(self):
        return str(ACL)



ingress = 1
egress = 2
leftFilter = 10
middleFilter = 11
rightFilter = 12
endHost = 30

host0 = host_to_ip(20)
host1 = host_to_ip(21)
host2 = host_to_ip(22)

ingress_port_map = { host0 : 1,
                    host1 : 2,
                    host2: 9,
                    leftFilter : 3,
                    middleFilter : 4,
                    rightFilter : 5}

port_to_ingress = {leftFilter : 1,
                   middleFilter : 1,
                   rightFilter : 1}

port_to_egress = { leftFilter : 2,
                  middleFilter : 2,
                  rightFilter : 2}

egress_ports = { leftFilter : 1,
                middleFilter : 2,
                rightFilter : 3,
                endHost : 4}

# Screw around w/ topology detection later. For now, hardcode the topo

# Two things we need: ACL and ACL space distribution. These are essentially independent

        
ACList = {host0:True,
       host1:False,
       host2:True}

ACL_dist = {host0:leftFilter,
            host1:leftFilter,
            host2:rightFilter}

# --
# Packet entry method.
# Drop LLDP packets (or we get confused) and attempt learning and
# forwarding
# --
def packet_in_callback(dpid, inport, reason, len, bufid, packet):

    if not packet.parsed:
        log.msg('Ignoring incomplete packet',system='pyswitch')

    # don't forward lldp packets    
    if packet.type == ethernet.LLDP_TYPE:
        return CONTINUE
    else:
        print packet

# --
# Packet entry method.
# Drop LLDP packets (or we get confused) and attempt learning and
# forwarding
# --

def install_ingress(dpid, distribution_map):

    for host,filterSwitch in distribution_map.items():
        forward_output = [[openflow.OFPAT_OUTPUT, [0, ingress_port_map[filterSwitch]]]]
        # return_output = [[openflow.OFPAT_OUTPUT, [0, ingress_port_map[host]]]]
        return_output = [[openflow.OFPAT_OUTPUT, [0, openflow.OFPP_FLOOD]]]
            
        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.IP_TYPE,
                                     core.NW_SRC : host },
                                   # {core.IN_PORT : ingress_port_map[host]},
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    forward_output)

        # Added for ARP
        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.ARP_TYPE,
                                     core.IN_PORT : ingress_port_map[host]},
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    forward_output)

        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.IP_TYPE,
                                     core.NW_DST : host},
                                     # core.IN_PORT : ingress_port_map[filterSwitch]},
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    return_output)
        # Added for ARP
        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.ARP_TYPE,
                                     core.IN_PORT : ingress_port_map[filterSwitch]},
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    return_output)



def install_filter(dpid, access_list):

    egress_port = port_to_egress[dpid]
    ingress_port = port_to_ingress[dpid]
    
    for host,allowed in access_list.items():
        if allowed:
            forward_action = [[openflow.OFPAT_OUTPUT, [0, egress_port]]]
        else:
            forward_action = []
        return_action = [[openflow.OFPAT_OUTPUT, [0, ingress_port]]]
        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.IP_TYPE,
                                     core.NW_SRC : host},
                                     # {core.IN_PORT : ingress_port},
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    forward_action)
        # Added for ARP
        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.ARP_TYPE,
                                     core.IN_PORT : ingress_port},
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    forward_action)
        
        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.IP_TYPE},
                                     # {core.IN_PORT : egress_port },
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    return_action)
        # Added for ARP
        inst.install_datapath_flow(dpid,
                                   { core.DL_TYPE : ethernet.ARP_TYPE,
                                     core.IN_PORT : egress_port },
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    return_action)


def install_egress(dpid, egress_port):

    for host,port in egress_ports.items():
        if host == endHost:
            action = [[openflow.OFPAT_OUTPUT, [0,openflow.OFPP_FLOOD]]]
        else:
            action = [[openflow.OFPAT_OUTPUT, [0,egress_port]]]
        inst.install_datapath_flow(dpid,
                               # { core.DL_TYPE : ethernet.IP_TYPE,
                                 {core.IN_PORT : port},
                                    openflow.OFP_FLOW_PERMANENT,
                                    openflow.OFP_FLOW_PERMANENT,
                                    action)
       
        
def datapath_join_callback(dpid,stats):
    # Install static config

    if dpid == ingress:
        install_ingress(dpid,ACL_dist)
    elif dpid == egress:
        # Do nothing for now
        install_egress(dpid,4)
        pass
    else:
        # One of the filter switches
        install_filter(dpid, ACList)
        
    logger.info('Switch %x has joined the network' % dpid)

    return CONTINUE

def datapath_leave_callback(dpid):
    logger.info('Switch %x has left the network' % dpid)
    
def getFactory():
    class Factory:
        def instance(self, ctxt):
            return ACL(ctxt)
   
    return Factory()
