# ==========================================
# Author: Richard Wang
# Contact: rwthree@princeton.edu
#
# File contain the global variables
# Note: ALPHAFILE is necessary contains (Replica #, Alpha) pair
#   Ex: 1, 3
#       2, 4
#       3, 1
# ==========================================

import logging
import nox.lib.openflow as openflow

log = logging.getLogger('nox.loadbalancer.lbtest.lbtest')
RULESLOG = open('/home/mininet/Testing/rules.txt', 'w')

# Global Data
ARP_TYPE = 0x0806
IP_TYPE = 0x0800

VIP = '10.0.0.5'
VMAC = "11:22:33:44:55:66"
SWITCHID = 0x000102030401
DUMMYID = 0x000403020101
REPLICAS = [
                {'no': 1, 'port':1, 'ip':'10.0.0.1', 'mac':''},
                {'no': 2, 'port':2, 'ip':'10.0.0.2', 'mac':''},
                {'no': 3, 'port':3, 'ip':'10.0.0.3', 'mac':''}
           ]
SWITCHES = [
		{'no': 1, 'mac': 0x000102030401, 'neighbors': [{'no': 2, 'port': 0}, {'no': 3, 'port': 1}], 'replicas': []},
		{'no': 2, 'mac': 0x000102030402, 'neighbors': [{'no': 1, 'port': 0}, {'no': 4, 'port': 1}, {'no': 5, 'port': 2}], 'replicas': []},
		{'no': 3, 'mac': 0x000102030403, 'neighbors': [{'no': 1, 'port': 0}, {'no': 4, 'port': 1}], 'replicas': []},
		{'no': 4, 'mac': 0x000102030404, 'neighbors': [{'no': 2, 'port': 0}, {'no': 3, 'port': 1}, {'no': 5, 'port': 2}], 'replicas': []},
		{'no': 5, 'mac': 0x000102030405, 'neighbors': [{'no': 2, 'port': 0}, {'no': 4, 'port': 1}], 'replicas': []}
	   ]
NUMREPLICAS = len(REPLICAS)
CACHE_TIMEOUT = openflow.OFP_FLOW_PERMANENT

ALPHAFILE = '/home/mininet/Testing/alpha.txt'

STATSFILE = open('/home/mininet/Testing/Stats.txt', 'w')

PORT_STATS_PERIOD = 5

HARD_TIMEOUT = 60
SOFT_TIMEOUT = 60
