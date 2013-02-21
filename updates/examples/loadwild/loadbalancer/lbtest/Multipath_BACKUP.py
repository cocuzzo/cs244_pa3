import Globals
import nox.lib.openflow as openflow

INFINITE = 100
HOPCOST = 1

class Multipath:
    def __init__(self, Component):
	self.Component = Component
	self.ForwardingTable = {}
        SetAllNodes = []

	# Initialize
        for i, switchI in enumerate(Globals.SWITCHES):
            switchINum = switchI['no']
	    self.ForwardingTable[switchINum] = {}
	    SetAllNodes.append({'switch': switchINum, 'cost':INFINITE})

	    for j, switchJ in enumerate(Globals.SWITCHES):
	        switchJNum = switchJ['no']
		if (switchINum == switchJNum):
		    self.ForwardingTable[switchINum][switchJNum] = {'cost': 0, 'prevhop': 0}
		else:
		    self.ForwardingTable[switchINum][switchJNum] = {'cost': INFINITE, 'prevhop': 0}

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

                currentNeighbors = self.getNeighbors(currentNode['switch'])

		for neighbor in currentNeighbors:
		    oldCost = self.ForwardingTable[switchINum][neighbor['no']]['cost']
		    alternateCost = currentNode['cost'] + HOPCOST
		    alternatePair = {'switch': neighbor['no'], 'cost': oldCost}

                    if alternateCost < oldCost and alternatePair in UnoptimizedNodes:
			UnoptimizedNodes.remove(alternatePair)
			self.ForwardingTable[switchINum][neighbor['no']]['cost'] = alternateCost
			self.ForwardingTable[switchINum][neighbor['no']]['prevhop'] = currentNode['switch']
			UnoptimizedNodes.append({'switch': neighbor['no'], 'cost': alternateCost})

        self.printTable()

#	shortestPath = self.getShortestPath(1, 4)
#	print 'Shortest Path: ' + str(shortestPath)
#	allPaths = self.getAllPaths(4)
#	print 'All Paths: ' + str(allPaths)

    def printTable(self):
        # Print Result
        for i, switchI in enumerate(Globals.SWITCHES):
            switchINum = switchI['no']
            Globals.log.info('\tTable: [' + str(switchINum) + ']')
            for j, switchJ in enumerate(Globals.SWITCHES):
                switchJNum = switchJ['no']
                Globals.log.info(str(self.ForwardingTable[switchINum][switchJNum]))

    def getShortestPath(self, srcNum, dstNum):
	shortestPath = []
	currNode = dstNum
	while (currNode != srcNum):
	    shortestPath.insert(0, currNode)
	    currNode = self.ForwardingTable[srcNum][currNode]['prevhop']
	shortestPath.insert(0, srcNum)
	return shortestPath
	   
    def getAllPaths(self, srcNum):
	Visited = {}
	VisitQueue = [srcNum]
	OrderedPath = [srcNum]

	while VisitQueue != []:
	    currNode = VisitQueue.pop()
	    Visited[currNode] = []
	    
	    for i, switchI in enumerate(Globals.SWITCHES):
		prevNode = self.ForwardingTable[srcNum][switchI['no']]
	        if prevNode['prevhop'] == currNode and (not switchI['no'] in Visited):
		    VisitQueue.append(switchI['no'])
		    OrderedPath.append(switchI['no'])

	return OrderedPath	    

    def findReplicasSwitch(self, replicaNum):
	for i, switchI in enumerate(Globals.SWITCHES):
	    for replica in switchI['replicas']:
		if replica == replicaNum:
		    return switchI['no']

    def findMacSwitch(self, switchMac):
	for i, switchI in enumerate(Globals.SWITCHES):
	    if switchI['mac'] == switchMac:
		return switchI['no']

    def getMac(self, switchNum):
	for i, switchI in enumerate(Globals.SWITCHES):
	    if switchI['no'] == switchNum:
		return switchI['mac']
	return None

    def getNeighbors(self, switchNum):
	for i, switchI in enumerate(Globals.SWITCHES):
	    if switchI['no'] == switchNum:
	        return switchI['neighbors']
	return None

    def setReplicaOutPort(self, actions, destSwitchNum, currSwitchNum, replicaNum):
	newActions = []
	# If nexthop is a switch
	nextHopNum = self.ForwardingTable[destSwitchNum][currSwitchNum]['prevhop']

	outport = 0
	# If nexthop is a replica
	if nextHopNum == 0:
	    for i, replicaI in enumerate(Globals.REPLICAS):
		if replicaI['no'] == replicaNum:
		    outport = replicaI['port']
	else:
	    for neighbor in self.getNeighbors(currSwitchNum):
	        if neighbor['no'] == nextHopNum:
		    outport = neighbor['port']

	for action in actions:
	    if action[0] == openflow.OFPAT_OUTPUT:
		newActions.append([openflow.OFPAT_OUTPUT, [0, outport]])
	    else:
	        newActions.append(action)

	return newActions

    def setMicroflowOutPort(self, actions, destSwitchNum, currSwitchNum, port):
        newActions = []
        # If nexthop is a switch
        nextHopNum = self.ForwardingTable[destSwitchNum][currSwitchNum]['prevhop']

        outport = 0
        # If nexthop is a replica
        if nextHopNum == 0:
	    outport = port
        else:
            for neighbor in self.getNeighbors(currSwitchNum):
                if neighbor['no'] == nextHopNum:
                    outport = neighbor['port']

        for action in actions:
            if action[0] == openflow.OFPAT_OUTPUT:
                newActions.append([openflow.OFPAT_OUTPUT, [0, outport]])
            else:
                newActions.append(action)

        return newActions


    def install_replica_flow(self, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet, replicaNum, rewriteActions):
	switchNum = self.findReplicasSwitch(replicaNum)
	orderInstall = self.getAllPaths(switchNum)
	orderInstall.reverse()
	Globals.log.info('Order of Install ' + str(orderInstall))
	for currSwitchNum in orderInstall:
	    currMac = self.getMac(currSwitchNum)
	    if switchNum == currSwitchNum:
		actions = self.setReplicaOutPort(rewriteActions, switchNum, currSwitchNum, replicaNum)
	    else:
	        actions = self.setReplicaOutPort(actions, switchNum, currSwitchNum, replicaNum)
	    Globals.log.info('Install Datapath Flow: ' + str(flow) + ' at ' + str(currSwitchNum))
	    self.Component.install_datapath_flow(currMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)

    def install_controller_flow(self, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet, replicaNum, rewriteActions):
        switchNum = self.findReplicasSwitch(replicaNum)
        orderInstall = self.getAllPaths(switchNum)
        orderInstall.reverse()
	Globals.log.info('Order of Install ' + str(orderInstall))
        for currSwitchNum in orderInstall:
            currMac = self.getMac(currSwitchNum)
	    Globals.log.info('Install Controller Flow: ' + str(flow) + ' at ' + str(currSwitchNum))
            self.Component.install_datapath_flow(currMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)


    def install_microflow_flow(self, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet, switchMac, outport, rewriteActions):
	switchNum = self.findMacSwitch(switchMac)
	orderInstall = self.getAllPaths(switchNum)
	orderInstall.reverse()
	Globals.log.info('Order of Install ' + str(orderInstall))
	for currSwitchNum in orderInstall:
	    currMac = self.getMac(currSwitchNum)
	    if currMac == switchMac:
	        actions = self.setMicroflowOutPort(rewriteActions, switchNum, currSwitchNum, outport)
	    else:
	        actions = self.setMicroflowOutPort(actions, switchNum, currSwitchNum, outport)
	    Globals.log.info('Install Microflow Flow: ' + str(flow) + ' at ' + str(currSwitchNum))
	    self.Component.install_datapath_flow(currMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)

    def install_flow_switch(self, switchMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet):
	self.Component.install_datapath_flow(switchMac, flow, idle_timeout, hard_timeout, actions, bufid, priority, inport, packet)

    def delete_flow(self, flow, replicaNum):
	switchNum = self.findReplicasSwitch(replicaNum)
	orderDelete = self.getAllPaths(switchNum)
	orderDelete.reverse()
	Globals.log.info('Order of Delete ' + str(orderDelete))
	for switch in orderDelete:
	    currMac = self.getMac(switch)
	    Globals.log.info('Delete Flow: ' + str(flow) + ' at ' + str(switch))
	    self.Component.delete_strict_datapath_flow(currMac, flow)

    def flood(self, bufid, packet, actions, inport):
	for i, switchI in enumerate(Globals.SWITCHES):
	    self.Component.send_openflow(switchI['mac'], bufid, packet, actions, inport)

    def send(self, switchMac, bufid, packet, actions, inport):
	self.Component.send_openflow(switchMac, bufid, packet, actions, inport)
