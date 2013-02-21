# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Logic behind installing new wildcard rules
# and maintaining transition data
# ==========================================


import time
from Multipath import *

import nox.lib.openflow as openflow
from nox.lib.packet import tcp, ethernet, ipv4
from nox.lib.packet.packet_utils import ip_to_str

import IPs
import Globals

class IPTransition:
    def __init__(self, Component, Multipath):
	self.Component = Component
	self.InstalledRules = [] # {'IP', 'NumWild', 'Replica'}
	self.InTransitionRules = [] # {'NewRule': {'IP', 'NumWild', 'Replica'}, 'OldRuleList': [{'IP', 'NumWild', 'Replica'}]}
	self.InWaitingRules = [] # 

	self.Multipath = Multipath
	self.TimeoutQueue = []

    def installRules(self, rulePairList):
	Globals.RULESLOG.write('\n=======================================\n Install NEW Rules\n')
	self.printRules(rulePairList)
	for i, rulePair in enumerate(rulePairList):
	    self.handleRulePair(rulePair)

	Globals.RULESLOG.write('*** Installed Rules: \n')
	self.printRules(self.InstalledRules)
	Globals.RULESLOG.write('*** InTransition Rules: \n')
	self.printRules(self.InTransitionRules)

	Globals.RULESLOG.write('----------------------------------------\n\n')
	Globals.RULESLOG.flush()

    # =================================
    # CONTROLLER ACTION
    # =================================
    def controllerAction(self, packet):
	Globals.RULESLOG.write('Handle Action by Controller\n')

	installedHandler = self.findHandlerInNewList(packet.next.srcip, self.InstalledRules)
	if installedHandler != None:
	    Globals.log.info('Warning! WHY HERE?' + str(installedHandler))
	    self.installMicroflowRule(packet, installedHandler['NewRule']['Replica'])
	    return
	
	oldTransitionHandler = self.findHandlerInOldList(packet.next.srcip, self.InTransitionRules)
	newTransitionHandler = self.findHandlerInNewList(packet.next.srcip, self.InTransitionRules)
	if oldTransitionHandler != None and newTransitionHandler != None:
	    if packet.type == packet.IP_TYPE and packet.next.protocol == packet.next.TCP_PROTOCOL:
		tcpFlag = packet.next.arr[33]
		if tcpFlag == 2:
	            Globals.RULESLOG.write('New Flow ' + str(time.time()) + '\n')
	            Globals.RULESLOG.write(str(packet))
		    Globals.log.info(str(newTransitionHandler))
	            self.installMicroflowRule(packet, newTransitionHandler['Replica'])
		else:
		    Globals.RULESLOG.write('Old Flow ' + str(time.time()) + '\n')
		    Globals.RULESLOG.write(str(packet))
	            self.installMicroflowRule(packet, oldTransitionHandler['Replica'])
	    else:
		Globals.RULESLOG.write('Unknown Flow ' + str(time.time()) + '\n')
		Globals.RULESLOG.write(str(packet))
	        self.installMicroflowRule(packet, oldTransitionHandler['Replica'])
	    return
	
	Globals.log.info('Warning! CONTROLLER ACTION NOT HANDLED')
	return

    # =================================
    # HARD TIMEOUT CALLBACK
    # =================================
    def hardTimeoutExpiration(self):
	rule = self.TimeoutQueue.pop()
	Globals.RULESLOG.write('\n-------------------------------\nHARD TIMEOUT!!!\n')
	Globals.RULESLOG.write('Timeout Rule: ' + ip_to_str(rule['IP']) + ':' + str(rule['NumWild']) + ':' + str(rule['Replica']) + '\n')
	
	foundInTransitParentPairs = self.childToRuleInList(rule, self.InTransitionRules)
	foundInTransitChildPair = self.parentToRuleInList(rule, self.InTransitionRules)
	Globals.RULESLOG.write('Transit Parent: \n')
	self.printRules(foundInTransitParentPairs)
	Globals.RULESLOG.write('Transit Child: \n')
	self.printRules(foundInTransitChildPair)

	# Part of a Big list
	if foundInTransitParentPairs != []:
	    if len(foundInTransitParentPairs) > 1:
		Globals.log.info('Warning! Shouldnt be more than one parent')

	    parent = foundInTransitParentPairs[0]
	    for i in range(0, len(parent['OldRuleList'])):
		if parent['OldRuleList'][i]['IP'] == rule['IP']:
		    self.deleteRule(parent['OldRuleList'][i])
		    parent['OldRuleList'].remove(parent['OldRuleList'][i])
		    rule['Replica'] = parent['NewRule']['Replica']
		    parent['OldRuleList'].append(rule)
		    self.installPermRule(rule)
	    
	    done = True
	    for i in range(0, len(parent['OldRuleList'])):
		if parent['OldRuleList'][i]['Replica'] != parent['NewRule']['Replica']:
		    done = False

	    if done == True:
		if len(parent['OldRuleList']) == 1:
		    self.InTransitionRules.remove(parent)
		    self.InstalledRules.append({'NewRule': parent['NewRule'], 'OldRuleList': []})
		else:
		    for i in range(0, len(parent['OldRuleList'])):
		        self.deleteRule(parent['OldRuleList'][i])
		    self.InTransitionRules.remove(parent)
		    self.installPermRule(parent['NewRule'])
		    self.InstalledRules.append({'NewRule': parent['NewRule'], 'OldRuleList': []})		    

	# Broken into smaller pieces 
	elif foundInTransitChildPair != []:
	    for i in range(0, len(foundInTransitChildPair)):
		child = foundInTransitChildPair[i]
		self.InTransitionRules.remove(child)
		for j in range(0, len(child['OldRuleList'])):
		    childRule = child['OldRuleList'][j]
		    self.deleteRule(childRule)

		rule = {'NewRule': child['NewRule'], 'OldRuleList': []}
		self.InstalledRules.append(rule)
		self.installPermRule(rule['NewRule'])
	   
        Globals.RULESLOG.write('*** Installed Rules: \n')
      	self.printRules(self.InstalledRules)
        Globals.RULESLOG.write('*** InTransition Rules: \n')
        self.printRules(self.InTransitionRules)
	Globals.RULESLOG.flush()


    # =================================	
    # Helpers
    # =================================	
    def findHandlerInNewList(self, ruleIP, list):
	for i in range(0, len(list)):
	    IP = list[i]['NewRule']['IP']
	    numWild = list[i]['NewRule']['NumWild']
	    if ((ruleIP >> numWild) == (IP >> numWild)):
		return list[i]['NewRule']

	return None

    def findHandlerInOldList(self, ruleIP, list):
	for i in range(0, len(list)):
	    for j in range(0, len(list[i]['OldRuleList'])):
		IP = list[i]['OldRuleList'][j]['IP']
		numWild = list[i]['OldRuleList'][j]['NumWild']
		if ((ruleIP >> numWild) == (IP >> numWild)):
		    return list[i]['OldRuleList'][j]

	return None

    def printRules(self, rulelist):
	for i in range(0, len(rulelist)):
	    Globals.RULESLOG.write('\tNew Rule: ' + self.ruleToString(rulelist[i]['NewRule']) + ' ==> [')
	    for j in range(0, len(rulelist[i]['OldRuleList'])):
		Globals.RULESLOG.write('! OldRule: ' + self.ruleToString(rulelist[i]['OldRuleList'][j]))
	    Globals.RULESLOG.write(']\n')

    def childToRuleInList(self, rule, list):
        IP = rule['IP']
        numWild = rule['NumWild']
	parents = []
	for i in range(0, len(list)):
	    if ((IP >> list[i]['NewRule']['NumWild']) == (list[i]['NewRule']['IP'] >> list[i]['NewRule']['NumWild'])) and (numWild <= list[i]['NewRule']['NumWild']):
		parents.append(list[i])
        return parents

    def parentToRuleInList(self, rule, list):
	IP = rule['IP']
	numWild = rule['NumWild']
	children = []
	for i in range(0, len(list)):
	    if ((IP >> numWild) == (list[i]['NewRule']['IP'] >> numWild)) and (numWild > list[i]['NewRule']['NumWild']):
		children.append(list[i])

	return children

    def getOverlapRules(self, rule, list):
	overlapRules = []
	for i in range(0, len(list)):
	    if list[i]['NumWild'] == rule['NumWild'] and list[i]['IP'] == rule['IP']:
		overlapRules.append(list[i])

	    elif list[i]['NumWild'] < rule['NumWild']:
		overlapRules.append(list[i])

	    elif list[i]['NumWild'] > rule['NumWild']:
		possibleOverlapList = self.getRulesForDepth(list[i], rule['NumWild'])
		for j in range(0, len(possibleOverlapList)):
		    if possibleOverlapList[j]['NumWild'] == rule['NumWild'] and possibleOverlapList[j]['IP'] == rule['IP']:
			overlapRules.append(possibleOverlapList[j])
	return overlapRules

    def coalesceNewRules(self, list):
        startIndex = 0
	newlist = list

	while startIndex < len(newlist):
	    startRule = newlist[startIndex]
	    startIP = startRule['NewRule']['IP']
	    startWild = startRule['NewRule']['NumWild']
	    startReplica = startRule['NewRule']['Replica']
	    for i in range(0, len(newlist)):
		currRule = newlist[i]
		currIP = currRule['NewRule']['IP']
		currWild = currRule['NewRule']['NumWild']
		currReplica = currRule['NewRule']['Replica']
		if startWild == currWild and startIP == (currIP ^ (1 << currWild)) and startReplica == currReplica:
		    oldList = startRule['OldRuleList']
		    oldList.extend(currRule['OldRuleList'])
		    newRule = {'NewRule': {'IP': (startIP & (~(1 << currWild))), 'NumWild': currWild + 1, 'Replica': currReplica}, 'OldRuleList': oldList}
		    newlist.remove(startRule)
		    newlist.remove(currRule)
		    newlist.append(newRule)
		    startIndex = -1
		    break
	    startIndex = startIndex + 1
	return newlist
	

    def handleRulePair(self, rulePair):
	newRule = rulePair['NewRule']
	oldRuleList = rulePair['OldRuleList']
	Globals.RULESLOG.write('*Handling New Rule: ' + self.ruleToString(newRule) + '\n')

	foundInstallParentPairs = self.parentToRuleInList(newRule, self.InstalledRules)
	foundInstallChildPair = self.childToRuleInList(newRule, self.InstalledRules)
	foundInTransitParentPairs = self.parentToRuleInList(newRule, self.InTransitionRules)
	foundInTransitChildPair = self.childToRuleInList(newRule, self.InTransitionRules)

	# This rule is a child of a rule => split rule into smaller pieces
	if foundInstallChildPair != []:
	    Globals.RULESLOG.write('FoundInstallChildPair\n')
	    if len(foundInstallChildPair) > 1:
		Globals.log.info('Warning! Should not be more than one parent')

	    parentRule = foundInstallChildPair[0]
	    # Find the smaller rules bigger parent rule should be replaced with
	    smallerInstalledRules = self.getRulesForDepth(parentRule['NewRule'], newRule['NumWild'])
	    Globals.RULESLOG.write('SMALLER ' + str(smallerInstalledRules) + '\n')
	    handleToInstallRules = []
	    handleToTransitRules = []

	    # Install subsequent smaller rules
	    for i in range(0, len(smallerInstalledRules)):
		# Rule with new replica assignment
		if smallerInstalledRules[i]['IP'] == newRule['IP'] and smallerInstalledRules[i]['Replica'] != newRule['Replica']:
		    rule = smallerInstalledRules[i]
		    handleToTransitRules.append({'NewRule': {'IP': rule['IP'], 'NumWild': rule['NumWild'], 'Replica': newRule['Replica']}, 'OldRuleList': [{'IP': rule['IP'], 'NumWild': rule['NumWild'], 'Replica': parentRule['NewRule']['Replica']}]})
		else:
		    handleToInstallRules.append({'NewRule': smallerInstalledRules[i], 'OldRuleList': []})


	    coalesceInstallRules = self.coalesceNewRules(handleToInstallRules)
	    coalesceTransitRules = self.coalesceNewRules(handleToTransitRules)
	    self.InstalledRules.remove(parentRule)
	    self.deleteRule(parentRule['NewRule'])
	    for i in range(0, len(coalesceInstallRules)):
		self.InstalledRules.append(coalesceInstallRules[i])
		self.installPermRule(coalesceInstallRules[i]['NewRule'])
	    for i in range(0, len(coalesceTransitRules)):
		self.InTransitionRules.append(coalesceTransitRules[i])
		for j in range(0, len(coalesceTransitRules[i]['OldRuleList'])):
		    self.installRuleToController(coalesceTransitRules[i]['OldRuleList'][j])
		    self.TimeoutQueue.insert(0, coalesceTransitRules[i]['OldRuleList'][j])
		    self.Component.post_callback(Globals.HARD_TIMEOUT, lambda : self.hardTimeoutExpiration())


	elif foundInTransitChildPair != []:
	    Globals.RULESLOG.write('FoundInTransitChildPair\n')
	    if len(foundInTransitChildPair) > 1:
		Globals.log.info('Warning! Should not be more than one parent!')
	
	    parentRule = foundInTransitChildPair[0]
	    # Find the smaller rules
	    smallerInTransitRules = self.getRulesForDepth(parentRule['NewRule'], newRule['NumWild'])
	    
	    handleToTransitRules = []
	    
	    for i in range(0, len(smallerInTransitRules)):
		if smallerInTransitRules[i]['IP'] == newRule['IP']:
		    rule = {'NewRule': newRule, 'OldRuleList': self.getOverlapRules(newRule, parentRule['OldRuleList'])}
		    for j in range(0, len(parentRule['OldRuleList'])):
			if parentRule['NewRule']['Replica'] == parentRule['OldRuleList'][j]['Replica']:
			    self.deleteRule(parentRule['OldRuleList'][j])
			    self.installRuleToController(parentRule['OldRuleList'][j])
			    self.TimeoutQueue.insert(0, parentRule['OldRuleList'][j])
			    self.Component.post_callback(Globals.HARD_TIMEOUT, lambda : self.hardTimeoutExpiration())
		    handleToTransitRules.append(rule)
		else:
		    rule = {'NewRule': smallerInTransitRules[i], 'OldRuleList': self.getOverlapRules(smallerInTransitRules[i], parentRule['OldRuleList'])}
		    handleToTransitRules.append(rule)

	    coalesceTransitRules = self.coalesceNewRules(handleToTransitRules)
	    self.InTransitionRules.remove(parentRule)
	    for i in range(0, len(coalesceTransitRules)):
		childRule = coalesceTransitRules[i]
		self.InTransitionRules.append(childRule)
		for j in range(0, len(childRule['OldRuleList'])):
		    if childRule['NewRule']['Replica'] == childRule['OldRuleList'][j]['Replica']:
			self.deleteRule(childRule['OldRuleList'][j])
			self.installPermRule(childRule['OldRuleList'][j])

	elif foundInstallParentPairs != [] or foundInTransitParentPairs != []:
	    Globals.RULESLOG.write('FoundInstall + FoundInTransit\n')
            handleToInstallRules = []
            handleToTransitRules = []
	    handleInTransitRules = []
	    Globals.log.info('FoundInstall ' + str(foundInstallParentPairs))
	    Globals.log.info('FoundTransit ' + str(foundInTransitParentPairs))

	    # Installed Rules
	    for i in range(0, len(foundInstallParentPairs)):
		childRule = foundInstallParentPairs[i]
		self.InstalledRules.remove(childRule)
		if newRule['Replica'] == childRule['NewRule']['Replica']:
		    handleToInstallRules.append(childRule)
		    Globals.log.info('Handle ' + str(handleToInstallRules))
		else:
		    rule = {'NewRule': {'IP': childRule['NewRule']['IP'], 'NumWild': childRule['NewRule']['NumWild'], 'Replica': newRule['Replica']}, 'OldRuleList': [{'IP': childRule['NewRule']['IP'], 'NumWild': childRule['NewRule']['NumWild'], 'Replica': childRule['NewRule']['Replica']}]}
		    handleToTransitRules.append(rule)
		    Globals.log.info('Parent ' + str(foundInstallParentPairs))
		    Globals.log.info('RULE: ' + str(rule))
		    Globals.log.info('childRule: ' + str(childRule))
		    Globals.log.info('Handle TO Transit ' + str(handleToTransitRules))

	    # In Transition Rules
	    for i in range(0, len(foundInTransitParentPairs)):
		childRule = foundInTransitParentPairs[i]
		self.InTransitionRules.remove(childRule)
		for j in range(0, len(childRule['OldRuleList'])):
		    oldRule = childRule['OldRuleList'][j]
		    Globals.log.info('Child ' + str(childRule))
		    Globals.log.info('Old ' + str(oldRule))
		    if childRule['NewRule']['Replica'] == oldRule['Replica']:
			self.deleteRule(oldRule)
			self.installRuleToController(oldRule)
			self.Component.post_callback(Globals.HARD_TIMEOUT, lambda : self.hardTimeoutExpiration(oldRule))
			
		childRule['NewRule']['Replica'] = newRule['Replica']
		handleInTransitRules.append(childRule)

	    oldRuleList = []
	    coalesceInstallRules = handleToInstallRules
	    coalesceToTransitRules = self.coalesceNewRules(handleToTransitRules)
	    coalesceInTransitRules = self.coalesceNewRules(handleInTransitRules)
	    Globals.log.info(str(coalesceInstallRules))
	    Globals.log.info(str(coalesceToTransitRules))
	    Globals.log.info(str(coalesceInTransitRules))
	    for i in range(0, len(coalesceInstallRules)):
		oldRuleList.append(coalesceInstallRules[i]['NewRule'])
	    for i in range(0, len(coalesceToTransitRules)):
		for j in range(0, len(coalesceToTransitRules[i]['OldRuleList'])):
		    oldRule = coalesceToTransitRules[i]['OldRuleList'][j]
		    self.deleteRule(oldRule)
		    Globals.log.info('COALESCE TO TRANSIT ' + str(coalesceToTransitRules))
		    self.installRuleToController(oldRule)
		    Globals.RULESLOG.write('Timeout Installed For: ' + self.ruleToString(oldRule) + '\n')
		    self.TimeoutQueue.insert(0, oldRule)
		    self.Component.post_callback(Globals.HARD_TIMEOUT, lambda : self.hardTimeoutExpiration())
		    oldRuleList.append(oldRule)
		    Globals.log.info('Installing Rule for ' + str(oldRule))
	    for i in range(0, len(coalesceInTransitRules)):
	        childRule = coalesceInTransitRules[i]
		for j in range(0, len(childRule['OldRuleList'])):
		    if childRule['NewRule']['Replica'] == childRule['OldRuleList'][j]['Replica']:
			self.deleteRule(childRule['OldRuleList'][j])
			self.installPermRule(childRule['OldRuleList'][j])
		    oldRuleList.append(childRule['OldRuleList'][j])

	    rule = {'NewRule': newRule, 'OldRuleList': oldRuleList}		
	    Globals.log.info('New Rule ' + str(rule))
	    self.InTransitionRules.append(rule)
		

	else:
	    self.InstalledRules.append({'NewRule': newRule, 'OldRuleList': []})
	    self.installPermRule(newRule)

    def getRulesForDepth(self, rule, depth): 
	if rule['NumWild'] == 0:
	    return []
	if rule['NumWild'] == depth:
	    return [rule]

	leftRule = {'IP': rule['IP'], 'NumWild': rule['NumWild'] - 1, 'Replica': rule['Replica']}
	rightRule = {'IP': rule['IP'] + (1 << (rule['NumWild'] - 1)), 'NumWild': rule['NumWild'] - 1, 'Replica': rule['Replica']}
	leftList = self.getRulesForDepth(leftRule, depth)
	rightList = self.getRulesForDepth(rightRule, depth)
	leftList.extend(rightList)

	return leftList

    def installRuleToController(self, rule):
	Globals.RULESLOG.write('Installed CONTROLLER Rule ' + self.ruleToString(rule) + '\n')
	(flow, defaultActions, rewriteActions) = IPs.get_controller_dstrule(rule['IP'], rule['NumWild'], Globals.VIP)
	self.Multipath.install_controller_flow(flow, Globals.CACHE_TIMEOUT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY, 0, None, rule['Replica'], rewriteActions)


    def installMicroflowRule(self, packet, replica):
	Globals.RULESLOG.write('Microflow for replica ' + str(replica) +'\n')
	for i in range(0, Globals.NUMREPLICAS):
	    if Globals.REPLICAS[i]['no'] == replica:
	        Globals.RULESLOG.write('Installed MICROFLOW Rule ' + str(packet.next.srcip) + '\n')
		(flow, defaultActions, rewriteActions) = IPs.get_microflow_dstrule(packet, Globals.REPLICAS[i]['mac'], Globals.REPLICAS[i]['ip'], replica)
		self.Multipath.install_replica_flow(flow, Globals.SOFT_TIMEOUT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY + 10, 0, None, replica, rewriteActions)


    def installPermRule(self, rule):
	for i in range(0, Globals.NUMREPLICAS):
	    if Globals.REPLICAS[i]['no'] == rule['Replica']:
                Globals.RULESLOG.write('Installed NEW Rule ' + self.ruleToString(rule) + '\n')
		(flow, defaultActions, rewriteActions) = IPs.get_forwarding_dstrule(rule['IP'], rule['NumWild'], Globals.VIP, Globals.REPLICAS[i]['mac'], Globals.REPLICAS[i]['ip'], Globals.REPLICAS[i]['port'])
		self.Multipath.install_replica_flow(flow, Globals.CACHE_TIMEOUT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY, 0, None, rule['Replica'], rewriteActions)

    def deleteRule(self, rule):
        for i in range(0, Globals.NUMREPLICAS):
            if Globals.REPLICAS[i]['no'] == rule['Replica']:
		Globals.RULESLOG.write('Deleted OLD Rule ' + self.ruleToString(rule) + '\n')
                (flow, defaultActions, rewriteActions) = IPs.get_forwarding_dstrule(rule['IP'], rule['NumWild'], Globals.VIP, Globals.REPLICAS[i]['mac'], Globals.REPLICAS[i]['ip'], Globals.REPLICAS[i]['port'])
		self.Multipath.delete_flow(flow, rule['Replica'])

    def ruleToString(self, rule):
        return 'IP: ' + ip_to_str(rule['IP']) + ' NumWild: ' + str(rule['NumWild']) + ' Replica: ' + str(rule['Replica'])
