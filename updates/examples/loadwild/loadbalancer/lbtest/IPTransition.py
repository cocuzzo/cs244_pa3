# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Logic behind installing new wildcard rules
# and maintaining transition data
# ==========================================

import Globals
import IPRules
import Multipath
import IPs

import nox.lib.openflow as openflow
#from nox.lib.packet import tcp, ethernet, ipv4
from nox.lib.packet.packet_utils import ipstr_to_int, ip_to_str

def hardTimeoutHandler(rule):
    Globals.log.info('Hard Timeout for ' + rule['ip'] + '/' + str(rule['wild']))
    handleTimeoutRule(rule)
    Globals.TARGETLOG.write(' ************************************* \n')
    Globals.TARGETLOG.write('Hard Timeout: ' + rule['ip'] + '/' + str(rule['wild']) + '\n')
    printTargetInstallPairs(Globals.TARGETRULES, Globals.INSTALLEDRULES, Globals.TRANSITRULES)

def handleControllerAction(packet):
    if packet.type == packet.IP_TYPE and packet.next.TCP_PROTOCOL:
        Globals.log.info('Controller Action ' + ip_to_str(packet.next.srcip))
        (newReplica, oldReplica) = findReplicaAssignment(ip_to_str(packet.next.srcip), Globals.TARGETRULES, Globals.TRANSITRULES)
        tcpFlag = packet.next.arr[33]
        # SYN Flag Set
        if tcpFlag == 2:
            actionInstallMicroflow(packet, newReplica)
	else:
            actionInstallMicroflow(packet, oldReplica)
    else:
	Globals.log.info('Unknown Flow handled by controller')

def handleTimeoutRule(timeoutRule):
    printTimeoutRule(timeoutRule)

    for i, targetRule in enumerate(Globals.TARGETRULES):
        childRules = IPRules.findChildRules(Globals.TRANSITRULES, targetRule['ip'], targetRule['wild'])
        allDone = True
        for j, childRule in enumerate(childRules):
            if childRule['ip'] == timeoutRule['ip'] and childRule['wild'] == timeoutRule['wild']:
                Globals.TRANSITRULES.remove(timeoutRule)
                timeoutRule['replica'] = targetRule['replica']
		Globals.TRANSITRULES.append(timeoutRule)
            elif childRule['replica'] != targetRule['replica']:
                allDone = False
        
        if allDone and childRules != []:
            Globals.ASSIGNLOG.write("Moving to Installed: " + str(targetRule['ip']) + "/" + str(targetRule['wild']) + ":" + str(targetRule['replica']) + "\n")
            childRules = IPRules.findChildRules(Globals.TRANSITRULES, targetRule['ip'], targetRule['wild'])
            for j, childRule in enumerate(childRules):
                Globals.TRANSITRULES.remove(childRule)
                actionDeleteRule(childRule)
            newChildren = IPRules.genChildrenRules(targetRule)
            newChildren[0]['replica'] = targetRule['replica']
            newChildren[1]['replica'] = targetRule['replica']
	    newChildren[0]['traffic'] = long(targetRule['traffic'] / 2)
	    newChildren[1]['traffic'] = long(targetRule['traffic'] / 2)
            Globals.INSTALLEDRULES.append(newChildren[0])
            Globals.INSTALLEDRULES.append(newChildren[1])
            actionInstallRule(newChildren[0])
            actionInstallRule(newChildren[1])
    

def handleRules(rulesList):

    for i, rule in enumerate(rulesList):

    	newRules = rule['NewRules']
    	oldRules = rule['OldRules']
    	
    	# 1:1 means simply replacement! Never should be N:N
    	if len(newRules) == len(oldRules):
    	    oldRule = oldRules[0]
    	    newRule = newRules[0]
    	    oldIP = oldRule['ip']
    	    oldWild = oldRule['wild']
	    oldTraffic = oldRule['traffic']
    	    newIP = newRule['ip']
    	    newWild = newRule['wild']
    	    newReplica = newRule['replica']
    	    
    	    Globals.TARGETRULES.remove(oldRule)
    	    oldInstalledChildren = IPRules.findChildRules(Globals.INSTALLEDRULES, oldIP, oldWild)
    	    for i, oldChildRule in enumerate(oldInstalledChildren):
		newChildRule = copyRule(oldChildRule)
		newChildRule['replica'] = newReplica
    	        actionReplaceRule([oldChildRule], [newChildRule])
	    newRule['traffic'] = oldTraffic
    	    Globals.TARGETRULES.append(newRule)
    	    
    	# 1:2 install more specific targets
    	elif len(newRules) > len(oldRules):
    	    oldRule = oldRules[0]
    	    newRule1 = newRules[0]
    	    newRule2 = newRules[1]
    	    oldIP = oldRule['ip']
    	    oldWild = oldRule['wild']
            oldReplica = oldRule['replica']
            oldTraffic = oldRule['traffic']
    	    newIP1 = newRule1['ip']
    	    newWild1 = newRule1['wild']
    	    newReplica1 = newRule1['replica']
	    newTraffic1 = long(oldTraffic / 2)
    	    newIP2 = newRule2['ip']
    	    newWild2 = newRule2['wild']
    	    newReplica2 = newRule2['replica']
	    newTraffic2 = long(oldTraffic / 2)
    	   
    	    Globals.TARGETRULES.remove(oldRule)
    	    oldInstalledChildren = IPRules.findChildRules(Globals.INSTALLEDRULES, oldIP, oldWild)
    	    for i, rule in enumerate(oldInstalledChildren):
    	        newChildren = IPRules.genChildrenRules(rule)
	        if IPRules.findMatch([IPRules.getParentRule(newChildren[0])], newIP1, newWild1) != []:
                    newChildren[0]['replica'] = newReplica1
                    newChildren[1]['replica'] = newReplica1
		else:	
    	            newChildren[0]['replica'] = newReplica2
    	            newChildren[1]['replica'] = newReplica2
		newChildren[0]['traffic'] = long(rule['traffic'] / 2)
		newChildren[1]['traffic'] = long(rule['traffic'] / 2)
                rule['replica'] = oldReplica

    	        actionReplaceRule([rule], newChildren)
    	    Globals.TARGETRULES.append(newRule1)
    	    Globals.TARGETRULES.append(newRule2)

	# 2:1 install more general targets
        else:
            newRule = newRules[0]
            newIP = newRule['ip']
            newWild = newRule['wild']
            newReplica = newRule['replica']
            oldRule1 = oldRules[0]
            oldRule2 = oldRules[1]
            oldIP1 = oldRule1['ip']
            oldWild1 = oldRule1['wild']
	    oldTraffic1 = oldRule1['traffic']
            oldIP2 = oldRule2['ip']
            oldWild2 = oldRule2['wild']
	    oldTraffic2 = oldRule2['traffic']
            
            Globals.TARGETRULES.remove(oldRule1)
            Globals.TARGETRULES.remove(oldRule2)
            oldInstalledChildren1 = IPRules.findChildRules(Globals.INSTALLEDRULES, oldIP1, oldWild1)
	    oldTransitionChildren1 = IPRules.findChildRules(Globals.TRANSITRULES, oldIP1, oldWild1)
	    oldInstalledChildren1.extend(oldTransitionChildren1)
            oldRule1['replica'] = newReplica
            actionReplaceRule(oldInstalledChildren1, [oldRule1])
            oldInstalledChildren2 = IPRules.findChildRules(Globals.INSTALLEDRULES, oldIP2, oldWild2)
	    oldTransitionChildren2 = IPRules.findChildRules(Globals.TRANSITRULES, oldIP2, oldWild2)
	    oldInstalledChildren2.extend(oldTransitionChildren2)
            oldRule2['replica'] = newReplica
            actionReplaceRule(oldInstalledChildren2, [oldRule2])
	    newRule['traffic'] = long(oldTraffic1 + oldTraffic2)
            Globals.TARGETRULES.append(newRule)


def actionReplaceRule(oldRuleList, newRuleList):

    if len(oldRuleList) == len(newRuleList):
	oldRule = oldRuleList[0]
	newRule = newRuleList[0]
        if oldRule in Globals.INSTALLEDRULES:
            Globals.INSTALLEDRULES.remove(oldRule)
            actionDeleteRule(oldRule)
	    if oldRule['replica'] == -1:
		Globals.INSTALLEDRULES.append(newRule)
		actionInstallRule(newRule)
	    else:
		newRule['replica'] = oldRule['replica']
	        Globals.TRANSITRULES.append(newRule)
	        actionTransitionRule(newRule)
	else:
	    print "Should NOT Be In Transitions"
	    
    elif len(oldRuleList) > len(newRuleList):
        newRule = newRuleList[0]
        for i, oldRule in enumerate(oldRuleList):
            if oldRule in Globals.INSTALLEDRULES:
                Globals.INSTALLEDRULES.remove(oldRule)
                actionDeleteRule(oldRule)
                Globals.TRANSITRULES.append(oldRule)
                actionTransitionRule(oldRule)

    elif len(oldRuleList) < len(newRuleList):
	oldRule = oldRuleList[0]
        newRule1 = newRuleList[0]	
	newRule2 = newRuleList[1]
	if oldRule in Globals.INSTALLEDRULES:
	    Globals.INSTALLEDRULES.remove(oldRule)
	    actionDeleteRule(oldRule)
	    if oldRule['replica'] == -1:
	        Globals.INSTALLEDRULES.append(newRule1)
		Globals.INSTALLEDRULES.append(newRule2)
		actionInstallRule(newRule1)
		actionInstallRule(newRule2)
	    else:
		newRule1['replica'] = oldRule['replica']
                newRule2['replica'] = oldRule['replica']
		Globals.TRANSITRULES.append(newRule1)
		Globals.TRANSITRULES.append(newRule2)
		actionTransitionRule(newRule1)
		actionTransitionRule(newRule2)
	else:
	    print "Should NOT Be IN Transition"

def actionInstallMicroflow(packet, replica):
    Globals.INSTALLLOG.write("***Microflow " + ip_to_str(packet.next.srcip) + " to replica " + str(replica) + '\n')
    for i in range(0, Globals.NUMREPLICAS):
        if Globals.REPLICAS[i]['no'] == replica:
            (flow, defaultActions, rewriteActions) = IPs.get_microflow_dstrule(packet, Globals.REPLICAS[i]['mac'], Globals.REPLICAS[i]['ip'], replica)
	    Multipath.install_replica_flow(flow, Globals.SOFT_TIMEOUT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY + 10, 0, None, replica, rewriteActions)
   
def actionInstallRule(rule):
    Globals.INSTALLLOG.write("***Installing Rule: " + str(rule) + '\n')
    for i in range(0, Globals.NUMREPLICAS):
        if Globals.REPLICAS[i]['no'] == rule['replica']:
            (flow, defaultActions, rewriteActions) = IPs.get_forwarding_dstrule(ipstr_to_int(rule['ip']), rule['wild'], Globals.VIP, Globals.REPLICAS[i]['mac'], Globals.REPLICAS[i]['ip'], Globals.REPLICAS[i]['port'])
	    Multipath.install_replica_flow(flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY, 0, None, rule['replica'], rewriteActions)

def actionTransitionRule(rule):
    Globals.INSTALLLOG.write("***Transition Rule: " + str(rule) + '\n')
    (flow, defaultActions, rewriteActions) = IPs.get_controller_dstrule(ipstr_to_int(rule['ip']), rule['wild'], Globals.VIP)
    Multipath.install_controller_flow(flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, defaultActions, None, openflow.OFP_DEFAULT_PRIORITY, 0, None, rule['replica'], rewriteActions)
    Globals.COMPONENT.post_callback(Globals.HARD_TIMEOUT, lambda : hardTimeoutHandler(rule))

def actionDeleteRule(rule):
    Globals.INSTALLLOG.write("***Removing Rule: " + str(rule) + '\n')
    for i in range(0, Globals.NUMREPLICAS):
        if Globals.REPLICAS[i]['no'] == rule['replica']:
            (flow, defaultActions, rewriteActions) = IPs.get_forwarding_dstrule(ipstr_to_int(rule['ip']), rule['wild'], Globals.VIP, Globals.REPLICAS[i]['mac'], Globals.REPLICAS[i]['ip'], Globals.REPLICAS[i]['port'])
            Multipath.delete_flow(flow, rule['replica'])

# =======================================
# Helper Functions
# =======================================

def findReplicaAssignment(srcIP, targetList, transitList):
    newTarget = 0
    oldTarget = 0

    for i, target in enumerate(targetList):
        if IPRules.isChild(target, srcIP):
            newTarget = target['replica']

    for i, transit in enumerate(transitList):
        if IPRules.isChild(transit, srcIP):
            oldTarget = transit['replica']

    return (newTarget, oldTarget)


def printTargetInstallPairs(targetList, installList, transitList):
    Globals.TARGETLOG.write('Installed:\n')
    for i, target in enumerate(targetList):
        childRules = IPRules.findChildRules(installList, target['ip'], target['wild'])
	if childRules != []:
	    Globals.TARGETLOG.write(str(target['ip']) + "/" + str(target['wild']) + " -> " + str(target['replica']) + ":" + str(target['traffic']) + '\n')
	    for j, rule in enumerate(childRules):
	        Globals.TARGETLOG.write('\t' + str(rule['ip']) + "/" + str(rule['wild']) + " -> " + str(rule['replica']) + ":" + str(rule['traffic']) + '\n')

    Globals.TARGETLOG.write('Transition:\n')
    for i, target in enumerate(targetList):
        childRules = IPRules.findChildRules(transitList, target['ip'], target['wild'])
	if childRules != []:
            Globals.TARGETLOG.write(str(target['ip']) + "/" + str(target['wild']) + " -> " + str(target['replica']) + ":" + str(target['traffic']) + '\n')
            for j, rule in enumerate(childRules):
                Globals.TARGETLOG.write('\t' + str(rule['ip']) + "/" + str(rule['wild']) + " -> " + str(rule['replica']) + ":" + str(rule['traffic']) + '\n')

def printTimeoutRule(rule):
    Globals.ASSIGNLOG.write("Hard Timeout: " + str(rule['ip']) + "/" + str(rule['wild']) + "/" + str(rule['replica']) + "\n")

def copyRule(rule):
    return {'ip': rule['ip'], 'wild': rule['wild'], 'replica': rule['replica'], 'traffic': rule['traffic']}

