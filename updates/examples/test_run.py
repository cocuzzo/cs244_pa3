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
# /updates/test_run.py                                                         #
# Test harness front-end                                                       #
# $Id$ #
################################################################################

# This script is a wrapper around running Nox and Frenetic.  It takes
# the desired module as an argument, stores it in an environment
# variable, and then starts Frenetic under Nox, which then can
# retrieve the environment variable

# TODO(astory): consider putting nox's directories into sys.path
import optparse
import os
import sys

# Note that boolean benavior when running frenetic_run directly is largely
# determined by store_false and store_true in the parser configuration in the
# main() function
default_function = "main" 
default_independent = False
default_nox_path = "/home/ubuntu/nox-classic/build/src/nox_core"
default_verbose = False 
default_justnox = False
default_topo = "test_topo"

def fetch_subdirs(directory = os.getcwd()):
    """Returns a list including this directory and all of its subdirectories"""
    return [dirpath for (dirpath, dirnames, filenames) in os.walk(directory)]

def setup_env(application, params = [], function = "main", dirs = None):
    """set up environment variables for Frenetic_app to pull from
    application: the name of the module to import, minimally qualified
        (frenetic_examples, NOT nox.coreapps.examples.frenetic_examples)
    params: a list of parameters to pass to the function.  Will be packed into a
        single whitespace-separated list.
    function: name of the function inside the module to call
    dirs: list of directories to include in the python path.  This is important
        when using frenetic because nox does weird things to python's
        expectations of where files will be.
    """
    os.environ["FRENETIC_APPLICATION"] = application
    os.environ["FRENETIC_PARAMETERS"] = ",".join(params)
    os.environ["FRENETIC_FUNCTION"] = function
    os.environ["FRENETIC_LIBS"] = " ".join(dirs)

def import_directories(dirs):
    """Prepends all the directories in dirs onto sys.path, causing python to
    look there first for modules"""
    sys.path = reduce((lambda paths, path: paths + [path]), sys.path, dirs)

def get_function_by_name(module, function):
    """Imports module, and returns module.function"""
    # Import the module in question and hold on to it
    application = __import__(module, globals(), locals(), [], -1)
    # get the function we want out
    return getattr(application, function)

def execute(module,
        args=[],
        function=default_function,
        independent=default_independent,
        nox_path=default_nox_path,
        verbose=default_verbose,justnox=default_justnox,topo=default_topo):

    if not(justnox):
        dirs = fetch_subdirs()

        # TODO(astory): once we have a standard interface for passing args
        #   to the called function, this should probably only be done if
        #   we're calling nox.
        setup_env(module, args, function, dirs)

    if independent:
        import_directories(dirs)
        application = get_function_by_name(module, function)
        application()
    else:
        # Nox only works if run in the directory in which the nox
        # binary lives Note that this only affects spawned processes,
        # and does not affect the user's shell.
        nox_command = os.path.expanduser(nox_path)
        nox_dir = os.path.dirname(nox_command)
        os.chdir(nox_dir)
        if (verbose):
            nox_command += " -v"

        if (justnox):
            if args != []:
                a = reduce(lambda r,s:r+','+ s, args[1:], args[0])
                app = module+'='+a
            else:
                app = module
        else:
            app = "FreneticApp"

        command = "%s -i ptcp:6633 %s" % (nox_command,app)
        os.system(command)

def main():
    usage = "usage: %prog [options] MODULE [ARGS...]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-f", "--function", action="store", type="string",\
        dest="function", default=default_function,
        help="function to call, default is %s"%default_function)
    parser.add_option("-i", "--independent", action="store_true",\
        dest="independent", help="run module without nox")
    parser.add_option("-n", "--nox", action="store_false", dest="independent",\
        help="run module with nox")
    parser.add_option("-p", "--path", action="store", type="string",\
        dest="nox_path", default=default_nox_path,\
        help=
        "Full path of NOX binary. Default is %s.\nIgnored if not using NOX."
        % default_nox_path)
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
        help="Run NOX is verbose mode")
    parser.add_option("-N", "--nox-app", action="store_true", dest="justnox",
        help="Run NOX in verbose mode")
    parser.add_option("-t", "--topology", action="store_true", dest="topo",
        help="specify topology")    
    (options, args) = parser.parse_args()
    function = options.function
    independent = options.independent
    
    if len(args) < 1:
        parser.print_help()
        parser.error("Please specify a module to run.")    


    # This is the same as os.putenv(...) but the documentation
    # recommends this method because putenv does not update the
    # os.environ hash, while assignments into os.environ also call
    # putenv automatically.
    module = args[0]
    args = args[1:]

    execute(module,
            args=args,
            function=function,
            independent=independent,
            nox_path=options.nox_path,
            verbose=options.verbose,justnox=options.justnox,topo=options.topo)


if __name__ == "__main__":
    main()
