from nox.lib.core import *
import nox.lib.openflow as openflow
from nox.lib.packet.packet_utils import ip_to_str, mac_to_str

from ipflowlib import *
from iptree import *

class IPpartition:

        def __init__(self, Component, Logger):
		""" Init """
		self.myComponent = Component
		self.myLogger = Logger

		self.myIPFlow = IPFlowLib(Component)
		self.myIPTree = IPTree(Logger)
		self.myIPTreeRoot = IPNode(None)

		self.myMacLearningTable = {}

		self.ippart_partition()

	def ippart_partition(self):
		self.myLogger.info('Partitioning:')

		block = self.ippart_bestblock(2)
		self.myIPTree.insert(self.myIPTreeRoot, block)
		self.myIPTree.printIPTree(self.myIPTreeRoot)
		self.myLogger.info('')

                block = self.ippart_bestblock(4)
                self.myIPTree.insert(self.myIPTreeRoot, block)
                self.myIPTree.printIPTree(self.myIPTreeRoot)
                self.myLogger.info('')

                block = self.ippart_bestblock(3)
                self.myIPTree.insert(self.myIPTreeRoot, block)
                self.myIPTree.printIPTree(self.myIPTreeRoot)
                self.myLogger.info('')

                block = self.ippart_bestblock(4)
                self.myIPTree.insert(self.myIPTreeRoot, block)
                self.myIPTree.printIPTree(self.myIPTreeRoot)
                self.myLogger.info('')

		#self.myLogger.info('SWITCH DPID: ' + mac_to_str(0x000102030401))
		#self.ippart_installrule(0x000102030401, '10.0.0.2', '10.0.0.5', '10.0.0.3', 2, 1, 100)

	def ippart_bestblock(self, height):
		blocksList = self.myIPTree.getfree(self.myIPTreeRoot, height)
		bestBlock = ''
		for block in blocksList:
			if len(bestBlock) < len(block):
				bestBlock = block

		if len(bestBlock) != height:
			choicesList = self.myIPTree.listChoices(bestBlock, height)
			bestBlock = choicesList[0]

		return bestBlock

	def ippart_installrule(self, switch, srcIP, maskIP, dstIP, inport, outport, timeout):
		self.myIPFlow.ipflow_dstrule_install(switch, srcIP, maskIP, dstIP, inport, outport, timeout)
		self.myIPFlow.ipflow_srcrule_install(switch, dstIP, maskIP, outport, inport, timeout)

	def ippart_packet_in(self, switch, inport, packet, buf):
		ARP_TYPE = 0x0806

		if packet.type == ARP_TYPE:
			if ip_to_str(packet.next.protodst) == '10.0.0.5':
				self.myLogger.info('TO 10.0.0.5')
				buf[38] = 10
				buf[39] = 0
				buf[40] = 0
				buf[41] = 3
				self.myIPFlow.ipflow_send(switch, buf, 1, inport)
				#self.myIPFlow.ipflow_dstrule_install(switch, '10.0.0.5', '10.0.0.3', inport, 1, 100)
				#self.myIPFlow.ipflow_rule_install(switch, '10.0.0.2', '10.0.0.5', '10.0.0.3', 2, 1, 100)
				self.ippart_installrule(0x000102030401, '10.0.0.2', '10.0.0.5', '10.0.0.3', 2, 1, 100)
			elif ip_to_str(packet.next.protosrc) == '10.0.0.3':
				buf[28] = 10
				buf[29] = 0
				buf[30] = 0
				buf[31] = 5
				self.myIPFlow.ipflow_send(switch, buf, 2, inport)
				#self.myIPFlow.ipflow_srcrule_install(switch, '10.0.0.3', '10.0.0.5', inport, 0, 100)
			else:
				self.myLogger.info('NOT TO 10.0.0.5')
				self.ippart_learnnforward(switch, inport, packet, buf)
		else:
			self.myLogger.info('NOT ARP')
			self.ippart_learnnforward(switch, inport, packet, buf)

	# MAC Learning
	def ippart_learnnforward(self, switch, inport, packet, buf):
		if not self.myMacLearningTable.has_key(switch):
			self.myMacLearningTable[switch] = {}

		# Learn MAC address of incoming packet
		srcaddr = packet.src.tostring()
		if (self.myMacLearningTable[switch].has_key(srcaddr)):
			dst = self.myMacLearningTable[switch][srcaddr]
			if dst != inport:
				self.myLogger.info('MAC Learning: MAC has moved')
		else:
			self.myLogger.info('MAC Learning: Learned MAC')
			self.myMacLearningTable[switch][srcaddr] = inport

		# Forward packet on appropriate port	
		dstaddr = packet.dst.tostring()
		if (self.myMacLearningTable[switch].has_key(dstaddr)):
			self.myLogger.info('MAC Learning: Forwarding to Learned MAC')
			prt = self.myMacLearningTable[switch][dstaddr]

			# Unicast
			self.myIPFlow.ipflow_send(switch, buf, prt, inport)	
		else:
			self.myLogger.info('MAC Learning: Flooding')
			self.myIPFlow.ipflow_send(switch, buf, openflow.OFPP_FLOOD, inport)

