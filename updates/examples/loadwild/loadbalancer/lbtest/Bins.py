# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Determines bins for required wildcard rule
# ==========================================


import Globals
import IPRules
import Alphas

def redistributeTargets(oldTargetRules, oldAlphas, newAlphas, oldTargetList, newTargetList):
    totalTraffic = sumTraffic(oldTargetRules)
    for i, oldAlpha in enumerate(oldAlphas):
        for j, newAlpha in enumerate(newAlphas):
            if oldAlpha['replica'] == newAlpha['replica']:
                overAssigns = 0
                if oldAlpha['alphaTarget'] == 0:
                    overAssigns = oldAlpha['alphaAssign'] - (Globals.MAXTGTTHRESH * totalTraffic * newAlpha['alphaTarget'])
		else:
                    overAssigns = oldAlpha['alphaAssign'] - (Globals.MAXTGTTHRESH * totalTraffic * newAlpha['alphaTarget'] / oldAlpha['alphaTarget'])
                if overAssigns > 0:
                    for k, target in enumerate(oldTargetRules):
			parentRule = IPRules.getParentRule(target)
			matchParentRule = IPRules.findMatch(newTargetList, parentRule['ip'], parentRule['wild'])
                        matchTargetRule = IPRules.findMatch(newTargetList, target['ip'], target['wild'])
                        childrenRule = IPRules.genChildrenRules(target)
                        matchChild1Rule = IPRules.findMatch(newTargetList, childrenRule[0]['ip'], childrenRule[0]['wild'])
                        matchChild2Rule = IPRules.findMatch(newTargetList, childrenRule[1]['ip'], childrenRule[1]['wild'])
                        if target['replica'] == oldAlpha['replica'] and overAssigns > 0 and matchTargetRule == [] and matchChild1Rule == [] and matchChild2Rule == [] and matchParentRule == [] and target['traffic'] != 0:
			    Globals.ASSIGNLOG.write("Redistributing: " + str(target['ip']) + '/' + str(target['wild']) + ':' + str(target['replica']) + '\n')
                            oldTargetList.append(target)
                            newTargetList.append(target)
                            break

    return (oldTargetList, newTargetList)
                            


def determineTargets(targetList, alphas, deeperList):
    totalTraffic = long(sumTraffic(targetList) / numNonZero(targetList))
    newTargetList = []
    oldTargetList = []

    Globals.ASSIGNLOG.write('Threshold: ' + str(totalTraffic * Globals.MINTGTTHRESH) + " < x < " + str(totalTraffic * Globals.MAXTGTTHRESH) + '\n')
    for i in range(0, len(targetList)):
        if targetList[i]['traffic'] > (totalTraffic * Globals.MAXTGTTHRESH) or Alphas.sumAllAlphaAssign(alphas) < Alphas.sumAllAlphaTarget(alphas):
	    Globals.ASSIGNLOG.write('\t' + str(targetList[i]['ip']) + " Beyond Threshold " + str(targetList[i]['traffic']) + '\n')
	    # Beyond Threshold: Need more rules
            childList = IPRules.findChildRules(deeperList, targetList[i]['ip'], targetList[i]['wild'])
            for j, child in enumerate(childList):
                newTargetList.append(child)
            if childList != []:
	        oldTargetList.append(targetList[i])
	elif targetList[i]['traffic'] < (totalTraffic * Globals.MINTGTTHRESH):
	    Globals.ASSIGNLOG.write('\t' + str(targetList[i]['ip']) + " Under Threshold " + str(targetList[i]['traffic']) + '\n')
	    # Below Theshold: Reduce rules
	    (siblingIP, siblingWild) = IPRules.findSiblingRule(targetList[i])
	    siblingRule = IPRules.findMatch(targetList, siblingIP, siblingWild)
	    if siblingRule != []:
	        if siblingRule[0]['traffic'] <= (totalTraffic * Globals.MINTGTTHRESH) and \
                   targetList.index(siblingRule[0]) < i:
		    parentRule = IPRules.getParentRule(siblingRule[0])
		    Globals.ASSIGNLOG.write('\t' + str(parentRule['ip']) + '/' + str(parentRule['wild']) + ' combined\n')
	            newTargetList.append(parentRule)
		    oldTargetList.append(targetList[i])
		    oldTargetList.append(siblingRule[0])
	else:
	    Globals.ASSIGNLOG.write('\t' + str(targetList[i]['ip']) + " Fine Threshold " + str(targetList[i]['traffic']) + '\n')
	    if targetList[i]['replica'] == -1:
	        newTargetList.append(targetList[i])
		oldTargetList.append(targetList[i])

    return (oldTargetList, newTargetList)

# =======================================
# Helper Functions
# =======================================

def sumTraffic(targetList):
    sum = 0
    for i in range(0, len(targetList)):
	sum += targetList[i]['traffic']

    return sum

def numNonZero(targetList):
    sum = 1
    for i in range(0, len(targetList)):
        if targetList[i]['traffic'] != 0:
	    sum += 1
    return sum

def printTargetList(targetList):
    Globals.ASSIGNLOG.write('New Rules to Assign:\n')
    for i in range(0, len(targetList)):
	Globals.ASSIGNLOG.write('\tIP : ' + targetList[i]['ip'] + ' Wild: ' + str(targetList[i]['wild']) + ' Replica: ' + str(targetList[i]['replica']) + ' Traffic ' + str(targetList[i]['traffic']))
	Globals.ASSIGNLOG.write('\n')
