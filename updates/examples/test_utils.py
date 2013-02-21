#!/usr/bin/python

import sys
flush = sys.stdout.flush
from mininet.net import init, Mininet
from mininet.node import KernelSwitch, UserSwitch, OVSKernelSwitch, RemoteController
from mininet.topo import Topo, Node
from mininet.log import lg
from mininet.log import info, error, debug, output
from mininet.cli import CLI
from optparse import OptionParser
import re

def setFlags(dump_flows=False,nox_test=False,remote_nox=False,flow_size=958,
             debugp=False,interrupt=False,quiet=False,agg=False,full_arp=False,
             verify=False):
    opts = {'dump':False, 'nox':False, 'remote':False, 'flowsize':958, 'start':0,
            'debug':False, 'interrupt':False, 'quiet':False, 'agg': False,'arp':False,
            'verify':False}
    opts['dump'] = dump_flows
    opts['nox'] = nox_test
    opts['remote'] = remote_nox
    opts['flowsize'] = flow_size
    opts['debug'] = debugp
    opts['interrupt'] = interrupt
    opts['quiet'] = quiet
    opts['agg'] = agg
    opts['arp'] = full_arp
    opts['verify'] = verify

    if opts['quiet']:
        opts['debug'] = False
        opts['dump'] = False
        opts['interrupt'] = False
        opts['verify'] = True
    return opts.copy()

class LinearTopo(Topo):

    def __init__(self, numHosts=4, numSwitches=1):

        # Add default members to class.
        super(LinearTopo, self ).__init__()

        # Create hosts and switches 
        # Hosts numbered 1..numHosts
        # Switches numbered 101..numSwitches
        hosts = range(1,numHosts+1)
        switches = range(101,numSwitches+101)
        for i in hosts:
            self.add_node(i, Node(is_switch=False))
        for i in switches:
            self.add_node(i, Node(is_switch=True))

        # Connect Switches in linear topology
        for s in switches[:-1]:
            self.add_edge(s, s+1)

        # Connect nodes, divide them evenly across the switches
        k = 101
        h = hosts[:]
        hps = max(1,len(hosts) // len(switches))
        while len(h) > 0:
            l = h[:hps]
            h = h[hps:]
            for j in l:
                self.add_edge(k,j)
            if [k] == switches[-1:]:
                k = 101
            else:
                k += 1

        # Consider all switches and hosts 'on'
        self.enable_all()

def getControllerOutput(res):
    regexp = re.compile(res, re.IGNORECASE)
    f=open('/tmp/c0.log')
    noxOutput = f.read()
    result = regexp.findall(noxOutput)
    return result

# Command line input validator
def check_ip(i):
    l = i.split(".")
    if len(l) < 4 or len(l) > 4:
        return False
    else:
        for o in l:
            if not(o.isdigit()):
                return False
            if int(o) < 0 or int(o) > 255:
                return False
        return True

# Command line input validator
def check_controller(c):
    l = c.split(":")
    if l == [c]:
        # Should be a single IP
        if check_ip(c):
            return (c,"6633")
        else:
        # Maybe it's a port
            if c.isdigit():
                if (int(c) > 0 and int(c) < 65536):
                    return("127.0.0.1",c)
                else:
                    #parser.error("Bad IP:Port")
                    return (None,None)
            else:
                #parser.error("Bad IP:Port")
                return (None,None)
    elif len(l) > 2:
        #parser.error("Bad IP:Port")
        return (None,None)
    else:
        [ip,port] = l
        if check_ip(ip):
            if port.isdigit():
                if (int(port) > 0 and int(port) < 65536):
                    return (ip,port)
                else:
                    #parser.error("Bad Port")
                    return (None,None)
            else:
                #parser.error("Bad Port")
                return (None,None)
        else:
            #parser.error("Bad IP")
            return (None,None)

def CommonParser(name=None):
    if name is None:
        usage = "Usage: %prog [options]"
    else:
        usage = "Usage: %s [options]" % name
    parser = OptionParser(usage=usage)
    parser.add_option('-D', '--debug', action='store_true', dest='debug', default=False,
                        help='Debug the script with additional output.')
    parser.add_option('-d', '--dump-flows', action='store_true', dest='dump_flows', default=False,
                        help='Dump flow table at the conclusion of the experiment.')
    parser.add_option('-r', '--remote-nox', action='store_true', dest='remote_nox', default=False,
                        help="Use a remote NOX instance run separately specified by -c/--controller-address."
                        + "This is helpful for debugging.")
    parser.add_option('-N', '--test-nox', action='store_true', dest='nox_test', default=False,
                        help="Run the reference pure NOX implementation.")
    parser.add_option('-n', '--num-hosts', action='store',type='int', dest='numhosts', default=4,
                        help="Specify the number of hosts to use. ")
    parser.add_option('-s', "--num-switches", action="store", type='int', dest="numswitches", default=1,
                        help="Number of switches.")
    parser.add_option('-t', "--switch-type", action="store", type='string', dest="st", default='us',
                        help="Type of switch to use [us|ovsk]. us = UserSwitch, ovsk = OpenVSwitch Kernel")
    parser.add_option('-c', "--controller-address", action="store", type='string', dest="controller", default='127.0.0.1:6633',
                        help="If specified, connects to a remote controller instance at IP:Port." +
                             "  Ignored unless -r/--remote-nox is specified.")
    parser.add_option('-v', "--verify-output", action="store_true", dest="verify", default=False,
                        help="Run as a unit test and verify the stats reported by NOX with a packet capture")
    parser.add_option('-I', "--interrupt-execution", action="store_true", dest="interrupt", default=False,
                        help="Interrupt execution to issue interactive commands at a CLI before termination.")
    parser.add_option('-q', '--quiet-unit-test', action="store_true",dest='quiet', default=False,
                        help="Run in unit test mode. Don't print anything to the console.")
    parser.add_option('-i', "--polling-interval", action="store", type='int', dest="interval", default=5,
                        help="Specify the polling interval for the stats collection.")
    parser.add_option('-f', "--forwarding-policy", action="store", type='string', dest="forwarding", default="lsw",
                        help="Specify the forwarding policy for the experiment.  hub | lsw | fls.")
    parser.add_option('-F', '--flow-size', action='store',type='int', dest='flow_size', default=958,
                        help="Specify size of the packets to be sent in bytes (max 1471). ")
    parser.add_option('-a', "--aggregate-mode", action="store_true", dest="agg", default=False,
                        help="Report aggregate bytes on all network interfaces")
    parser.add_option('-A', "--full-arp", action="store_true", dest="arp", default=False,
                        help="Do NOT setup static ARP caches.")

    return parser

def dumpFlows(st,net):
    idx = 0
    for s in net.switches:
        output("=== " + s.name + " Flow Table ===\n")
        if st == 'us':
            output(s.cmd('dpctl dump-flows unix:/tmp/' + s.name))
        elif st == 'ovsk':
            output(s.cmd('dpctl dump-flows nl:' + idx))
            idx += 1

def buildNetElems(dbg,net):
    netElems = {}
    for h in net.hosts:
        netElems[h.name] = h
        if dbg:
            output("=== " + h.name + " Connections ===\n")
            for (k,v) in h.connection.items():
                output(str(k) + " : " + str(v) +"\n")

    for s in net.switches:
        netElems[s.name] = s
        if dbg:
            output("=== " + s.name + " Connections ===\n")
            for (k,v) in s.connection.items():
                output(str(k) + " : " + str(v) +"\n")
    for c in net.controllers:
            netElems[c.name] = c
    return netElems
