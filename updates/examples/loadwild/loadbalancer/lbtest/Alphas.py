# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# Performs simple parsing of an "Alpha" file
# Contents are simply (Server #, Alpha)
# Ex: 
# 1, 3
# 2, 0
# 3, 1
# ==========================================

import random
import Globals

def updateAlphas(newAlphas, oldTargetList):
    for i in range(0, len(newAlphas)):
        found = False
	for j in range(0, len(Globals.ALPHAS)):
	    if newAlphas[i]['replica'] == Globals.ALPHAS[j]['replica']:
                Globals.ALPHAS[j]['alphaTarget'] = newAlphas[i]['alphaTarget']
                found = True
        if not found:
	    Globals.ALPHAS.append({'replica': newAlphas[i]['replica'], 'alphaTarget': newAlphas[i]['alphaTarget'], 'alphaAssign': 0})

    for i in range(0, len(oldTargetList)):
        for j in range(0, len(Globals.ALPHAS)):
            if oldTargetList[i]['replica'] == Globals.ALPHAS[j]['replica']:
                Globals.ALPHAS[j]['alphaAssign'] -= 1

def getAlphas(filename):
    file = open(filename, 'r+')

    alphalist = []

    for line in file:
        line2 = line.replace('\n', '')
	line3 = line2.replace(' ', '')
	l = line3.split(',')
        for i, replica in enumerate(Globals.REPLICAS):
            if replica['no'] == int(l[0]):
                if replica['mac'] != '':
	            alphalist.append({'replica': int(l[0]), 'alphaTarget': int(l[1]), 'alphaAssign': 0})
		else:
	            alphalist.append({'replica': int(l[0]), 'alphaTarget': 0, 'alphaAssign': 0})
    file.close()

    return alphalist

def distributeAlphas(newAlphas, oldAlphas, totalAssigns):
    sumTarget = sumAllAlphaTarget(newAlphas)
    sumOldAssigns = sumAllAlphaAssign(oldAlphas)

    for i in range(0, len(newAlphas)):
	for j in range(0, len(oldAlphas)):
	    if newAlphas[i]['replica'] == oldAlphas[j]['replica'] and newAlphas[i]['alphaTarget'] != 0:
		numAssigns = sumOldAssigns + totalAssigns
		newAssigns = numAssigns / sumTarget - oldAlphas[j]['alphaAssign']
		Globals.log.info('New Assigns: ' + str(newAssigns))
		if newAssigns > 0:
                    newAlphas[i]['alphaAssign'] = newAssigns

    return newAlphas

def distributeEven(newAlphas, totalAssigns):
    remainingAssigns = totalAssigns - sumAllAlphaAssign(newAlphas)
    sumTarget = sumAllAlphaTarget(newAlphas)

    for i in range(0, len(newAlphas)):
	if sumTarget != 0:
	    newAlphas[i]['alphaAssign'] += int(newAlphas[i]['alphaTarget'] * remainingAssigns / sumTarget)
    return newAlphas

#def distributeOld(newAlphas, oldAlphas, totalAssigns):
#    remainingAssigns = totalAssigns - sumAllAlphaAssign(newAlphas)
#    totalAssigns = sumAllAlphaAssign(oldAlphas) + sumAllAlphaAssign(newAlphas)
#
#    changes = True
#    while changes:
#	changes = False
#
#        for i in range(0, len(newAlphas)):
#	    if remainingAssigns == 0:
#		return newAlphas
#
#	    for j in range(0, len(oldAlphas)):
#		if newAlphas[i]['replica'] == oldAlphas[j]['replica']:
#		    totalAssign = oldAlphas[j]['alphaAssign'] + newAlphas[i]['alphaAssign']
#                    totalTarget = newAlphas[i]['alphaTarget']
#                    if totalAssign == 0: totalAssign = 1
#		    if totalTarget == 0: totalTarget = 1
#                    if (totalAssigns / totalAssign) > (totalAssigns / totalTarget):
#                        newAlphas[i]['alphaAssign'] += 1
#		        remainingAssigns -= 1
#		        changes = True
#
#    return newAlphas

def distributeRemaining(newAlphas, totalAssigns):
    remainingAssigns = totalAssigns - sumAllAlphaAssign(newAlphas)

    rand = random.randint(0, Globals.NUMREPLICAS - 1)
    while remainingAssigns > 0 and sumAllAlphaTarget(newAlphas) != 0:
        if newAlphas[rand]['alphaTarget'] != 0:
            newAlphas[rand]['alphaAssign'] += 1
	    remainingAssigns -= 1
	rand += 1
	if rand > Globals.NUMREPLICAS - 1:
	    rand = 0

    return newAlphas

def printAlphas(alphas):
    Globals.ASSIGNLOG.write('Current Alpha Assignments:\n')
    for i in range(0, len(alphas)):
	Globals.ASSIGNLOG.write('\tReplica ' + str(alphas[i]['replica']) + ' is currently assigned ' + str(alphas[i]['alphaAssign']) + ' wants to have ' + str(alphas[i]['alphaTarget']))
	Globals.ASSIGNLOG.write('\n')


# =======================================
# Helper Functions
# =======================================

def sumAllAlphaTarget(alphalist):
    sum = 0
    for i in range(0, len(alphalist)):
	sum = sum + alphalist[i]['alphaTarget']
    return sum

def sumAllAlphaAssign(alphalist):
    sum = 0
    for i in range(0, len(alphalist)):
        sum = sum + alphalist[i]['alphaAssign']
    return sum

