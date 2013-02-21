
import logging

from nox.lib.core import *
import nox.lib.openflow as openflow
from nox.lib.packet import *
from nox.lib.packet.packet_utils import mac_to_str, ip_to_str, ipstr_to_int

from iptree import *
from ipflowlib import *

logger = logging.getLogger("nox.loadbalancer.lbtest")

class LBTest(Component):

    def arpdstrw_and_forward(self, dpid, inport, packet, buf, bufid):
        logger.info('BUFBF:[' + str(buf) + ']{' + str(packet) + '}\n')

        buf[38] = 10 
        buf[39] = 0
        buf[40] = 0
        buf[41] = 3
        logger.info('BUFAF:[' + str(buf) + ']{' + str(packet) + '}\n')
	self.send_openflow(dpid, None, buf, 1, inport)

    def arpsrcrw_and_forward(self, dpid, inport, packet, buf, bufid):
        logger.info('SUFBF:[' + str(buf) + ']{' + str(packet) + '}\n')
        buf[28] = 10
        buf[29] = 0
        buf[30] = 0
        buf[31] = 5
        logger.info('SUFAF:[' + str(buf) + ']{' + str(packet) + '}\n')
	self.send_openflow(dpid, None, buf, 0, inport)

    def ipdstrw_and_forward(self, dpid, inport, packet, buf, bufid):
	myIPFlowLib = IPFlowLib()
        myIPFlowLib.ipflow_dstrule_install(self, dpid, '10.0.0.5', '10.0.0.3', inport, 1, 100)
#	myIPFlowLib.ipflow_send(self, dpid, buf, 1, inport)
        
    def ipsrcrw_and_forward(self, dpid, inport, packet, buf, bufid):
	myIPFlowLib = IPFlowLib()
	myIPFlowLib.ipflow_srcrule_install(self, dpid, '10.0.0.3', '10.0.0.5', inport, 0, 100)



    def learn_and_forward(self, dpid, inport, packet, buf, bufid):
	logger.info("Learning & Forwarding Packet" + str(packet))

        # Starter psuedocode for learning switch exercise

        if not self.mac_to_port.has_key(dpid):
            self.mac_to_port[dpid] = {}

        #learn the port for the source MAC
	srcaddr = packet.src.tostring()
	if (self.mac_to_port[dpid].has_key(srcaddr)):
	    # If address has already been learned, check if it has moved
	    dst = self.mac_to_port[dpid][srcaddr]
	    if dst[0] != inport:
		logger.info('MAC has moved from ' + str(dst) + 'to' + str(inport))
	else:
	    logger.info('Learned MAC ' + mac_to_str(packet.src) + 'on %d %d' % (dpid, inport))
	    self.mac_to_port[dpid][srcaddr] = (inport, packet)

        #if (destination MAC of the packet is known)
	dstaddr = packet.dst.tostring()
	if (self.mac_to_port[dpid].has_key(dstaddr)):
	    logger.info('Learned Destionation MAC')
	    prt = self.mac_to_port[dpid][dstaddr]

	    #send unicast packet to known output port
	    self.send_openflow(dpid, bufid, buf, prt[0], inport)

	    # push down flow entry
#	    flow = extract_flow(packet)
#	    flow[core.IN_PORT] = inport
#	    actions = [[openflow.OFPAT_OUTPUT, [0, prt[0]]]]
#	    CACHE_TIMEOUT = 5
#	    self.install_datapath_flow(dpid, flow, CACHE_TIMEOUT,
#				       openflow.OFP_FLOW_PERMANENT, actions,
#				       bufid, openflow.OFP_DEFAULT_PRIORITY,
#				       inport, buf)
#
	else:
	    #flood packet out everything but the input port
	    self.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)

    def packet_in_callback(self, dpid, inport, reason, len, bufid, packet):
        IP_TYPE  = 0x0800
        ARP_TYPE = 0x0806 

	if not packet.parsed:
	    logger.debug('Ignoring incomplete packet')

        elif (packet.type == ARP_TYPE):
            if (ip_to_str(packet.next.protodst) == '10.0.0.5'):
                logger.info('THIS IS AN ARP TO 10.0.0.5')
	        self.arpdstrw_and_forward(dpid, inport, packet, packet.arr, bufid)
            elif (ip_to_str(packet.next.protosrc) == '10.0.0.3'):
                logger.info('THIS IS AN ARP FROM 10.0.0.3')
                self.arpsrcrw_and_forward(dpid, inport, packet, packet.arr, bufid)
            else:
	        self.learn_and_forward(dpid, inport, packet, packet.arr, bufid)
        elif (packet.type == IP_TYPE):
            if (ip_to_str(packet.next.dstip) == '10.0.0.5'):
                logger.info('THIS IS IP TO 10.0.0.5')
	        self.ipdstrw_and_forward(dpid, inport, packet, packet.arr, bufid)
            elif (ip_to_str(packet.next.srcip) == '10.0.0.3'):
                logger.info('THIS IS IP FROM 10.0.0.3')
                self.ipsrcrw_and_forward(dpid, inport, packet, packet.arr, bufid)
            else:
	        self.learn_and_forward(dpid, inport, packet, packet.arr, bufid)

	else:
	    self.learn_and_forward(dpid, inport, packet, packet.arr, bufid)
	return CONTINUE


    # ================================================== 
    def __init__(self, ctxt):
        Component.__init__(self, ctxt)
	self.mac_to_port = {}

    def install(self):
	logger.info("installed lbtest module")
        self.register_for_packet_in(self.packet_in_callback)

    def getInterface(self):
        return str(LBTest)

    # ================================================== 


def getFactory():
    class Factory:
        def instance(self, ctxt):
            return LBTest(ctxt)

    return Factory()
