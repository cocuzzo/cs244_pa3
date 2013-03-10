#!/usr/bin/python

################################################################################
# The Frenetic Project                                                         #
# frenetic@frenetic-lang.org                                                   #
################################################################################
# Licensed to the Frenetic Project by one or more contributors. See the        #
# NOTICE file distributed with this work for additional information            #
# regarding copyright and ownership. The Frenetic Project licenses this        #
# file to you under the following license.                                     #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided the following conditions are met:       #
# - Redistributions of source code must retain the above copyright             #
#   notice, this list of conditions and the following disclaimer.              #
# - Redistributions in binary form must reproduce the above copyright          #
#   notice, this list of conditions and the following disclaimer in            #
#   the documentation or other materials provided with the distribution.       #
# - The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################
# /updates/run.py                                                              #
# Update front-end                                                             #
################################################################################
import optparse
import os
import sys
from multiprocessing import Process, Queue
from multiprocessing.connection import Client,Listener
from mininet.log import lg, output
from mininet.net import init, Mininet
from mininet.node import UserSwitch, NOX
from mininet.cli import CLI
# import yappi
import string

default_topology = "Topology"
default_function = "main"
default_args = []
default_independent = False
default_nox_path = "/home/ubuntu/nox-classic/build/src/nox_core"
default_verbose = False 
default_justnox = False
default_nox_only = False
default_cli = False
default_timeout = None
default_experiment_mode = False
default_nodes = 4
mininet = None

def fetch_subdirs(directory = os.getcwd()):
    """Returns a list including this directory and all of its subdirectories"""
    return [dirpath for (dirpath, dirnames, filenames) in os.walk(directory)]

def setup_env(module, topology_module, function, args, topology, dirs, experiment_mode, num_nodes):
    """set up environment variables for Update to pull from
    module: the name of the module to import, minimally qualified
        (routing, NOT nox.coreapps.examples.routing)
    params: a list of parameters to pass to the function.  Will be packed into a
        single whitespace-separated list.
    function: name of the function inside the module to call
    dirs: list of directories to include in the python path.  This is important
        when using frenetic because NOX does weird things to python's
        expectations of where files will be.
    """
    os.environ["UPDATE_MODULE"] = module
    os.environ["UPDATE_TOPOLOGY_MODULE"] = topology_module
    os.environ["UPDATE_FUNCTION"] = function
    os.environ["UPDATE_ARGS"] = ",".join(args)
    os.environ["UPDATE_TOPOLOGY"] = topology
    os.environ["UPDATE_LIBS"] = " ".join(dirs)
    if experiment_mode:
        os.environ["UPDATE_EXPERIMENT_MODE"] = str(experiment_mode)
    os.environ["UPDATE_NUM_NODES"] = str(num_nodes)
    # MJR: Added for debugging
    os.environ["PYTHONUNBUFFERED"] = "True"

def import_directories(dirs):
    """Prepends all the directories in dirs onto sys.path, causing python to
    look there first for modules"""
    sys.path = reduce((lambda paths, path: paths + [path]), sys.path, dirs)

def get_function_by_name(module, function):
    """Imports module, and returns function"""
    module_object = __import__(module, globals(), locals(), [], -1)
    return getattr(module_object, function)

def getControllerOutput():
    return open('/tmp/c0.log').read()

signal_address = ('localhost', 3366)

def receive_signal(listener, q):
    conn = listener.accept()
    s = conn.recv()
    q.put(s)
    listener.close()
    return 

def send_signal(s):
    conn = Client(signal_address)
    conn.send(s)
    conn.close()
    return

def run_nox():
    nox_command = os.path.expanduser(default_nox_path)
    nox_dir = os.path.dirname(nox_command)
    os.chdir(nox_dir)

    nox_command += " -v"
    command = "%s -i ptcp:6633 %s" % (nox_command,"UpdateApp")
    os.system(command)

def execute(module,
            topology_module = None,
            topology=default_topology,
            function=default_function,
            args=default_args,
            cli=default_cli,
            timeout=default_timeout,
            nodes=default_nodes,
            nox_path=default_nox_path,
            verbose=default_verbose,
            experiment_mode=default_experiment_mode):

    nodes = int(nodes)
    topology_module = module + "_topo" if topology_module is None else topology_module

    dirs = fetch_subdirs()
    setup_env(module, topology_module, function, args, topology, dirs, experiment_mode, nodes)
    import_directories(dirs)

    q = Queue()
    listener = Listener(signal_address)
    wait = Process(target=receive_signal, args=(listener,q))
    wait.daemon = True
    wait.start()

    # if experiment_mode:
    #     update_application = get_function_by_name(module, function)
    #     initial_topology = get_function_by_name(topology_module, topology)
    #     setup = get_function_by_name("update_lib", "setup")
    #     inst = DummyComponent(args, update_application, setup, initial_topology)
    #     os._exit(0)
        
    if experiment_mode:
        # yappi.start()
        nox = Process(target=run_nox)
        nox = NOX("c0", "UpdateApp")
        nox.start()
        lg.setLogLevel('output')        
        output("*** Application started ***\n")
        wait.join(timeout)
        msg = ""
        status = ""
        if wait.is_alive():
            status = "killed"
            wait.terminate()
        else:
            status = "finished"
            msg = q.get()
        # yappi.stop()
        # stats = string.join([str(stat) for stat in yappi.get_stats(yappi.SORTTYPE_TTOTAL)],"\n")
        output("*** Application %s ***\n%s" % (status, msg))
        # output("*** Stats %s " % (stats))
        if verbose:
            output("\n*** Controller output: ***\n" + getControllerOutput() + "\n")
        nox.stop()
        os._exit(0)
    # elif nox_only:
    #     nox_command = os.path.expanduser(nox_path)
    #     nox_dir = os.path.dirname(nox_command)
    #     os.chdir(nox_dir)
    #     if verbose:
    #         nox_command += " -v"
 
    #     command = "%s -i ptcp:6633 %s" % (nox_command,"UpdateApp")
    #     os.system(command)        
    #     wait.join()
    #     os._exit(0)

    else:
        global mininet
        topo = get_function_by_name(topology_module, topology)(nodes).mininet_topo()
        mininet = Mininet( topo=topo, switch=UserSwitch,
                           controller=lambda name: NOX(name, "UpdateApp"),
                           xterms=False, autoSetMacs=True, autoStaticArp=True )
        mininet.start()
        lg.setLogLevel('output')
        output("*** Mininet Up ***\n")
        output("*** Application started ***\n")
        if cli:
            CLI(mininet)
        wait.join(timeout)
        msg = ""
        status = ""
        if wait.is_alive():
            status = "killed"
            listener.close()
            wait.terminate()
        else:
            status = "finished"
            msg = q.get()
        output("*** Application %s ***\n%s" % (status, msg))
        if verbose:
            output("*** Controller output: ***\n" + getControllerOutput() + "\n")
        mininet.stop()
        output("*** Mininet Down ***\n")
        os._exit(0)

def main():
    usage = "usage: %prog [options] MODULE [ARGS...]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-f", "--function", action="store", type="string",\
        dest="function", default=default_function,
        help="function to call, default is %s" %default_function)
    parser.add_option("-m", "--topology-module", action="store", type="string",\
                      dest="topology_module", default=None,
                      help="Topology module")
    parser.add_option("-t", "--topology", action="store", type="string",\
                      dest="topology", default=default_topology,
                      help="Initial topology constructor")
    parser.add_option("-c", "--command-line", action="store_true",\
                      dest="cli", help="Enable Mininet command-line interface")
    # parser.add_option("-n", "--nox-only", action="store_true",\
    #                   dest="nox_only", help="Only run NOX")
    parser.add_option("-n", "--nodes", action="store", type="int",\
                      default=default_nodes,
                      dest="nodes", help="Number of network nodes to pass to topo")
    parser.add_option("-e", "--experiment-mode", action="store_true",\
                      default=None,
                      dest="experiment_mode", help="Run in experiment mode, no mininet, no NOX calls")    
    parser.add_option("-p", "--path", action="store", type="string",\
        dest="nox_path", default=default_nox_path, help="Path to NOX binary")
    parser.add_option("-s", "--seconds", action="store", type="int",\
        dest="timeout", default=None, help="Amount of time to wait for controller application")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
        help="Run in verbose mode")
    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        exit(1)

    module = args[0]
    args = args[1:]
    topology_module = options.topology_module
    topology = options.topology
    function = options.function
    args = default_args if args == [] else args
    nodes = options.nodes
    cli = options.cli
    timeout = options.timeout
    nox_path = options.nox_path
    
    execute(module,
            topology_module=topology_module,
            topology=topology,
            function=function,
            args=args,
            nodes=nodes,
            cli=cli,
            timeout=timeout,
            nox_path=options.nox_path,
            verbose=options.verbose,
            experiment_mode=options.experiment_mode)

if __name__ == "__main__":
    # cProfile.run('main()', "/home/openflow/prof.out")
    main()
