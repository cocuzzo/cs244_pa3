# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Main function
# ==========================================


import os
import time

from nox.lib.core import *
import nox.lib.openflow as openflow
from array import *
from nox.lib.packet import *
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int, ipstr_to_int, octstr_to_array


# Helper Files
import Arps
import IPs
import Globals
from Multipath import *
from IPTransition import *
from EvalRules import *

class lbtest(Component):

    # ==========================================
    # INIT
    # ==========================================
    def __init__(self, ctxt):
        Component.__init__(self, ctxt)
	self.Init = True
	self.myEvalRules = EvalRules()
	self.Multipath = Multipath(self)
	self.myIPTransition = IPTransition(self, self.Multipath)
	self.myLastAlphaMod = 0
	self.AllMacsFound = False

    # ==========================================
    # Check Alpha Callback
    # ==========================================
    def checkAlphaFile(self):
	lastAlphaMod = os.path.getmtime(Globals.ALPHAFILE)
	if lastAlphaMod > self.myLastAlphaMod:
	    Globals.RULESLOG.write('Alpha File Modification')
	    self.myLastAlphaMod = lastAlphaMod

	    
	
	    rulePairList = self.myEvalRules.updateAlphas()
	    self.myIPTransition.installRules(rulePairList)
	self.post_callback(2, self.checkAlphaFile)

    # ==========================================
    # Packet In Callback
    # ==========================================
    def packet_in_callback(self, dpid, inport, reason, len, bufid, packet):

        # Install initial setup forwarding rules
	if self.Init == True:
	    self.post_callback(Globals.PORT_STATS_PERIOD, lambda : self.port_timer())
	    self.Init = False

        # Controller Attention
	if reason == openflow.OFPR_ACTION:
	    self.myIPTransition.controllerAction(packet)

	# Incoming ARPs
	elif packet.type == Globals.ARP_TYPE:

	    # Response to our ARP requests 
	    # 1. Record MAC 
	    # 2. Install appropriate IP Forwarding Rule: Change dest VIP to dest Replica i
            if packet.dst == octstr_to_array(Globals.VMAC):
	        foundMacs = True
                for i in range(0, Globals.NUMREPLICAS):
	            if ((packet.next.protosrc == ipstr_to_int(Globals.REPLICAS[i]['ip'])) and (Globals.REPLICAS[i]['mac'] != mac_to_str(packet.src))):
		        Globals.REPLICAS[i]['mac'] = mac_to_str(packet.src)
			Globals.REPLICAS[i]['port'] = inport

			for j, switchJ in enumerate(Globals.SWITCHES):
			    if switchJ['mac'] == dpid:
				switchJ['replicas'].append(Globals.REPLICAS[i]['no'])

		    if (Globals.REPLICAS[i]['mac'] == ''):
		        foundMacs = False

	        if foundMacs == True and self.AllMacsFound == False:
		    Globals.log.info('REPLICAS ' + str(Globals.REPLICAS))
		    Globals.log.info('SWITCHES ' + str(Globals.SWITCHES))
		    Globals.log.info('\n')
		    Globals.log.info('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
		    rulePairList = self.myEvalRules.updateAlphas()
		    self.myIPTransition.installRules(rulePairList)
		    Globals.log.info('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
		    Globals.log.info('\n')
		    self.AllMacsFound = True

    	    # Requests for VIP respond with ARP Response
   	    elif packet.next.protodst == ipstr_to_int(Globals.VIP):
		srcIP = ip_to_str(packet.next.protosrc)
	
		# IP Rules
		(flow, defaultActions, rewriteActions) = IPs.get_forwarding_srcrule(srcIP, mac_to_str(packet.src), Globals.VMAC, Globals.VIP, inport)
		self.Multipath.install_microflow_flow(flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY, 0, None, dpid, inport, rewriteActions)

	        arpResponse = Arps.create_virtual_arp_response(packet, octstr_to_array(Globals.VMAC), ipstr_to_int(Globals.VIP))
                self.Multipath.send(dpid, None, arpResponse, [[openflow.OFPAT_OUTPUT, [0, inport]]], openflow.OFPP_CONTROLLER)

	    else:
		arpResponse = Arps.create_arp_response(packet)
		self.Multipath.send(dpid, None, arpResponse, [[openflow.OFPAT_OUTPUT, [0, inport]]], openflow.OFPP_CONTROLLER)

        elif packet.type == Globals.IP_TYPE:
	    Globals.log.info("Warning! S1 SHOULD NOT BE RECEIVING IP Traffic!!!")
#	    self.myIPTransition.controllerAction(packet)

        return CONTINUE


    # =======================================
    # ARP Request Replicas to retrieve MACs
    # =======================================
    def arpRequestReplicas(self):
	for i in range(0, Globals.NUMREPLICAS):
	    if Globals.REPLICAS[i]['mac'] == '':
		arpRequest = Arps.create_arp_request(octstr_to_array(Globals.VMAC), ipstr_to_int(Globals.VIP), ipstr_to_int(Globals.REPLICAS[i]['ip']))
		self.Multipath.flood(None, arpRequest, openflow.OFPP_FLOOD, openflow.OFPP_CONTROLLER)
		
	self.post_callback(5, self.arpRequestReplicas)

    # =======================================
    # Install Events
    # =======================================

    def install(self):
        self.register_for_packet_in(self.packet_in_callback)
	self.post_callback(3, self.arpRequestReplicas)
	self.post_callback(5, self.checkAlphaFile)
	self.register_for_port_stats_in(self.port_stats_in_handler)
    
    def getInterface(self):
        return str(lbtest)


    # =======================================
    # Port Stats
    # =======================================
    def port_stats_in_handler(self, dpid, ports):
	for port, info in enumerate(ports):
	    timer = str(time.time())
	    portno = str(ports[port]['port_no'])
	    rxpackets = str(ports[port]['rx_packets'])
	    rxbytes = str(ports[port]['rx_bytes'])
	    txpackets = str(ports[port]['tx_packets'])
	    txbytes = str(ports[port]['tx_bytes'])
	    Globals.STATSFILE.write(portno + ':' + rxpackets + ':' + rxbytes + ':' + txpackets + ':' + txbytes + ':' + timer + '\n')

    def port_timer(self):
	self.ctxt.send_port_stats_request(Globals.SWITCHES[0]['mac'])
	self.post_callback(Globals.PORT_STATS_PERIOD, lambda : self.port_timer())

# ===================================
# Factory
# ===================================

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return lbtest(ctxt)

    return Factory()

