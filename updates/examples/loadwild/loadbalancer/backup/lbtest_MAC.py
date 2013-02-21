# This app just drops to the python interpreter.  Useful for debugging
#

import logging

from nox.lib.core import *
import nox.lib.openflow as openflow
from nox.lib.packet import *
from nox.lib.packet.packet_utils import mac_to_str

logger = logging.getLogger("nox.loadbalancer.lbtest")

class LBTest(Component):

    def learn_and_forward(self, dpid, inport, packet, buf, bufid):
	logger.info("Learning & Forwarding Packet" + str(packet))

        # Starter psuedocode for learning switch exercise

        #learn the port for the source MAC
	srcaddr = packet.src.tostring()
	if (self.mac_to_port.has_key(srcaddr)):
	    # If address has already been learned, check if it has moved
	    dst = self.mac_to_port[srcaddr]
	    if dst[0] != inport:
		logger.info('MAC has moved from ' + str(dst) + 'to' + str(inport))
	else:
	    logger.info('Learned MAC ' + mac_to_str(packet.src) + 'on %d %d' % (dpid, inport))
	    self.mac_to_port[srcaddr] = (inport, packet)

        #if (destination MAC of the packet is known)
	dstaddr = packet.dst.tostring()
	if (self.mac_to_port.has_key(dstaddr)):
	    logger.info('Learned Destionation MAC')
	    prt = self.mac_to_port[dstaddr]

	    #send unicast packet to known output port
	    self.send_openflow(dpid, bufid, buf, prt[0], inport)
	    #self.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)


	    #[later] push down flow entry
	    flow = extract_flow(packet)
	    flow[core.IN_PORT] = inport
	    actions = [[openflow.OFPAT_OUTPUT, [0, prt[0]]]]
	    CACHE_TIMEOUT = 5
	    self.install_datapath_flow(dpid, flow, CACHE_TIMEOUT,
				       openflow.OFP_FLOW_PERMANENT, actions,
				       bufid, openflow.OFP_DEFAULT_PRIORITY,
				       inport, buf)

	else:
	    #flood packet out everything but the input port
	    self.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)

    def packet_in_callback(self, dpid, inport, reason, len, bufid, packet):
	if not packet.parsed:
	    logger.debug('Ignoring incomplete packet')
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
