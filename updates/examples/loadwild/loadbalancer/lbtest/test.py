import EvalRules
import IPTransition
import Globals
import Multipath

import os
import time

def alphaFileUpdate():
    Globals.printNewPeriod()
    Globals.PERIOD += 1
    rulePairList = EvalRules.updateAlphas()
    IPTransition.handleRules(rulePairList)
    IPTransition.printTargetInstallPairs(Globals.TARGETRULES, Globals.INSTALLEDRULES, Globals.TRANSITRULES)

def hardTimeoutHandler(timeoutRule):
    Globals.printNewPeriod()
    Globals.PERIOD += 1
    IPTransition.handleTimeoutRule(timeoutRule)
    IPTransition.printTargetInstallPairs(Globals.TARGETRULES, Globals.INSTALLEDRULES, Globals.TRANSITRULES)

# Init Forwarding Table
Multipath.calcForwardingTable()

# NEW ALPHAS
os.system('cp ' + Globals.HOME + 'alpha1.txt ' + Globals.HOME + 'alpha.txt') 
time.sleep(1)

alphaFileUpdate()
Globals.TARGETRULES[0]['traffic'] = 99

alphaFileUpdate()
Globals.TARGETRULES[0]['traffic'] = 1


# NEW ALPHAS
os.system('cp ' + Globals.HOME + 'alpha2.txt ' + Globals.HOME + 'alpha.txt')
time.sleep(1)


alphaFileUpdate()
Globals.TARGETRULES[1]['traffic'] = 10

hardTimeoutHandler(Globals.TRANSITRULES[0])

timeoutRules = []
for i, transitRule in enumerate(Globals.TRANSITRULES):
    timeoutRules.append(IPTransition.copyRule(transitRule))
for i, transitRule in enumerate(timeoutRules):
    hardTimeoutHandler(transitRule)

