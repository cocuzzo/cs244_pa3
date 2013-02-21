# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Creates typical ARP requests/response packets
# ==========================================

from nox.lib.packet.arp import arp
from nox.lib.packet.ethernet import ethernet, ETHER_ANY, ETHER_BROADCAST
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int, ipstr_to_int, octstr_to_array, ip_to_str


# ==========================================
# Create ARP Response
# ==========================================

def create_arp_response(packet):
    arpReqHeader = packet.find('arp')

    arpResponse = arp()
    arpResponse.hwdst = arpReqHeader.hwsrc
    arpResponse.protodst = arpReqHeader.protosrc
    arpResponse.hwsrc = arpReqHeader.hwdst
    arpResponse.protosrc = arpReqHeader.protodst
    arpResponse.hwtype = arpReqHeader.HW_TYPE_ETHERNET
    arpResponse.hwlen = 6
    arpResponse.prototype = arpResponse.PROTO_TYPE_IP
    arpResponse.protolen = 4
    arpResponse.opcode = arpResponse.REPLY

    ethResponse = ethernet()
    ethResponse.dst = packet.src
    ethResponse.src = packet.dst
    ethResponse.type = ethernet.ARP_TYPE
    ethResponse.set_payload(arpResponse)

    return ethResponse.tostring()

def create_virtual_arp_response(packet, srcMAC, srcIP):
    arpReqHeader = packet.find('arp')

    arpResponse = arp()
    arpResponse.hwdst = arpReqHeader.hwsrc
    arpResponse.protodst = arpReqHeader.protosrc
    arpResponse.hwsrc = srcMAC
    arpResponse.protosrc = srcIP
    arpResponse.hwtype = arpReqHeader.HW_TYPE_ETHERNET
    arpResponse.hwlen = 6
    arpResponse.prototype = arpResponse.PROTO_TYPE_IP
    arpResponse.protolen = 4
    arpResponse.opcode = arpResponse.REPLY

    ethResponse = ethernet()
    ethResponse.dst = packet.src
    ethResponse.src = srcMAC
    ethResponse.type = ethernet.ARP_TYPE
    ethResponse.set_payload(arpResponse)

    return ethResponse.tostring()

# =========================================
# Create ARP Request
# =========================================

def create_arp_request(srcMAC, srcIP, dstIP):
    arpRequest = arp()
    arpRequest.hwdst = ETHER_ANY
#    arpRequest.hwdst = ETHER_BROADCAST
    arpRequest.protodst = dstIP
    arpRequest.hwsrc = srcMAC
    arpRequest.protosrc = srcIP
    arpRequest.hwtype = arpRequest.HW_TYPE_ETHERNET
    arpRequest.hwlen = 6
    arpRequest.protolen = 4
    arpRequest.opcode = arpRequest.REQUEST

    ethRequest = ethernet()
    ethRequest.dst = ETHER_BROADCAST
    ethRequest.src = srcMAC
    ethRequest.type = ethernet.ARP_TYPE
    ethRequest.set_payload(arpRequest)

    return ethRequest.tostring()
