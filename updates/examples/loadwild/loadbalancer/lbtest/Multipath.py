import Globals
import IPs
import random

from nox.lib.core import *
from nox.lib.packet import *

import nox.lib.openflow as openflow
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int, ipstr_to_int, octstr_to_array, ip_to_str


INFINITE = 100
HOPCOST = 1


def calcForwardingTable():
    SetAllNodes = []

    # Initialize
    for i, switchI in enumerate(Globals.SWITCHES):
        switchINum = switchI['no']
        Globals.FORWARDINGTABLE[switchINum] = {}
        SetAllNodes.append({'switch': switchINum, 'cost': INFINITE})

        for j, switchJ in enumerate(Globals.SWITCHES):
            switchJNum = switchJ['no']
            if (switchINum == switchJNum):
                Globals.FORWARDINGTABLE[switchINum][switchJNum] = {'cost': 0, 'prevhop': 0}
	    else:
	        Globals.FORWARDINGTABLE[switchINum][switchJNum] = {'cost': INFINITE, 'prevhop': 0}

    # Dijkstra
    for i, switchI in enumerate(Globals.SWITCHES):
        switchINum = switchI['no']
        UnoptimizedNodes = list(SetAllNodes)
        UnoptimizedNodes.remove({'switch': switchINum, 'cost': INFINITE})
        UnoptimizedNodes.append({'switch': switchINum, 'cost': 0})
	    
        while (UnoptimizedNodes != []):
 	    # Next Lowest Cost
   	    currentNode = UnoptimizedNodes[0]
	    for node in UnoptimizedNodes:
	        if node['cost'] < currentNode['cost']:
		    currentNode = node
  	    UnoptimizedNodes.remove(currentNode)

	    if currentNode['cost'] == INFINITE:
	        break

            currentNeighbors = getNeighbors(currentNode['switch'])

	    for neighbor in currentNeighbors:
	        oldCost = Globals.FORWARDINGTABLE[switchINum][neighbor['no']]['cost']
	        alternateCost = currentNode['cost'] + HOPCOST # TODO Modify HOP COST
	        alternatePair = {'switch': neighbor['no'], 'cost': oldCost}

                if alternateCost < oldCost and alternatePair in UnoptimizedNodes:
	  	    UnoptimizedNodes.remove(alternatePair)
		    Globals.FORWARDINGTABLE[switchINum][neighbor['no']]['cost'] = alternateCost
		    Globals.FORWARDINGTABLE[switchINum][neighbor['no']]['prevhop'] = currentNode['switch']
		    UnoptimizedNodes.append({'switch': neighbor['no'], 'cost': alternateCost})

    printTable(Globals.FORWARDINGTABLE)

#	shortestPath = self.getShortestPath(1, 4)
#	print 'Shortest Path: ' + str(shortestPath)
#	allPaths = self.getAllPaths(4)
#	print 'All Paths: ' + str(allPaths)

def printTable(table):
    # Print Result
    for i, switchI in enumerate(Globals.SWITCHES):
        switchINum = switchI['no']
	Globals.RULESLOG.write('\tTable: [' + str(switchINum) + ']\n')
#        Globals.log.info('\tTable: [' + str(switchINum) + ']')
        for j, switchJ in enumerate(Globals.SWITCHES):
            switchJNum = switchJ['no']
	    Globals.RULESLOG.write(str(Globals.FORWARDINGTABLE[switchINum][switchJNum]) + '\n')
#            Globals.log.info(str(Globals.FORWARDINGTABLE[switchINum][switchJNum]))

def getShortestPath(srcNum, dstNum):
    shortestPath = []
    currNode = dstNum
    while (currNode != srcNum):
        shortestPath.insert(0, currNode)
        currNode = Globals.FORWARDINGTABLE[srcNum][currNode]['prevhop']
    shortestPath.insert(0, srcNum)
    return shortestPath
	   
def getAllPaths(srcNum):
    Visited = {}
    VisitQueue = [srcNum]
    OrderedPath = [srcNum]

    while VisitQueue != []:
        currNode = VisitQueue.pop()
        Visited[currNode] = []
	    
        for i, switchI in enumerate(Globals.SWITCHES):
   	    prevNode = Globals.FORWARDINGTABLE[srcNum][switchI['no']]
	    if prevNode['prevhop'] == currNode and (not switchI['no'] in Visited):
	        VisitQueue.append(switchI['no'])
	        OrderedPath.append(switchI['no'])

    OrderedPath.reverse()
    return OrderedPath

def getMultipaths(srcNum):
    orderedPaths = getAllPaths(srcNum)
    orderedMultipaths = []

    for currSwitchNum in orderedPaths:
        currMac = getMac(currSwitchNum)
	currInstall = {'mac': currMac, 'no': currSwitchNum, 'nexthops': []}
	if Globals.ENABLE_MULTIPATH:
            for i, switch in enumerate(Globals.SWITCHES):
                if switch['mac'] == currMac:
                    for j, neighbor in enumerate(switch['neighbors']):
                        if orderedPaths.index(neighbor['no']) > orderedPaths.index(currSwitchNum):
		   	    currInstall['nexthops'].append(neighbor['no'])
	else:
	    currInstall['nexthops'].append(Globals.FORWARDINGTABLE[srcNum][currSwitchNum]['prevhop'])
	orderedMultipaths.append(currInstall)

    return orderedMultipaths

def findReplicasSwitch(replicaNum):
    for i, switchI in enumerate(Globals.SWITCHES):
        for replica in switchI['replicas']:
	    if replica == replicaNum:
	        return switchI['no']

def findMacSwitch(switchMac):
    for i, switchI in enumerate(Globals.SWITCHES):
        if switchI['mac'] == switchMac:
  	    return switchI['no']

def getMac(switchNum):
    for i, switchI in enumerate(Globals.SWITCHES):
        if switchI['no'] == switchNum:
	    return switchI['mac']
    return None

def getNeighbors(switchNum):
    for i, switchI in enumerate(Globals.SWITCHES):
        if switchI['no'] == switchNum:
            return switchI['neighbors']
    return None

def setReplicaOutPort(actions, destSwitchNum, currSwitchNum, nextHopNum, replicaNum):
    newActions = []
    # If nexthop is a switch
#    nextHopNum = Globals.FORWARDINGTABLE[destSwitchNum][currSwitchNum]['prevhop']

    outport = 0
    # If nexthop is a replica
    if nextHopNum == 0:
        for i, replicaI in enumerate(Globals.REPLICAS):
  	    if replicaI['no'] == replicaNum:
	        outport = replicaI['port']
    else:
        for neighbor in getNeighbors(currSwitchNum):
            if neighbor['no'] == nextHopNum:
  	        outport = neighbor['port']

    for action in actions:
        if action[0] == openflow.OFPAT_OUTPUT:
  	    newActions.append([openflow.OFPAT_OUTPUT, [0, outport]])
        else:
            newActions.append(action)

    return newActions

def setMicroflowOutPort(actions, destSwitchNum, currSwitchNum, port):
    newActions = []
    # If nexthop is a switch
    nextHopNum = Globals.FORWARDINGTABLE[destSwitchNum][currSwitchNum]['prevhop']

    outport = 0
    # If nexthop is a replica
    if nextHopNum == 0:
        outport = port
    else:
        for neighbor in getNeighbors(currSwitchNum):
            if neighbor['no'] == nextHopNum:
                outport = neighbor['port']

    for action in actions:
        if action[0] == openflow.OFPAT_OUTPUT:
            newActions.append([openflow.OFPAT_OUTPUT, [0, outport]])
        else:
            newActions.append(action)

    return newActions

def getMultiFlow(flow, numRules):
    numBits = 0
    found = False

    while numRules > 1:
        numBits += 1
        if numRules % 2 != 0:
	    found = True
        numRules = numRules / 2
    
    if found:
	numBits += 1

    if not flow.has_key(NW_SRC_N_WILD):
        return [flow]

    flowList = []
    for i in range(0, 2 ** numBits):
	newFlow = IPs.copyflow(flow)
	numWild = newFlow[NW_SRC_N_WILD] - numBits
        newFlow[NW_SRC] = ((newFlow[NW_SRC] >> numWild) + i) << numWild
        newFlow[NW_SRC_N_WILD] = numWild
	flowList.append(newFlow)
    return flowList


def install_replica_flow(flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet, replicaNum, rewriteActions):
    switchNum = findReplicasSwitch(replicaNum)
    orderMultipaths = getMultipaths(switchNum)
    Globals.log.info("Order Multipaths")
    Globals.log.info(str(orderMultipaths))
    for currNode in orderMultipaths:
        currSwitchNum = currNode['no']
	currMac = currNode['mac']
	if flow.has_key(NW_SRC_N_WILD):
	    flowList = getMultiFlow(flow, len(currNode['nexthops']))
            for i, miniFlow in enumerate(flowList):
                if switchNum == currSwitchNum:
		    nextHop = 0
      	            actions = setReplicaOutPort(rewriteActions, switchNum, currSwitchNum, nextHop, replicaNum)
                else:
	            nextHop = currNode['nexthops'][i % len(currNode['nexthops'])]
    	            actions = setReplicaOutPort(actions, switchNum, currSwitchNum, nextHop, replicaNum)
	        Globals.COMPONENT.install_datapath_flow(currMac, miniFlow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)
	        Globals.RULESLOG.write(mac_to_str(currMac) + " Install Multipath @ " + str(currSwitchNum) + " to dest " + str(switchNum) + ' ' + ip_to_str(miniFlow[NW_SRC]) + '/' + str(miniFlow[NW_SRC_N_WILD]) + '\n')
	else:
	    if switchNum == currSwitchNum:
		nextHop = 0
		actions = setReplicaOutPort(rewriteActions, switchNum, currSwitchNum, nextHop, replicaNum)
	    else:
		nextHopIndex = random.randint(0, len(currNode['nexthops']) - 1)
		nextHop = currNode['nexthops'][nextHopIndex]
#		nextHop = Globals.FORWARDINGTABLE[switchNum][currSwitchNum]['prevhop']
		actions = setReplicaOutPort(actions, switchNum, currSwitchNum, nextHop, replicaNum)
	    Globals.COMPONENT.install_datapath_flow(currMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)
	    Globals.RULESLOG.write(mac_to_str(currMac) + " Install Multipath @ " + str(currSwitchNum) + " to dest " + str(switchNum) + ' ' + ip_to_str(flow[NW_SRC]) + '\n')
    Globals.RULESLOG.write('Install Wildcard: ' + ip_to_str(flow[NW_SRC]) + '\n')

def install_controller_flow(flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet, replicaNum, rewriteActions):
    switchNum = findReplicasSwitch(replicaNum)
    orderInstall = getAllPaths(switchNum)
    for currSwitchNum in orderInstall:
        currMac = getMac(currSwitchNum)
#        Globals.log.info('Install Controller Flow: ' + str(flow) + ' at ' + str(currSwitchNum))
        Globals.COMPONENT.install_datapath_flow(currMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)
    Globals.RULESLOG.write('Install Controller: ' + ip_to_str(flow[NW_SRC]) + str(flow[NW_SRC_N_WILD]) + '\n')


def install_microflow_flow(flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet, switchMac, outport, rewriteActions):
    switchNum = findMacSwitch(switchMac)
    orderInstall = getAllPaths(switchNum)
#    Globals.log.info('Order of Install ' + str(orderInstall))
    for currSwitchNum in orderInstall:
        currMac = getMac(currSwitchNum)
	Globals.RULESLOG.write('Switch: ' + str(currSwitchNum) + '\n')
	if currMac == switchMac:
	    actions = setMicroflowOutPort(rewriteActions, switchNum, currSwitchNum, outport)
	else:
	    actions = setMicroflowOutPort(actions, switchNum, currSwitchNum, outport)
#	Globals.log.info('Install Microflow Flow: ' + str(flow) + ' at ' + str(currSwitchNum))
	Globals.COMPONENT.install_datapath_flow(currMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)
    if flow.has_key(NW_SRC):
        Globals.RULESLOG.write('Install Microflow SRC: ' + ip_to_str(flow[NW_SRC]) + '\n')
    if flow.has_key(NW_DST):
        Globals.RULESLOG.write('Install Microflow DST: ' + ip_to_str(flow[NW_DST]) + '\n')

def delete_flow(flow, replicaNum):
    switchNum = findReplicasSwitch(replicaNum)
    deleteMultipaths = getMultipaths(switchNum)
    for currNode in deleteMultipaths:
        currSwitchNum = currNode['no']
        currMac = currNode['mac']
        flowList = getMultiFlow(flow, len(currNode['nexthops']))
        for i, miniFlow in enumerate(flowList):
            Globals.COMPONENT.delete_strict_datapath_flow(currMac, miniFlow)
	    if not flow.has_key(NW_SRC_N_WILD):
	        Globals.RULESLOG.write(mac_to_str(currMac) + " Delete Multipath @ " + str(currSwitchNum) + " to dest " + str(switchNum) + ' ' + ip_to_str(flow[NW_SRC]) + '\n')
	    else:
	        Globals.RULESLOG.write(mac_to_str(currMac) + " Delete Multipath @ " + str(currSwitchNum) + " to dest " + str(switchNum) + ' ' + ip_to_str(flow[NW_SRC]) + '/' + str(flow[NW_SRC_N_WILD]) + '\n')

#    orderDelete = getAllPaths(switchNum)
#    for switch in orderDelete:
#        currMac = getMac(switch)
#        Globals.log.info('Delete Flow: ' + str(flow) + ' at ' + str(switch))
#        Globals.COMPONENT.delete_strict_datapath_flow(currMac, flow)
    Globals.RULESLOG.write('Delete: ' + ip_to_str(flow[NW_SRC]) + '/' + str(flow[NW_SRC_N_WILD]) + '\n')


def flood(bufid, packet, actions, inport):
    for i, switchI in enumerate(Globals.SWITCHES):
        Globals.COMPONENT.send_openflow(switchI['mac'], bufid, packet, actions, inport)
    Globals.RULESLOG.write('Flood: ' + '\n')

def send(switchMac, bufid, packet, actions, inport):
#    Globals.RULESLOG.write('Send ' +   '\n')
    Globals.COMPONENT.send_openflow(switchMac, bufid, packet, actions, inport)


