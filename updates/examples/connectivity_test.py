#!/usr/bin/python

"""
Mininet Unit/Benchmarking Test for All Pairs connectivity
USAGE: sudo ./connectivity_test.py [OPTIONS]
Command Line Options:

"""

import sys
import re
flush = sys.stdout.flush
import os
cwd = os.getcwd().split('/')
parent = reduce(lambda s,n: s+'/'+n, cwd[1:-1], "")
sys.path.append(parent)
from frenetic_run import setup_env, fetch_subdirs

from mininet.net import init, Mininet
from mininet.node import KernelSwitch, UserSwitch, OVSKernelSwitch, RemoteController, NOX
from mininet.topo import Topo, Node
from mininet.log import lg
from mininet.log import info, error, debug, output
from mininet.cli import CLI
from mininet.term import makeTerm
import time
from optparse import OptionParser
import subprocess
from test_utils import *
import signal

validforwarding = ['hub','lsw','fls','adapt']
switchTypes = {'us' : UserSwitch, 'ovsk' : OVSKernelSwitch}
MAXHOSTS = 100
MININET = None
GOPTS = {}

def setNet(net):
    global MININET
    MININET = net

def startNet():
    global MININET
    if MININET != None:
        MININET.start()

def stopNet():
    global MININET
    if MININET != None:
        if MININET.terms:
            MININET.stopXterms()
        for host in MININET.hosts:
            host.terminate()
        for switch in MININET.switches:
            switch.stop()
        # If there are more controllers, I need to do more here
        # for controller in MININET.controllers:
        #    controller.stop()


def hostSweep(network, numHosts, numSwitches, wait,p=2,size=56):
    net=network
    hosts = net.hosts
    node = hosts[0]
    totallost = 0
    for i in range(1, p+1):
        packets = 0
        lost = 0
        ploss = None
        if not(GOPTS['quiet']):
           output('### Pass %i of %i:\n' % (i,p))
        if (wait > 0) and (i > 1):
            time.sleep(wait)
        for node in hosts:
            if not(GOPTS['quiet']):
                output('%s -> ' % (node.name))
            for dest in hosts:
                if node != dest:
                    if i > 1 and not(GOPTS['quiet']):
                        result = node.cmd('ping -i 0.1 -s %s -c5 %s' % (size,dest.IP()))
                    else:
                        result = node.cmd( 'ping -c1 ' + dest.IP())
                    sent, received = net._parsePing( result )
                    packets += sent
                    if received > sent:
                        if not(GOPTS['quiet']):        
                            error( '### Error: received too many packets')
                            error( '%s' % result )
                            node.cmdPrint( 'route' )
                        exit( 1 )
                    lost += sent - received
                    if not(GOPTS['quiet']):
                        output( ( '%s ' % dest.name ) if received else 'X ' )
            if not(GOPTS['quiet']):
                output( '\n' )
        ploss = 100 * lost / packets
        totallost += lost
        if not(GOPTS['quiet']):
            output( "    +++ Results: %i%% dropped (%d/%d lost)\n" % ( ploss, lost, packets ) )
    return totallost

def start(nh=4, ns=1, stype = 'us', ip="127.0.0.1", port="6633", pi=5, 
            fwd='lsw', val=2):
    init()
    passes = val
    # Initialize network
    noxfwd = {'lsw':'pyswitch', 'hub':'pyhub', 'fls':'sample_routing', 'adapt':'adaptive_routing'}
    noxapp = "FreneticApp"
    freneticapp = "benchmarks"
    freneticfun = "pc"
    args = [fwd]

    if GOPTS['remote']:
        net = Mininet( topo=LinearTopo(nh,ns), switch=switchTypes[stype],
                       controller=lambda name: RemoteController(name, defaultIP=ip, port=int(port)),
                       xterms=False, autoSetMacs=True)
    else:
        if GOPTS['nox']:
            noxapp = noxfwd[fwd]
        else:
            setup_env(freneticapp,args,freneticfun,fetch_subdirs(parent))
        
        net = Mininet( topo=LinearTopo(nh,ns), switch=switchTypes[stype],
                       controller=lambda name: NOX(name, noxapp),
                       xterms=False, autoSetMacs=True)

    setNet(net)
    startNet()

    INIT = time.time()

    if not GOPTS['quiet']:
        output("  *** Network Initialized in %s seconds***\n" % str(INIT-GOPTS['start']))

    if not(GOPTS['arp']):
        net.staticArp()
        if not GOPTS['quiet']:
            output("  *** Network Statically ARP'ed in %s seconds***\n" % str(time.time()-INIT))

    netElems = {}
    netElems = buildNetElems(GOPTS['debug'],net)

    if GOPTS['agg']:
        p = {}

        if GOPTS['debug']:
            qopt = ""
        else:
            qopt = "-q "
        pcmd = 'sudo tshark -a duration:%s ' + qopt + '-i %s -z io,stat,0,'

        justhosts = map(lambda h:h.name, net.hosts)
        for s in net.switches:
            for swifname in s.connection.keys():
                (h, hifname) = s.connection[swifname]
                [hostname,ifname] = hifname.split("-")
                if hostname in justhosts:
                    cmd = pcmd % (str(nh*4),swifname)
                    p[swifname] = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if GOPTS['debug']:
                        print "Beginning packet capture on interface %s..." % swifname

    # Change verbosity so that the output of CLI commands will display
    time.sleep(6)

    if GOPTS['debug']:
        output(netElems['s101'].cmd('dpctl show unix:/tmp/s101'))

    r = hostSweep(net, nh, ns, 0,passes)
    #r = net.pingall()

    # Despite the fact that the pings are blocking calls 
    # which wait for a result, it seems that tshark needs
    # additional time to 'catch up'
    time.sleep(int(pi*1.5))

    # Wait for capture processes to finish
    if GOPTS['agg']:
        for proc in p.values():
            proc.wait()

    if not GOPTS['quiet']:
        lg.setLogLevel('output')

    if GOPTS['dump']:
        dumpFlows(stype,net)
    
    ### Stop controller, but wait to kill mininet
    if not GOPTS['remote']:
        netElems['c0'].stop()
    
    if GOPTS['agg']:
        # Grab network capture data
        total = 0
        rexp = re.compile('000.000-[\s]+[\d]+[\s]+[\d]+', re.IGNORECASE)
        for (k,proc) in p.items():
            out = proc.stdout.read()
            err = proc.stderr.read()
            if GOPTS['debug']:
                print k
                print err
                print out
            l = rexp.findall(out)
            for e in l:
                x = e.split()
                [n] = x[-1:]
                total += int(n)

    if not(GOPTS['quiet'] or GOPTS['agg']):
        if r == 0:
            output("## SUCCESS: No Lost Packets ##\n")
        else:
            output("## FAIL: %i Lost Packet(s) ##\n" % r)
        retcode = r
    elif GOPTS['agg']:
        output('\n###$%s$###\n' % total)
        retcode = total
    elif GOPTS['quiet']:
        retcode = r
    else:
        retcode = 0
    return retcode

def go(cargs=None):
    global GOPTS
    lg.setLogLevel('output')
    parser = CommonParser('connectivity_test.py')
    parser.add_option('-p', '--num-passes', action="store",dest='passes', type='int', default=2,
                        help="Number of passes through the network.")

    (options, args) = parser.parse_args(cargs)

    if options.remote_nox and options.nox_test:
        parser.error("Run reference NOX test without the -r option.")
    if (options.numhosts < 2 or options.numhosts > MAXHOSTS):
        parser.error("Need at least 2 hosts. Maximum of %s" % str(MAXHOSTS))    
    if not(options.remote_nox) and options.controller != '127.0.0.1:6633':
        parser.error("Specified a remote controller address, but -r remote NOX mode not specified.")
    if not(options.forwarding.lower() in validforwarding):
        parser.error("Please specify a valid forwarding policy for the experiment.  hub | lsw | flw.")

    (ip,port) = check_controller(options.controller)
    if (ip,port) == (None,None):
        parser.error("Bad IP:Port specified for controller.")

    GOPTS = setFlags(dump_flows=options.dump_flows,nox_test=options.nox_test,
             remote_nox=options.remote_nox,flow_size=options.flow_size,
             debugp=options.debug,interrupt=options.interrupt,quiet=options.quiet,
             agg=options.agg,full_arp=options.arp,verify=options.verify)

    GOPTS['interrupt'] = options.interrupt
    interval = options.interval

    # QUIET mode trumps many options
    if GOPTS['quiet']:
        GOPTS['debug'] = False
        GOPTS['dump'] = False
        GOPTS['interrupt'] = False
        numpasses = 2
        GOPTS['flowsize'] = 56
        interval = 1
        

    GOPTS['start'] = time.time()
    # Initialize and run 
    init()
    retcode = start(options.numhosts, options.numswitches, options.st,
                    ip, port, interval, options.forwarding.lower(), options.passes)
    return retcode

if __name__=='__main__':
    retcode = go()
    stopNet()
    exit(retcode)

