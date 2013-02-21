#! /usr/bin/python

# install the multicast library by typing the following:
#   easy_install py-multicast

import sys
import multicast
from multicast import network

config = network.ifconfig()
ifc = config.keys()[0]
address = config[ifc].addresses[0]
port = 12345

if sys.argv[1] == "send":
    config = network.ifconfig()     
    sender = multicast.DatagramSender(address, port, "239.0.0.1", 1234)
    data = "Hello world"
    sender.write(data)
    print "Multicast: [%s]" % data
else:
    receiver = multicast.MulticastUDPReceiver(ifc, "239.0.0.1", 1234 )
    print "Waiting for multicast traffic..."
    data = receiver.read()
    print "Received: [%s]" % data
    receiver.close()
