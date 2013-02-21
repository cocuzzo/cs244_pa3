import IPRules
import Globals
from nox.lib.packet.packet_utils import mac_to_str

def updatePathCounters(switchNum, ports):
    switch = getSwitch(Globals.SWITCHES, switchNum)
    Globals.PATHSLOG.write(str(Globals.PERIOD) + ' Switch: ' + str(switch['no']) + ' -> ')
    for i, port in enumerate(ports):
	for j, neighbor in enumerate(switch['neighbors']):
            if port['port_no'] == neighbor['no']:
		Globals.PATHSLOG.write('S' + str(neighbor['no']) + ':' + str(port['rx_packets']) + ' ')
    Globals.PATHSLOG.write('\n')

def updateInstalledCounters(switchNum, ports):
    switch = getSwitch(Globals.SWITCHES, switchNum)
    Globals.log.info(mac_to_str(switchNum) + ' has ' + str(len(ports)) + ' ports')
    for i, port in enumerate(ports):
        for j, client in enumerate(switch['clients']):
	    client['oldCount'] = client['newCount']
            if port['port_no'] == client['port']:
		client['newCount'] = port['rx_packets']
#                client['newCount'] = Globals.EMA_CONSTANT * port['rx_packets'] + (1 - Globals.EMA_CONSTANT) * client['oldCount']
#		client['newCount'] = port['rx_packets']
		client['avg'] = Globals.EMA_CONSTANT * (client['newCount'] - client['oldCount']) + (1 - Globals.EMA_CONSTANT) * client['oldCount']
		Globals.STATSLOG.write(mac_to_str(switchNum) + ' ' + str(client['ip']) + ' -> ' + str(port['rx_packets']) + '\n')

def updateInstallTable():
    for i, install in enumerate(Globals.INSTALLEDRULES):
        install['traffic'] = 0L
    for i, transit in enumerate(Globals.TRANSITRULES):
        transit['traffic'] = 0L

    for i, switch in enumerate(Globals.SWITCHES):
        for j, client in enumerate(switch['clients']):
            for k, install in enumerate(Globals.INSTALLEDRULES):
                if IPRules.isChild(install, client['ip']):
#                    install['traffic'] += client['newCount']
#                    install['traffic'] = Globals.EMA_CONSTANT * client['newCount'] + (1 - Globals.EMA_CONSTANT) * install['traffic']
#		    install['traffic'] = long(Globals.EMA_CONSTANT * (client['newCount'] - client['oldCount']) + ((1 - Globals.EMA_CONSTANT) * install['traffic']))
		    install['traffic'] += client['avg']

            for k, transit in enumerate(Globals.TRANSITRULES):
                if IPRules.isChild(transit, client['ip']):
#                    transit['traffic'] += client['newCount']
#                    transit['traffic'] = Globals.EMA_CONSTANT * client['newCount'] + (1 - Globals.EMA_CONSTANT) * transit['traffic']
#		    transit['traffic'] = long(Globals.EMA_CONSTANT * (client['newCount'] - client['oldCount']) + (1 - Globals.EMA_CONSTANT) * transit['traffic'])
		    transit['traffic'] += client['avg']

            
    for i, target in enumerate(Globals.TARGETRULES):
        sumTraffic = 0
        for j, install in enumerate(Globals.INSTALLEDRULES):
            if IPRules.isChild(target, install['ip']):
		sumTraffic += install['traffic']
	for j, transit in enumerate(Globals.TRANSITRULES):
            if IPRules.isChild(target, transit['ip']):
		sumTraffic += transit['traffic']
        target['traffic'] = sumTraffic
        

def printStats():
    for i, switch in enumerate(Globals.SWITCHES):
        for j, client in enumerate(switch['clients']):
            Globals.STATSLOG.write('Client ' + client['ip'] + ' -> ' + str(client['newCount']) + '\n')

    for i, install in enumerate(Globals.INSTALLEDRULES):
        if install['traffic'] != 0L:
            Globals.STATSLOG.write('Install ' + install['ip'] + '/' + str(install['wild']) + ' -> ' + str(install['traffic']) + '\n')

    for i, transit in enumerate(Globals.TRANSITRULES):
        if transit['traffic'] != 0L:
            Globals.STATSLOG.write('Transit ' + transit['ip'] + '/' + str(transit['wild']) + ' -> ' + str(transit['traffic']) + '\n')

def getSwitch(switches, mac):
    for i, switch in enumerate(switches):
        if switch['mac'] == mac:
            return switch

    return None
