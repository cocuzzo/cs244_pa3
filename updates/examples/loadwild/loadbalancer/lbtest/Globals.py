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
#import nox.lib.openflow as openflow

log = logging.getLogger('nox.loadbalancer.lbtest.lbtest')

COMPONENT = None

HOME = '/home/mininet/Testing/'
ASSIGNLOG = open(HOME + 'assign.log', 'w')
TARGETLOG = open(HOME + 'target.log', 'w')
INSTALLLOG = open(HOME + 'install.log', 'w')
RULESLOG = open(HOME + 'rules.log', 'w')
STATSLOG = open(HOME + 'stats.log', 'w')
PORTSLOG = open(HOME + 'ports.log', 'w')
PATHSLOG = open(HOME + 'path.log', 'w')

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
		{'no': 1, 'mac': 0x000102030401, 'neighbors': [{'no': 2, 'port': 0}, {'no': 3, 'port': 1}], 'replicas': [], 'clients': []},
		{'no': 2, 'mac': 0x000102030402, 'neighbors': [{'no': 1, 'port': 0}, {'no': 4, 'port': 1}, {'no': 5, 'port': 2}], 'replicas': [], 'clients': []},
		{'no': 3, 'mac': 0x000102030403, 'neighbors': [{'no': 1, 'port': 0}, {'no': 4, 'port': 1}], 'replicas': [], 'clients': []},
		{'no': 4, 'mac': 0x000102030404, 'neighbors': [{'no': 2, 'port': 0}, {'no': 3, 'port': 1}, {'no': 5, 'port': 2}], 'replicas': [], 'clients': []},
		{'no': 5, 'mac': 0x000102030405, 'neighbors': [{'no': 2, 'port': 0}, {'no': 4, 'port': 1}], 'replicas': [], 'clients': []}
	   ]

ALPHAS = [
#		{'replica': 0, 'alphaTarget': 0, 'alphaAssign': 0}
	 ]


TARGETRULES = [
		{'ip': '0.0.0.0', 'wild': 31, 'replica': -1, 'traffic': 0L},
		{'ip': '128.0.0.0', 'wild': 30, 'replica': -1, 'traffic': 0L},
		{'ip': '192.0.0.0', 'wild': 30, 'replica': -1, 'traffic': 0L}
	      ]

TRANSITRULES = [
	       ]

INSTALLEDRULES = [
                {'ip': '0.0.0.0', 'wild': 30, 'replica': -1, 'traffic': 0L},
                {'ip': '64.0.0.0', 'wild': 30, 'replica': -1, 'traffic': 0L},
                {'ip': '128.0.0.0', 'wild': 29, 'replica': -1, 'traffic': 0L},
                {'ip': '160.0.0.0', 'wild': 29, 'replica': -1, 'traffic': 0L},
                {'ip': '192.0.0.0', 'wild': 29, 'replica': -1, 'traffic': 0L},
                {'ip': '224.0.0.0', 'wild': 29, 'replica': -1, 'traffic': 0L}
		]

PATHTABLE = [
	    ]

FORWARDINGTABLE = {}

MINTGTTHRESH = 0.7
MAXTGTTHRESH = 1.7

NUMREPLICAS = len(REPLICAS)

LASTALPHAMOD = 0
ALPHAFILE = '/home/mininet/Testing/alpha.txt'

MACREPLICAUPDATE = True
STATSUPDATE = True

ALPHA_CHECK_PERIOD = 800

PORT_STATS_PERIOD = 8
HARD_TIMEOUT = 60
SOFT_TIMEOUT = 60

EMA_CONSTANT = 0.66

PERIOD = 0

ENABLE_MULTIPATH = True
#ENABLE_MULTIPATH = False

def printNewPeriod():
    ASSIGNLOG.write("\n===========================")
    ASSIGNLOG.write("\t\tPERIOD " + str(PERIOD) + "\t\t")
    ASSIGNLOG.write("===========================\n")
    TARGETLOG.write("\n===========================")
    TARGETLOG.write("\t\tPERIOD " + str(PERIOD) + "\t\t")
    TARGETLOG.write("===========================\n")
    INSTALLLOG.write("\n===========================")
    INSTALLLOG.write("\t\tPERIOD " + str(PERIOD) + "\t\t")
    INSTALLLOG.write("===========================\n")
    RULESLOG.write("\n===========================")
    RULESLOG.write("\t\tPERIOD " + str(PERIOD) + "\t\t")
    RULESLOG.write("===========================\n")
    STATSLOG.write("\n===========================")    
    STATSLOG.write("\t\tPERIOD " + str(PERIOD) + "\t\t")
    STATSLOG.write("===========================\n")
    PORTSLOG.write("\n===========================")    
    PORTSLOG.write("\t\tPERIOD " + str(PERIOD) + "\t\t")    
    for i, switch in enumerate(SWITCHES):
        PORTSLOG.write('Switch: ' + str(switch['no']) + '\n')
	for j, neighbor in enumerate(switch['neighbors']):
            PORTSLOG.write('\tport: ' + str(neighbor['port']) + ' -> Switch ' + str(neighbor['no']) + '\n')
        for j, replica in enumerate(switch['replicas']):
	    for k, rep in enumerate(REPLICAS):
                if rep['no'] == replica:
                    PORTSLOG.write('\tport: ' + str(rep['port']) + ' -> Replica ' + str(rep['no']) + ' @ ' + rep['ip'] + '\n')
        for j, client in enumerate(switch['clients']):
            PORTSLOG.write('\tport: ' + str(client['port']) + ' -> Client ' + str(client['ip']) + '\n')
    PORTSLOG.write("===========================\n")
    PATHSLOG.write("\n===========================")
    PATHSLOG.write("\t\tPERIOD " + str(PERIOD) + "\t\t")
    PATHSLOG.write("===========================\n")




