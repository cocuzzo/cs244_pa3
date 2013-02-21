#!/usr/bin/python

import time
import os
import sys

"""
This example shows how to create an empty Mininet object
(without a topology object) and add nodes to it manually.
"""

from mininet.net import Mininet
from mininet.node import Controller, NOX
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def customNet():

    "Create an empty network and add nodes to it."

    net = Mininet( controller=lambda name: NOX( name, 'lbtest') )
#    net = Mininet( controller=Controller )

    info( '*** Adding controller\n' )
    net.addController( 'c0' )

    info( '*** Adding replicas + clients\n' )
    c1 = net.addHost('c1', ip='1.0.0.1')
    c2 = net.addHost('c2', ip='128.0.0.1')
    c3 = net.addHost('c3', ip='192.0.0.1')
    c4 = net.addHost('c4', ip='96.0.0.1')
    c5 = net.addHost('c5', ip='64.0.0.1')
    c6 = net.addHost('c6', ip='16.0.0.2')
    c7 = net.addHost('c7', ip='90.0.0.2')
    c8 = net.addHost('c8', ip='199.0.0.2')
    c9 = net.addHost('c9', ip='212.0.0.2')
    c10 = net.addHost('c10', ip='9.0.0.3')
    c11 = net.addHost('c11', ip='13.0.0.3')
    c12 = net.addHost('c12', ip='71.0.0.3')
    c13 = net.addHost('c13', ip='89.0.0.3')
    c14 = net.addHost('c14', ip='93.0.0.3')
    c15 = net.addHost('c15', ip='111.0.0.3')
    c16 = net.addHost('c16', ip='122.0.0.3')
    c17 = net.addHost('c17', ip='131.0.0.3')
    c18 = net.addHost('c18', ip='174.0.0.3')
    c19 = net.addHost('c19', ip='187.0.0.3')
    c20 = net.addHost('c20', ip='137.0.0.3')

    r1 = net.addHost('r1', ip='10.0.0.1')
    r2 = net.addHost('r2', ip='10.0.0.2')
    r3 = net.addHost('r3', ip='10.0.0.3')

    info( '*** Adding switch\n' )
    s1 = net.addSwitch( 's1', mac='00:01:02:03:04:01')
    s2 = net.addSwitch( 's2', mac='00:01:02:03:04:02')
    s3 = net.addSwitch( 's3', mac='00:01:02:03:04:03')
    s4 = net.addSwitch( 's4', mac='00:01:02:03:04:04')
    s5 = net.addSwitch( 's5', mac='00:01:02:03:04:05')

    info( '*** Creating links\n' )
    s1.linkTo(s2, port1=0, port2=0)
    s1.linkTo(s3, port1=1, port2=0)
    s2.linkTo(s4, port1=1, port2=0)
    s3.linkTo(s4, port1=1, port2=1)
    s2.linkTo(s5, port1=2, port2=0)
    s4.linkTo(s5, port1=2, port2=1)

    r1.linkTo(node2=s1, port2=2)
    r2.linkTo(node2=s2, port2=3)
    r3.linkTo(node2=s3, port2=2)

    c1.linkTo(s1)
    c2.linkTo(s2)
    c3.linkTo(s3)
    c4.linkTo(s4)
    c5.linkTo(s5)
    c6.linkTo(s1)
    c7.linkTo(s2)
    c8.linkTo(s3)
    c9.linkTo(s4)
    c10.linkTo(s5)
    c11.linkTo(s1)
    c12.linkTo(s2)
    c13.linkTo(s3)
    c14.linkTo(s4)
    c15.linkTo(s5)
    c16.linkTo(s1)
    c17.linkTo(s2)
    c18.linkTo(s3)
    c19.linkTo(s4)
    c20.linkTo(s5)

    info( '*** Starting network\n')
    net.start()

    info( '*** Init Replicas\n')
    r1.sendCmd('./mongoose/mongoose &')
    r2.sendCmd('./mongoose/mongoose &')
    r3.sendCmd('./mongoose/mongoose &')

    NUMTESTS = 10

    pid = os.fork()
    if pid == 0:
        time.sleep(10)
	for i in range(0, NUMTESTS):
            c1.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c01')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(11)
	for i in range(0, NUMTESTS):
            c2.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c02')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(12)
	for i in range(0, NUMTESTS):
            c3.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c03')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(13)
	for i in range(0, NUMTESTS):
            c4.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c04')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(14)
	for i in range(0, NUMTESTS):
            c5.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c05')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(15)
	for i in range(0, NUMTESTS):
            c6.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c06')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(16)
	for i in range(0, NUMTESTS):
            c7.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c07')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(17)
	for i in range(0, NUMTESTS):
            c8.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c08')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(18)
	for i in range(0, NUMTESTS):
            c9.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c09')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(19)
	for i in range(0, NUMTESTS):
            c10.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c10')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(20)
        for i in range(0, NUMTESTS):
            c11.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c11')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(21)
        for i in range(0, NUMTESTS):
            c12.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c12')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(22)
        for i in range(0, NUMTESTS):
            c13.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c13')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(23)
        for i in range(0, NUMTESTS):
            c14.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c14')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(24)
        for i in range(0, NUMTESTS):
            c15.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c15')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(25)
        for i in range(0, NUMTESTS):
            c16.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c16')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(26)
        for i in range(0, NUMTESTS):
            c17.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c17')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(27)
        for i in range(0, NUMTESTS):
            c18.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c18')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(28)
        for i in range(0, NUMTESTS):
            c19.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c19')
            time.sleep(10)
        sys.exit(0)
    pid = os.fork()
    if pid == 0:
        time.sleep(29)
        for i in range(0, NUMTESTS):
            c20.cmd('wget 10.0.0.5:8080/ServerData/dummyfile --directory-prefix=HTML-c20')
            time.sleep(10)
        sys.exit(0)








    info( '*** Running CLI\n' )
    CLI( net )

    info( '*** Stopping network' )
    net.stop()

    os.system('sudo killall wget')
    os.system('sudo killall python')
    os.system('sudo killall mongoose')
    os.system('sudo killall /home/mininet/noxcore/build/src/.libs/lt-nox_core')



if __name__ == '__main__':
    setLogLevel( 'info' )
    customNet()
