# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Main function
# ==========================================


import os

from nox.lib import openflow
from nox.lib.core import *
from nox.lib.openflow import ofp_match
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int, ipstr_to_int, octstr_to_array, ip_to_str

import Globals
import EvalRules
import IPTransition
import Multipath
import Arps
import Stats
import IPs

class lbtest(Component):

    # =======================================
    # Core Pieces
    # =======================================

    def install(self):
        self.register_for_packet_in(self.packet_in_callback)
#	self.post_callback(Globals.ALPHA_CHECK_PERIOD, self.alphaFileUpdate)
	self.post_callback(6, self.alphaFileUpdate)
        self.post_callback(2, self.arpRequestReplicas)

        self.post_callback(Globals.PORT_STATS_PERIOD, lambda : self.counterTimer())
        self.register_for_port_stats_in(self.calcCounters)
#        self.register_for_aggregate_stats_in(self.calcCounters)
        

    def getInterface(self):
        return str(lbtest)

    def __init__(self, ctxt):
        Component.__init__(self, ctxt)
        Globals.COMPONENT = self

	Multipath.calcForwardingTable()

    # ==========================================
    # Packet In Callback
    # ==========================================
    def packet_in_callback(self, dpid, inport, reason, len, bufid, packet):
        if packet.type == Globals.ARP_TYPE:
	    # ARP Response from replicas for our ARP Requests
            if packet.dst == octstr_to_array(Globals.VMAC):
                self.foundMac(dpid, mac_to_str(packet.src), ip_to_str(packet.next.protosrc), inport)
	    # Request for VIP, respond with ARP Response
            elif packet.next.protodst == ipstr_to_int(Globals.VIP):
		Globals.STATSLOG.write(mac_to_str(dpid) + ' received ' + ip_to_str(packet.next.protosrc) + '\n')
                srcIP = ip_to_str(packet.next.protosrc)
		# Install Rewrite Rules
                (flow, defaultActions, rewriteActions) = IPs.get_forwarding_srcrule(srcIP, mac_to_str(packet.src), Globals.VMAC, Globals.VIP, inport)
                Multipath.install_microflow_flow(flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY + 20, 0, None, dpid, inport, rewriteActions)
		# Response
                arpResponse = Arps.create_virtual_arp_response(packet, octstr_to_array(Globals.VMAC), ipstr_to_int(Globals.VIP))
                Multipath.send(dpid, None, arpResponse, [[openflow.OFPAT_OUTPUT, [0, inport]]], openflow.OFPP_CONTROLLER)
                ip = ip_to_str(packet.next.protosrc)
                for i, switchJ in enumerate(Globals.SWITCHES):
                    if switchJ['mac'] == dpid:
                        found = False
			for i, client in enumerate(switchJ['clients']):
			    if client['ip'] == ip:
 				found = True
			if not found:
   			    Globals.STATSLOG.write(mac_to_str(dpid) + ' found ' + ip + '\n')
                            switchJ['clients'].append({'port': inport, 'ip': ip, 'oldCount': 0L, 'newCount': 0L, 'avg': 0L})
            elif packet.src != octstr_to_array(Globals.VMAC):
		Globals.STATSLOG.write(mac_to_str(dpid) + ' received REQ ' + ip_to_str(packet.next.protosrc) + '\n')
                arpResponse = Arps.create_arp_response(packet)
                Multipath.send(dpid, None, arpResponse, [[openflow.OFPAT_OUTPUT, [0, inport]]], openflow.OFPP_CONTROLLER)
	elif packet.type == Globals.IP_TYPE:
            if reason == openflow.OFPR_ACTION:
                IPTransition.handleControllerAction(packet)

#            else:
#                Multipath.send(dpid, None, packet.arr, openflow.OFPP_FLOOD, inport)
#        else:
#            Multipath.send(dpid, None, packet.arr, openflow.OFPP_FLOOD, inport)

    # ===================================
    # Alpha File Update
    # ===================================
    def alphaFileUpdate(self):
        lastAlphaMod = os.path.getmtime(Globals.ALPHAFILE)
        if lastAlphaMod > Globals.LASTALPHAMOD or Globals.MACREPLICAUPDATE or Globals.STATSUPDATE:
            Globals.log.info("New Alpha File Update")
            Globals.LASTALPHAMOD = lastAlphaMod 

            Globals.printNewPeriod()
            Globals.PERIOD += 1
            rulePairList = EvalRules.updateAlphas()
            IPTransition.handleRules(rulePairList)
            IPTransition.printTargetInstallPairs(Globals.TARGETRULES, Globals.INSTALLEDRULES, Globals.TRANSITRULES)
	    Globals.MACREPLICAUPDATE = False
            Globals.STATSUPDATE = False
            
            Globals.log.info("Done Alpha File Update")
        self.post_callback(Globals.ALPHA_CHECK_PERIOD, self.alphaFileUpdate)

    # =======================================
    # ARP Request Replicas to retrieve MACs
    # =======================================
    def arpRequestReplicas(self):
        for i in range(0, Globals.NUMREPLICAS):
            if Globals.REPLICAS[i]['mac'] == '':
                Globals.log.info("Issuing ARP Request for " + Globals.REPLICAS[i]['ip'])
                arpRequest = Arps.create_arp_request(octstr_to_array(Globals.VMAC), ipstr_to_int(Globals.VIP), ipstr_to_int(Globals.REPLICAS[i]['ip']))
                Multipath.flood(None, arpRequest, openflow.OFPP_FLOOD, openflow.OFPP_CONTROLLER)

        self.post_callback(5, self.arpRequestReplicas)

    def foundMac(self, switchNum, mac, ip, inport):
        for i in range(0, Globals.NUMREPLICAS):
            if (ip == Globals.REPLICAS[i]['ip']) and Globals.REPLICAS[i]['mac'] == '':
                Globals.REPLICAS[i]['mac'] = mac
                Globals.REPLICAS[i]['port'] = inport
  
                for j, switchJ in enumerate(Globals.SWITCHES):
                    if switchJ['mac'] == switchNum:
                        Globals.log.info('Discovered MAC of replica w/IP: ' + ip + ' at switch # ' + str(switchJ['no']))
                        switchJ['replicas'].append(Globals.REPLICAS[i]['no'])
			flow = {}
			flow[DL_TYPE] = 0x0800
                        flow[NW_DST] = ipstr_to_int(ip)
                        actions = [[openflow.OFPAT_OUTPUT, [0, inport]]]
			Globals.COMPONENT.install_datapath_flow(switchNum, flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, openflow.OFP_DEFAULT_PRIORITY + 10, openflow.OFPP_CONTROLLER, None)
                Globals.MACREPLICAUPDATE = True

    # =======================================
    # Recalculate Counters
    # =======================================
    def calcCounters(self, dpid, ports):
	Globals.STATSLOG.write(' ====== Update Stats ====== \n')
        Stats.updateInstalledCounters(dpid, ports)
	Stats.updatePathCounters(dpid, ports)
#        Stats.updateInstallTable()
#        Stats.printStats()
        Globals.STATSUPDATE = True

    def counterTimer(self):
        Globals.log.info('Stats Request')
        for i, switch in enumerate(Globals.SWITCHES):
	     # This would work if we could measure flow stats
#            for j, rule in enumerate(Globals.INSTALLEDRULES):
#                self.ctxt.send_port_stats_request(switch['mac'])
            self.ctxt.send_port_stats_request(switch['mac'])
        Stats.updateInstallTable()
        Stats.printStats()
        self.post_callback(Globals.PORT_STATS_PERIOD, lambda : self.counterTimer()) 


# ===================================
# Factory
# ===================================

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return lbtest(ctxt)

    return Factory()

