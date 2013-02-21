# This app just drops to the python interpreter.  Useful for debugging
#

import logging

from nox.lib.core import *
import nox.lib.openflow as openflow
from nox.lib.packet import *
from nox.lib.packet.packet_utils import mac_to_str, ethtype_to_str

logger = logging.getLogger("nox.loadbalancer.lbtest")

class LBTest(Component):

    def learn_and_forward(self, dpid, inport, packet, buf, bufid):
#	logger.info("Learning & Forwarding Packet" + str(packet))

	# Another way to determine packet type
	pkt = packet

	while (True):
	    if (isinstance(pkt, ipv4.ipv4)):
	        logger.info("THIS IS IPv4 PACKET from: " + str(pkt.srcip) + " to: " + str(pkt.dstip))
		break
	
	    if (pkt.next):
	        pkt = pkt.next
	    else:
	        break

	# One way to determine packet type 
#	logger.info('\nETHERNET!!!!' + ethtype_to_str(packet.type))

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
