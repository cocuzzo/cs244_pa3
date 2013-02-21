# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Helper class for determining appropriate set of wildcard rules
# ==========================================


import Globals

class IPRules:
    def __init__(self):
	self.AvailableRules = [
				{'IP': 0, 'NumWild': 31, 'Replica': 0},
				{'IP': 1 << 31, 'NumWild': 30, 'Replica': 0},
				{'IP': 3 << 30, 'NumWild': 29, 'Replica': 0}
			      ]
	self.TryKeepRules = []
	self.InstalledRules = []

    def getNewRuleAtDepth(self, depth, replica):
        Globals.log.info("Looking for rule at depth: " + str(depth))

	currwild = self.findRepDepthInList(depth, replica, self.TryKeepRules)
        if (currwild != None):
	    self.TryKeepRules.remove(currwild)
	    self.InstalledRules.append(currwild)
	    return None
	
	if self.AvailableRules == []:
            newRulePair = self.makeRuleAtDepth(depth, replica)
            return newRulePair

	currwild = self.AvailableRules.pop(0)

	# If New Rules
	if (currwild['NumWild'] >= depth):
	    Globals.log.info('New Rule')
	    newRulePair = self.insertRuleAtDepth(currwild, depth, replica)
	    return newRulePair

	# Else Transition Rules
	else:
	    Globals.log.info('Transit Rule')
	    self.insertInAvailableRules(currwild)
	    newRulePair = self.makeRuleAtDepth(depth, replica)
	    return newRulePair

    def startNewRules(self):
	while self.InstalledRules != []:
	    self.insertInAvailableRules(self.InstalledRules.pop())

    def endNewRules(self):
	if self.AvailableRules != []:
	    Globals.log.info("Warning! Not ALL RULES INSTALLED")
	    Globals.log.info(str(self.AvailableRules))

    def tryKeepRuleAtDepth(self, depth, replica):
	for i in range(0, len(self.InstalledRules)):
	    if self.InstalledRules[i]['NumWild'] == depth and self.InstalledRules[i]['Replica'] == replica:
		wild = self.InstalledRules.pop(i)
		self.TryKeepRules.append(wild)
		return

	Globals.log.info("Couldn't find matching rule for " + str(depth) + " " + str(replica))

    # =====================================
    # Helpers
    # =====================================

    def possMatchInList(self, wild, list):
	for i in range(0, len(list)):
	    if (wild['IP'] == list[i]['IP'] and wild['NumWild'] >= list[i]['NumWild']):
		return True
	return False

    def findRepDepthInList(self, depth, replica, list):
	for i in range(0, len(list)):
	    if (list[i]['NumWild'] == depth and list[i]['Replica'] == replica):
		return list[i]
	return None

    def findRuleInList(self, wild, list):
	for i in range(0, len(list)):
	    if (wild['IP'] == list[i]['IP'] and wild['NumWild'] == list[i]['NumWild']):
		return list[i]
	return None

    def insertInAvailableRules(self, wild): # Make Generic
	for i in range(0, len(self.AvailableRules)):
	    if self.AvailableRules[i]['NumWild'] < wild['NumWild']:
		self.AvailableRules.insert(i, wild)
		return

	self.AvailableRules.append(wild)
	return

    def insertRuleAtDepth(self, wild, depth, replica):	
	# Exact Rule
	if wild['NumWild'] == depth:
	    Globals.log.info("Exact")
	    rule = {'IP': wild['IP'], 'NumWild': wild['NumWild'], 'Replica': replica}
	    self.InstalledRules.append(rule)
	    return {'NewRule': rule, 'OldRuleList': [wild]}
	
	# Error  
	elif wild['NumWild'] < depth:
	    Globals.log.info("Error") 
	    return None

	leftwild = {'IP': wild['IP'], 'NumWild': wild['NumWild'] - 1, 'Replica': wild['Replica']}
	rule = self.insertRuleAtDepth(leftwild, depth, replica)

	rightwild = {'IP': wild['IP'] + (1 << (wild['NumWild'] - 1)), 'NumWild': wild['NumWild'] - 1, 'Replica': wild['Replica']}
	self.insertInAvailableRules(rightwild)

	return rule


    def makeRuleAtDepth(self, depth, replica):
	allValidRules = self.getAllValidRules(depth)

	# Try to find in Available List
	for i in range(0, len(allValidRules)):
	    newRulePair = self.makeRuleAtDepthHelper(allValidRules[i], self.AvailableRules, replica)
	    if (newRulePair != None):
		for i in range(0, len(newRulePair['OldRuleList'])):
		    self.AvailableRules.remove(newRulePair['OldRuleList'][i])
		self.InstalledRules.append(newRulePair['NewRule'])
		return newRulePair

	CombinedRules = self.AvailableRules
	CombinedRules.extend(self.TryKeepRules)
	for i in range(0, len(allValidRules)):
            newRulePair = self.makeRuleAtDepthHelper(allValidRules[i], CombinedRules, replica)
            if (newRulePair != None):
                for i in range(0, len(newRulePair['OldRuleList'])):
		    if self.findRuleInList(newRulePair['OldRuleList'][i], self.AvailableRules):
                        self.AvailableRules.remove(newRulePair['OldRuleList'][i])
		    else:
			self.TryKeepRules.remove(newRulePair['OldRuleList'][i])
                self.InstalledRules.append(newRulePair['NewRule'])
                return newRulePair

    def makeRuleAtDepthHelper(self, rule, list, replica):
	oldRule = self.findRuleInList(rule, list)
        if (oldRule != None):
	    return {'NewRule': {'IP': rule['IP'], 'NumWild': rule['NumWild'], 'Replica': replica}, 'OldRuleList': [oldRule]}

	if self.possMatchInList(rule, list) != True:
	    return None
	
	leftRule = self.makeRuleAtDepthHelper({'IP': rule['IP'], 'NumWild': rule['NumWild'] - 1}, list, replica)
	rightRule = self.makeRuleAtDepthHelper({'IP': rule['IP'] + (1 << (rule['NumWild'] - 1)), 'NumWild': rule['NumWild'] - 1}, list, replica)
	if (leftRule != None and rightRule != None):
	    leftOldList = leftRule['OldRuleList']
	    rightOldList = rightRule['OldRuleList']
	    leftOldList.extend(rightOldList)
	    return {'NewRule': {'IP': rule['IP'], 'NumWild': rule['NumWild'], 'Replica': replica}, 'OldRuleList': leftOldList}
	return None

    def getAllValidRules(self, depth):
	return self.getAllValidRulesHelper({'IP': 0, 'NumWild':32}, depth)

    def getAllValidRulesHelper(self, wild, depth):
	if wild['NumWild'] == depth:
	    return [wild]

	leftwild = {'IP': wild['IP'], 'NumWild': wild['NumWild'] - 1}
	leftRules = self.getAllValidRulesHelper(leftwild, depth)

	rightwild = {'IP': wild['IP'] + (1 << (wild['NumWild'] - 1)), 'NumWild': wild['NumWild'] - 1}
	rightRules = self.getAllValidRulesHelper(rightwild, depth)

	leftRules.extend(rightRules)
	return leftRules
