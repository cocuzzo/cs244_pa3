# This app just drops to the python interpreter.  Useful for debugging
#

import logging

from nox.lib.core import *
import nox.lib.openflow as openflow
from nox.lib.packet import *
from nox.lib.packet.packet_utils import mac_to_str, ethtype_to_str, ip_to_str

logger = logging.getLogger("nox.loadbalancer.lbtest")

class LBTest(Component):

    def get_ippacket(self, packet):
        pkt = packet

        # What is the IP?
        while (True):
            if (isinstance(pkt, ipv4.ipv4)):
		return pkt

            if (pkt.next):
                pkt = pkt.next
	    else:
		return None


    def learn_and_forward(self, dpid, inport, packet, buf, bufid):
	# Flood

	# Find MAC + IP from header
	srcMACaddr = packet.src.tostring()
	ippkt = self.get_ippacket(packet)
	srcIPaddr = '0.0.0.0'
	if (ippkt != None):
	    srcIPaddr = ip_to_str(ippkt.srcip)

	# Does the source MAC + IP need to be learned?
	if (self.mac_to_port.has_key(srcMACaddr)):
	    dstMACaddr = self.mac_to_port[srcMACaddr]
	    if dstMACaddr[0] != inport:
		logger.info('MAC moved from ' + str(dst) + ' to ' + str(inport))
	    elif (dstMACaddr[1] == '0.0.0.0') and (srcIPaddr != None):
		logger.info('IP update')
		self.mac_to_port[srcMACaddr] = (inport, srcIPaddr)
	# If not, update table entry
        else:
	    logger.info('MAC learned ' + mac_to_str(packet.src) + ' on %d %d' % (dpid, inport))
  	    self.mac_to_port[srcMACaddr] = (inport, srcIPaddr)

	# Have we already learned destination MAC + IP?
	dstMACaddr = packet.dst.tostring()
	dstIPaddr = None
	if (ippkt != None):
	    dstIPaddr = ip_to_str(ippkt.dstip)

	logger.info('Sending to destination')

        # Is this server address?
	if ((dstIPaddr != None) and (dstIPaddr == "10.0.0.0")):
	    logger.info('SPECIAL FORWARDING IP\n')
	    for item in self.mac_to_port.items():
		logger.info(str(item) + "\n")
		if (item[1] == "10.0.0.2"):
		    logger.info('Found 10.0.0.2 and sending packet\n');
		    self.send_openflow(dpid, bufid, buf, item[0], inport)
	    	#prt = self.mac_to_port[dstMACaddr] # CHANGE
	    	#self.send_openflow(dpid, bufid, buf, prt[0] ,inport)

	# HARDCODED
	if (isinstance(packet.next, arp.arp) and (ip_to_str(packet.next.protodst) ==  "10.0.0.0")):
            logger.info('SPECIAL FORWARDING ARP\n')
            for item in self.mac_to_port.items():
                logger.info(str(item) + ": " + str(item[1][1]) + "\n")
                if (str(item[1][1]) == '10.0.0.2'):
                    logger.info('Found 10.0.0.2 and sending packet\n');
                    #self.send_openflow(dpid, bufid, buf, item[1][0], inport)

            	    # Install Flow Rule
                    #flow = extract_flow(packet)
                    #flow[core.IN_PORT] = inport
		    #flow = {}
		    #flow[DL_TYPE] = 0x0800
		    #flow[NW_PROTO] = 17
		    #flow[NW_DST] = ippkt.srcip
		    #flow[NW_DST_N_WILD] = 31

                    #actions = [[openflow.OFPAT_OUTPUT, [0, item[1][0]]]]
                    #CACHE_TIMEOUT = 100
                    #self.install_datapath_flow(dpid, flow, CACHE_TIMEOUT,
                    #                   openflow.OFP_FLOW_PERMANENT, actions,
                    #                   bufid, openflow.OFP_DEFAULT_PRIORITY,
                    #                   inport, buf)




	# Otherwise forward appropriately
	elif (self.mac_to_port.has_key(dstMACaddr)):
	    prt = self.mac_to_port[dstMACaddr]
	    #self.send_openflow(dpid, bufid, buf, prt[0] ,inport)

	# If we have not then flood
	else:
	    self.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)

            # Install Flow Rule
            #flow = extract_flow(packet)
            #flow[core.IN_PORT] = inport
            flow = {}
            #flow[DL_TYPE] = 0x0800
            #flow[NW_PROTO] = 17
            #flow[NW_DST] = 
            flow[NW_DST_N_WILD] = 32

            actions = [[openflow.OFPAT_OUTPUT, [0, 1]]]
            CACHE_TIMEOUT = 100
            self.install_datapath_flow(dpid, flow, CACHE_TIMEOUT,
                                       openflow.OFP_FLOW_PERMANENT, actions,
                                       bufid, openflow.OFP_DEFAULT_PRIORITY,
                                       inport, buf)


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
