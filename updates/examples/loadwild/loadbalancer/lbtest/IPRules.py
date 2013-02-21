# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Helper class for determining appropriate set of wildcard rules
# ==========================================


import Globals
import IPTransition
#from nox.lib.packet.packet_utils import ip_to_str, ipstr_to_int

#def redistributeRules(oldTargetRules, oldAlphas, newAlphas):
#    oldRules = []
#    newRules = []
#
#    totalTraffic = sumTraffic(oldTargetRules)
#    for i, oldAlpha in enumerate(oldAlphas):
#        for j, newAlpha in enumerate(newAlphas):
#            if oldAlpha['replica'] == newAlpha['replica']:
#                overAssigns = oldAlpha['alphaAssign'] - (Globals.MAXTGTTHRESH * totalTraffic * newAlpha['alphaTarget'] / oldAlpha['alphaTarget'])
#                if overAssigns > 0:
#                    for k, target in enumerate(oldTargetRules):
#                        if target['replica'] == oldAlpha['replica'] and overAssigns > 0:
#                            
#                            oldTargetList.append(target)
#                            newTargetList.append(target)
#                            overAssigns -= 1
#
#    return (oldRules, newRules)


def updateAssigns(newRulesList):
    for i in range(0, len(newRulesList)):
	newRules = newRulesList[i]['NewRules']
        oldRules = newRulesList[i]['OldRules']
        for j in range(0, len(newRules)):
            for k in range(0, len(Globals.ALPHAS)):
                if newRules[j]['replica'] == Globals.ALPHAS[k]['replica']:
                    Globals.ALPHAS[k]['alphaAssign'] += 1
	  
#    for i, oldRule in enumerate(oldRulesList):
#        for j, alpha in enumerate(Globals.ALPHAS):
#            if oldRule['replica'] == alpha['replica']:
#                Globals.ALPHAS[j]['alphaAssign'] -= 1
 
#        for i in range(0, len(oldRules)):
#            for j in range(0, len(Globals.ALPHAS)):
#                if oldRules[i]['replica'] == Globals.ALPHAS[j]['replica']:
#                    Globals.ALPHAS[j]['alphaAssign'] -= 1 
        

def assignReplicas(alphaList, newTargetList):
    finalTargetList = []
    unassignedTargetList = []
   
    # Keep Old Rules
    for i, target in enumerate(newTargetList):
	found = False
	for j, alpha in enumerate(alphaList):
	    if alpha['replica'] == target['replica']:
		if alpha['alphaAssign'] > 0:
		    alpha['alphaAssign'] -= 1
		    finalTargetList.append(target)
	        else:
		    target['replica'] = -1
		    unassignedTargetList.append(target)
		found = True
	if found == False:
            target['replica'] = -1
	    unassignedTargetList.append(target)

    # Distribute Remaining
    for i, alpha in enumerate(alphaList):
	numAssigns = alpha['alphaAssign']
	while numAssigns > 0:
	    target = unassignedTargetList.pop()
	    target['replica'] = alpha['replica']
	    finalTargetList.append(target)
	    numAssigns -= 1

    return finalTargetList

def getNewRules(oldTargets, newTargets):
    newRulesList = []
    for i in range(0, len(oldTargets)):    
        currIP = oldTargets[i]['ip']
        currWild = oldTargets[i]['wild']
        currReplica = oldTargets[i]['replica']

	matchRule = findMatch(newTargets, currIP, currWild)

	# 2 New Rules for 1 Old Rule
        if matchRule == []:
	    newChildRules = findChildRules(newTargets, currIP, currWild)
	    if newChildRules != []:
		newRulesList.append({'NewRules': newChildRules, 'OldRules': [oldTargets[i]]})

    for i in range(0, len(newTargets)):
	currRule = IPTransition.copyRule(newTargets[i])
        currIP = currRule['ip']
        currWild = currRule['wild']
        currReplica = currRule['replica']

        matchRule = findMatch(oldTargets, currIP, currWild)
	# 1 New Rule for 1 Old Rule
        if matchRule != []:
#	    if currRule['replica'] != matchRule[0]['replica']:
	    newRulesList.append({'NewRules': [currRule], 'OldRules': matchRule})
	# 1 New Rule for 2 Old Rules
	else:
	    oldChildRules = findChildRules(oldTargets, currIP, currWild)
	    alreadyRule = False
            for i, childRule in enumerate(oldChildRules):
                if findMatch(newTargets, childRule['ip'], childRule['wild']) != []:
		    alreadyRule = True
            if oldChildRules != [] and not alreadyRule:
		newRulesList.append({'NewRules': [currRule], 'OldRules': oldChildRules})

    return newRulesList

# =======================================
# Helper Functions
# =======================================

def printRules(rulesList):
    for  i in range(0, len(rulesList)):
	for j, oldRule in enumerate(rulesList[i]['OldRules']):
	    Globals.ASSIGNLOG.write(oldRule['ip'] + '/' + str(oldRule['wild']) + ':' + str(oldRule['replica']))
	    if j < len(rulesList[i]['OldRules']) - 1:
	        Globals.ASSIGNLOG.write(' + ')

        Globals.ASSIGNLOG.write('\t --> \t')

        for j, newRule in enumerate(rulesList[i]['NewRules']):
	    Globals.ASSIGNLOG.write(newRule['ip'] + '/' + str(newRule['wild']) + ':' + str(newRule['replica']))
	    if j < len(rulesList[i]['NewRules']) - 1:
	        Globals.ASSIGNLOG.write(' + ')
	Globals.ASSIGNLOG.write('\n')


def findMatch(rulesList, IP, numWild):
    for i in range(0, len(rulesList)):
        if rulesList[i]['ip'] == IP and rulesList[i]['wild'] == numWild:
	    return [rulesList[i]]
    return []

def findSiblingRule(rule):
    currIP = ipstr_to_int(rule['ip'])
    currWild = rule['wild']
    siblingIP = ((currIP >> (currWild - 1)) ^ 1) << (currWild - 1)
    siblingWild = currWild
    return (ip_to_str(siblingIP), siblingWild)

def isChild(parentRule, childIP):
    parentIP = ipstr_to_int(parentRule['ip'])
    parentWild = parentRule['wild']
    if parentIP >> parentWild == ipstr_to_int(childIP) >> parentWild:
#	Globals.log.info(childIP + ' is child of ' + ip_to_str(parentIP) + '/' + str(parentWild))
        return True
#    Globals.log.info(childIP + ' is NOT child of ' + ip_to_str(parentIP) + '/' + str(parentWild))
    return False

def findChildRules(rulesList, IP, numWild):
    IPAddr = ipstr_to_int(IP)
    childList = []
    for i in range(0, len(rulesList)):
        currIPAddr = ipstr_to_int(rulesList[i]['ip'])
        currNumWild = rulesList[i]['wild']
        if (currIPAddr >> numWild) == (IPAddr >> numWild) and numWild > currNumWild:
           childList.append(rulesList[i])
    return childList

def getParentRule(rule):
    currIP = ipstr_to_int(rule['ip'])
    currWild = rule['wild']
    currReplica = rule['replica']
    currTraffic = rule['traffic']

    parentIP = ip_to_str((currIP >> currWild) << currWild)
    parentWild = currWild + 1
    return {'ip': parentIP, 'wild': parentWild, 'replica': currReplica, 'traffic': currTraffic}

def genChildrenRules(rule):
    currIP = ipstr_to_int(rule['ip'])
    currWild = rule['wild']
    currReplica = rule['replica']
    currTraffic = rule['traffic']

    childRules = []
    leftIP = ip_to_str((currIP >> (currWild - 2)) << (currWild - 2))
    leftWild = currWild - 1
    childRules.append({'ip': leftIP, 'wild': leftWild, 'replica': currReplica, 'traffic': currTraffic})
    rightIP = ip_to_str(((currIP >> (currWild - 1))  + 1) << (currWild - 1))
    rightWild = currWild - 1
    childRules.append({'ip': rightIP, 'wild': rightWild, 'replica': currReplica, 'traffic': currTraffic})
    return childRules

# TODO: REMOVE
def ipstr_to_int(a):
    octets = a.split('.')
    return int(octets[0]) << 24 |\
           int(octets[1]) << 16 |\
           int(octets[2]) <<  8 |\
           int(octets[3]);

def ip_to_str(a):
    return "%d.%d.%d.%d" % ((a >> 24) & 0xff, (a >> 16) & 0xff, \
                            (a >> 8) & 0xff, a & 0xff)


