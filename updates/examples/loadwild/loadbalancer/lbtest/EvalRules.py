# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# 1. Parses Alpha File 
# 2. Determine Wildcard Rules
# ==========================================


import Alphas
import Bins
import Globals
import IPRules

import IPTransition # DELETE LATER TODO

#class EvalRules:
#    def __init__(self):
#	self.IPNumBits = 0
#	self.IPBins = None
#	self.IPRules = None

def updateAlphas():
    oldTargetRules = copyTargets(Globals.TARGETRULES)      
    oldInstallRules = copyTargets(Globals.INSTALLEDRULES) 

    newAlphas = Alphas.getAlphas(Globals.ALPHAFILE)
    Globals.log.info("NEW ALPHAS " + str(newAlphas))
    Globals.log.info("OLD ALPHAS" + str(Globals.ALPHAS))
    (oldTargetList, newTargetList) = Bins.determineTargets(oldTargetRules, Globals.ALPHAS, oldInstallRules)
    (oldTargetList, newTargetList) = Bins.redistributeTargets(oldTargetRules, Globals.ALPHAS, newAlphas, oldTargetList, newTargetList)
#    Bins.printTargetList(newTargetList)
    totalAssignments = len(newTargetList)
    Globals.log.info("Total Assigns: " + str(totalAssignments))

    newAlphas = Alphas.distributeAlphas(newAlphas, Globals.ALPHAS, totalAssignments)
    Globals.log.info("DISTRIBUTE NEW ALPHAS " + str(newAlphas))
    newAlphas = Alphas.distributeEven(newAlphas, totalAssignments)
#    newAlphas = Alphas.distributeOld(newAlphas, Globals.ALPHAS, totalAssignments)
    Globals.log.info("DISTRIBUTE OLD ALPHAS " + str(newAlphas))
    newAlphas = Alphas.distributeRemaining(newAlphas, totalAssignments)
    Globals.log.info("REMAINING NEW ALPHAS " + str(newAlphas))
    Alphas.updateAlphas(newAlphas, oldTargetList)

    newTargetList = IPRules.assignReplicas(newAlphas, newTargetList)
    Bins.printTargetList(newTargetList)

    newRuleList = IPRules.getNewRules(Globals.TARGETRULES, newTargetList)
    IPRules.printRules(newRuleList)

#    (oldRules, newRules) = IPRules.redistributeRules(Globals.TARGETRULES, Globals.ALPHAS, newAlphas)
#    newRuleList.extend(newRules)

#    IPRules.updateAssigns(newRuleList, oldRules)
    IPRules.updateAssigns(newRuleList)
    Alphas.printAlphas(Globals.ALPHAS)

    return newRuleList

def copyTargets(targetList):
    copyList = []
    for i in range(0, len(targetList)):
        copyList.append({'ip': targetList[i]['ip'], 'wild': targetList[i]['wild'], 'replica': targetList[i]['replica'], 'traffic': targetList[i]['traffic']})
    return copyList

def copyAlphas(alphaList):
    copyList = []
    for i in range(0, len(alphaList)):
        copyList.append({'replica': alphaList[i]['replica'], 'alphaTarget': alphaList[i]['alphaTarget'], 'alphaAssign': alphaList[i]['alphaAssign']})
    return copyList
