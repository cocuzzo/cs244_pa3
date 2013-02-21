# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Generates typical (flow, action) pairs
# ==========================================


from nox.lib.core import *
from nox.lib.packet import *
from nox.lib.packet.packet_utils import ipstr_to_int, octstr_to_array

# ======================================
# IP Flow Change SRC
# ======================================

def get_forwarding_srcrule(srcIP, srcMAC, dstMAC, dstIP, outport):
    flow = {}
    flow[DL_TYPE] = 0x0800
    flow[NW_DST] = ipstr_to_int(srcIP)
    defaultActions = [
	      [openflow.OFPAT_OUTPUT, [0, outport]]
	      ]
    rewriteActions = [
              [openflow.OFPAT_SET_DL_SRC, dstMAC],
              [openflow.OFPAT_SET_NW_SRC, ipstr_to_int(dstIP)],
	      [openflow.OFPAT_SET_DL_DST, octstr_to_array(srcMAC)],
              [openflow.OFPAT_OUTPUT, [0, outport]]
              ]
    return (flow, defaultActions, rewriteActions)

# ======================================
# IP Flow Change DST
# ======================================
def get_forwarding_dstrule(srcIP, srcWild, gateIP, dstMAC, dstIP, outport):
    flow = {}
    flow[DL_TYPE] = 0x0800
    flow[NW_SRC] = srcIP
    flow[NW_SRC_N_WILD] = srcWild
    flow[NW_DST] = ipstr_to_int(gateIP)
    defaultActions = [
              [openflow.OFPAT_OUTPUT, [0, outport]]
              ]
    rewriteActions = [
              [openflow.OFPAT_SET_DL_DST, dstMAC],
              [openflow.OFPAT_SET_NW_DST, ipstr_to_int(dstIP)],
              [openflow.OFPAT_OUTPUT, [0, outport]]
              ]

    return (flow, defaultActions, rewriteActions)

def get_microflow_dstrule(packet, dstMAC, dstIP, outport):
    currflow = extract_flow(packet)
    flow = {}
    flow[DL_TYPE] = 0x0800
    flow[NW_SRC] = currflow[NW_SRC]
    flow[NW_DST] = currflow[NW_DST]
    defaultActions = [
              [openflow.OFPAT_OUTPUT, [0, outport]]
              ]
    rewriteActions = [
              [openflow.OFPAT_SET_DL_DST, dstMAC],
              [openflow.OFPAT_SET_NW_DST, ipstr_to_int(dstIP)],
              [openflow.OFPAT_OUTPUT, [0, outport]]
              ]

    return (flow, defaultActions, rewriteActions)


def get_controller_dstrule(srcIP, srcWild, gateIP):
    flow = {}
    flow[DL_TYPE] = 0x0800
    flow[NW_SRC] = srcIP
    flow[NW_SRC_N_WILD] = srcWild
    flow[NW_DST] = ipstr_to_int(gateIP)
    actions = [
              [openflow.OFPAT_OUTPUT, [0, openflow.OFPP_CONTROLLER]]
              ]
    return (flow, actions, actions)

def copyflow(flow):
    newFlow = {}
    if flow.has_key(DL_TYPE):
        newFlow[DL_TYPE] = flow[DL_TYPE]
    if flow.has_key(NW_SRC):
        newFlow[NW_SRC] = flow[NW_SRC]
    if flow.has_key(NW_SRC_N_WILD):
        newFlow[NW_SRC_N_WILD] = flow[NW_SRC_N_WILD]
    if flow.has_key(NW_DST):
        newFlow[NW_DST] = flow[NW_DST]
    if flow.has_key(NW_DST_N_WILD):
        newFlow[NW_DST_N_WILD] = flow[NW_DST_N_WILD]
    return newFlow
