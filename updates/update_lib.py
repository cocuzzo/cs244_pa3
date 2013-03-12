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
# /updates/update_lib.py                                                       #
# Update Library Functions                                                     #
################################################################################

from collections import defaultdict
import sys, os
from time import time
sys.path.append(os.environ['NOX_CORE_DIR'])
from nox.lib.core import UINT32_MAX, openflow
from policy import *
import logging
from decimal import Decimal
import networkx as nx
from update import UpdateObject

log = logging.getLogger("frenetic.update.update_lib")

#############
# CONSTANTS #
#############

# maximum priority of OpenFlow rules 
MAX_PRIORITY = 0xffff

####################
# GLOBAL VARIABLES #
####################

# inst
#   * reference to currently running NOX component
#   * also stores run-time structures used during updates
#       - current_version: policy version 
#       - current_priority: OpenFlow priority level 
#       - current_internal_policy: policy for versioned traffic
#       - current_edge_policy: policy for unversioned traffic  
#       - active_flows: dictionary of active flows, used for per-flow updates
#       - current_abstract_policy: unversioned policy equivalent to current
#       - future_abstract_policy: unversioned policy we're updating to
#       - concrete_policy: maps abstract rules to installed versioned rules
#       - installed_priority: FIXME
#       - stats: statistics 

inst = None
experiment = False

DEBUG = True

def setup(_inst, _experiment):
    """ 
    _inst: reference to current NOX component
    sets inst to _inst and initializes run-time structures 
    """
    global inst
    global experiment
    inst = _inst
    experiment = _experiment
    inst.current_version = 0
    inst.current_priority = MAX_PRIORITY 
    inst.current_internal_policy = NetworkPolicy()
    inst.current_edge_policy = NetworkPolicy()
    inst.active_flows = {}
    inst.current_abstract_policy = NetworkPolicy()
    inst.future_abstract_policy = NetworkPolicy()
    inst.stats = UpdateStats()
    inst.concrete_policy = defaultdict(lambda:defaultdict(lambda:[]))
    inst.installed_priority = \
      defaultdict(lambda:defaultdict(lambda:MAX_PRIORITY))
    return

##############
# STATISTICS #
##############

# UpdateStats
class UpdateStats:
    """
    Class whose objects represent statistics about the number of
    policy updates, rule adds, and rule deletes.
    """
    
    def __init__(self):
        self.updates = 0
        self.start_time = time()
        self.installs = defaultdict(lambda:0)
        self.modifies = defaultdict(lambda:0)
        self.deletes = defaultdict(lambda:0)
        self.current_rules = defaultdict(lambda:0)
        self.current_abstract_rules = defaultdict(lambda:0)
        self.future_abstract_rules = defaultdict(lambda:0)
        self.max_overhead = defaultdict(lambda:0)
    def tally_update(self, policy):
        self.updates += 1
        self.current_abstract_rules = self.future_abstract_rules
        self.future_abstract_rules = {}
        for switch, config in policy:
            self.future_abstract_rules[switch] = Decimal(len(config))
    def tally_install(self, switch):
        self.installs[switch] += 1
        self.current_rules[switch] += 1
    def tally_overhead(self, switch, config):
        """
        Calculates rule overhead, i.e. the maximum number of rules
        actually installed at a time versus the minimal rules
        required. So, if we had 2*N rules installed while
        transitioning between configs of size N, the overhead would be
        100%
        """
        if switch in self.current_abstract_rules:
            old_size = self.current_abstract_rules[switch]
        else:
            old_size = 0
        if switch in self.future_abstract_rules:
            new_size = self.future_abstract_rules[switch]
        else:
            new_size = 0
        base_size = max(old_size, new_size)
        extra_size = \
          Decimal(self.current_rules[switch] - base_size + len(config))
        overhead = extra_size/max(base_size, 1)
        self.max_overhead[switch] = max(self.max_overhead[switch], overhead)
        
    def tally_modify(self, switch):
        self.modifies[switch] += 1
    def tally_delete(self, switch):
        self.deletes[switch] += 1
        self.current_rules[switch] -= 1
    def all_installs(self):
        return sum(self.installs.values())
    def all_modifies(self):
        return sum(self.modifies.values())
    def all_deletes(self):
        return sum(self.deletes.values())
    def all_operations(self):
        return self.all_installs() + self.all_modifies()
    def all_overheads(self):
        return max(self.max_overhead.values())
    def __str__(self):
        s =  "   Update Statistics\n"
        s += "--------------------------------------------\n"
        s += "Switch\t(+)\t(-)\t(~)\tTotal\tOverhead\n"
        s += "--------------------------------------------\n"
        for switch in set(self.installs.keys() 
                          + self.deletes.keys() 
                          + self.modifies.keys()):
            i = self.installs[switch]
            d = self.deletes[switch]
            m = self.modifies[switch]
            o = self.max_overhead[switch]
            s += "s%d\t%d\t%d\t%d\t%d\t%d%%\n" % (switch, i, d, m, i+d+m, 100*o)
        s += "--------------------------------------------\n"
        s += "total\t%d\t%d\t%d\t%d\t%d%%\t%.4f\n" % \
             (self.all_installs(), 
              self.all_deletes(), 
              self.all_modifies(),
              self.all_operations(),
              100*self.all_overheads(),
              time() - self.start_time)
        return s

##########################################
# OPENFLOW-LEVEL INSTALL/DELETE COMMANDS #
##########################################

def install_rule(switch, pattern, actions, priority, idle_timeout):
    """ Wrapper for OpenFlow add request """

    inst.stats.tally_install(switch)
    if not experiment:
        inst.send_flow_command(switch, 
                               openflow.OFPFC_ADD,
                               pattern,
                               priority, 
                               (idle_timeout, actions, UINT32_MAX), 
                               openflow.OFP_FLOW_PERMANENT)
    return

def modify_rule(switch, pattern, actions, priority, 
                idle_timeout=openflow.OFP_FLOW_PERMANENT):
    """ 
    Wrapper for OpenFlow modify request 
    counters and timeouts are copied from current rule if they exist 
    """

    inst.stats.tally_modify(switch)
    if not experiment:    
        inst.send_flow_command(switch,
                               openflow.OFPFC_MODIFY, 
                               pattern, 
                               priority, 
                               (idle_timeout, actions, UINT32_MAX),
                               openflow.OFP_FLOW_PERMANENT)
    return

def delete_rules(switch, pattern, priority):
    """ Wrapper for OpenFlow delete request """

    inst.stats.tally_delete(switch)
    if not experiment:
        inst.send_flow_command(switch, openflow.OFPFC_DELETE_STRICT, pattern,
                               priority)
    return

########################################
# POLICY-LEVEL INSTALL/DELETE COMMANDS #
########################################

def install(policy, idle_timeout=openflow.OFP_FLOW_PERMANENT):
    """ Propagates a policy into the network """
    for switch, config in policy:
        if not switch in inst.concrete_policy:
            inst.concrete_policy[switch] = defaultdict(lambda:[])
            
        inst.stats.tally_overhead(switch, config)
        if DEBUG:
            log.debug("Installing  " + str(len(config)) + " rules on " 
                      + str(switch))
	# log.debug("Installing: " + str(config))	
        for rule in config:
            nox_pattern, nox_actions = rule.convert_to_nox_rule()
            install_rule(switch, nox_pattern, nox_actions, rule.priority,
                         idle_timeout)
            inst.installed_priority[switch][rule.pattern] = rule.priority
            inst.concrete_policy[switch][rule.parent].append(rule)
    return

def uninstall(policy):
    """ Removes a policy from the network """
    for switch, config in policy:
        if not switch in inst.concrete_policy:
            inst.concrete_policy[switch] = defaultdict(lambda:[])
        if DEBUG:
            log.debug("Uninstalling  " + str(len(config)) + " rules on " 
                      + str(switch))
	# log.debug("Uninstalling: " + str(config))
        for rule in config:
            priority = inst.installed_priority[switch][rule.pattern]
            delete_rules(switch, rule.pattern.to_dict(), priority)
            inst.concrete_policy[switch][rule.parent].remove(rule)
    return

def modify_policy(policy, idle_timeout=openflow.OFP_FLOW_PERMANENT):
    """ Propagates a policy into the network """
    for switch, config in policy:
        if not switch in inst.concrete_policy:
            inst.concrete_policy[switch] = defaultdict(lambda:[])

        if DEBUG:
            log.debug("Modifying  " + str(len(config)) + " rules on " 
                      + str(switch))
        for rule in config:
            nox_pattern, nox_actions = rule.convert_to_nox_rule()
            old_priority = inst.installed_priority[switch][rule.pattern]
            # modify_rule(switch, nox_pattern, nox_actions, rule.priority,
            #             idle_timeout)
            if old_priority != rule.priority:
                install_rule(switch, nox_pattern, nox_actions, rule.priority, 
                             idle_timeout)
                delete_rules(switch, nox_pattern, old_priority)
            if rule in inst.concrete_policy[switch][rule.parent]:
                inst.concrete_policy[switch][rule.parent].remove(rule)
            inst.concrete_policy[switch][rule.parent].append(rule)
            inst.installed_priority[switch][rule.pattern] = rule.priority
    return

##########################
# POLICY INSTRUMENTATION #
##########################

# JNF TODO: implement IN_PORT and FLOOD actions
def mk_versioned_actions(actions, version, tagged, edge_ports, old_version, 
                         fake_edge_ports):
    """
    Instruments a list of actions, modifying the vlan tag as needed
    for a versioned policy
    actions: list of actions to instrument
    version: policy version number
    tagged: if the traffic is already versioned or not
    edge_ports: set of outward-facing ports according to the topology
   """
    new_actions = []
    for action in actions:
        if action.tag == "forward":
            [port] = action.subexprs
            if port in edge_ports:
                if tagged:
                    if old_version is None:
                        new_actions.append(strip("vlan"))
            elif port in fake_edge_ports:
                new_actions.append(modify(("vlan", old_version)))
                tagged = "external"
            else:
                if tagged == "external":
                    new_actions.append(modify(("vlan", version)))
                    tagged = "internal"
                elif not tagged:
                    new_actions.append(modify(("vlan", version)))
                    tagged = "internal"
            new_actions.append(action)
        else:
            new_actions.append(action)
    return new_actions

def mk_internal_rule(rule, version, priority, edge_ports, 
                     old_version, fake_edge_ports):
    internal_pattern = Pattern(rule.pattern, DL_VLAN=version)
    # internal_pattern.DL_VLAN = version
    internal_actions = mk_versioned_actions(rule.actions, version,
                                            tagged="internal", 
                                            edge_ports=edge_ports,
                                            old_version=old_version,
                                            fake_edge_ports=fake_edge_ports)
    return Rule(internal_pattern, internal_actions, priority=priority,
                parent=rule, edge=False)

def mk_edge_rule(rule, version, priority, edge_ports, old_version, 
                 fake_edge_ports):
    edge_pattern = Pattern(rule.pattern, DL_VLAN=openflow.OFP_VLAN_NONE)
    edge_actions = mk_versioned_actions(rule.actions, version, False, 
                                        edge_ports, old_version, 
                                        fake_edge_ports)
    return Rule(edge_pattern, edge_actions, priority=priority, parent=rule,
                edge=True)

def mk_fake_edge_rule(rule, version, priority, edge_ports, old_version, 
                      fake_edge_ports):
    edge_pattern = Pattern(rule.pattern, DL_VLAN=old_version)
    edge_actions = mk_versioned_actions(rule.actions, version, False, 
                                        edge_ports, old_version, 
                                        fake_edge_ports)
    return Rule(edge_pattern, edge_actions, priority=priority, 
                parent=rule, edge=True)

def mk_versioned_configs(switch, config, version, priority, 
                         topology, old_version=None, 
                         fake_edge_ports=None, fake_edge_switches=None):
    internal_config = SwitchConfiguration()
    edge_config = SwitchConfiguration()
    if not fake_edge_switches:
        fake_edge_switches = []
    edge_switches = topology.edge_switches() + list(fake_edge_switches)
    edge_ports = topology.edge_ports(switch)
    if not fake_edge_ports:
        fake_edge_ports = []
    for rule in config:

        # if rule only applies to internal traffic  
        if (switch not in edge_switches 
            or (rule.pattern.IN_PORT != Pattern.WILD 
                and rule.pattern.IN_PORT not in edge_ports 
                and rule.pattern.IN_PORT not in fake_edge_ports)):
            internal_rule = mk_internal_rule(rule, version, priority, 
                                             edge_ports, old_version,
                                             fake_edge_ports)
            internal_config.add_rule(internal_rule)
        # otherwise, if rule may apply to both internal and edge traffic
        else:
            # if rule only applies to edge traffic
            if rule.pattern.IN_PORT in edge_ports:
                edge_rule = mk_edge_rule(rule, version, priority, 
                                         edge_ports, old_version, 
                                         fake_edge_ports)
                edge_config.add_rule(edge_rule)
            elif rule.pattern.IN_PORT in fake_edge_ports:
                edge_rule = mk_fake_edge_rule(rule, version, priority, 
                                              edge_ports, old_version,
                                              fake_edge_ports)
                edge_config.add_rule(edge_rule)
            else:
                edge_rule = mk_edge_rule(rule, version, priority,
                                         edge_ports, old_version,
                                         fake_edge_ports)     
                fake_edge_rule = mk_fake_edge_rule(rule, version, priority,
                                                   edge_ports, old_version,
                                                   fake_edge_ports)
                # add both internal and edge rules to respective configs
                internal_rule = mk_internal_rule(rule, version, priority,
                                                 edge_ports, old_version,
                                                 fake_edge_ports)
                internal_config.add_rule(internal_rule)
                edge_config.add_rule(edge_rule)
                edge_config.add_rule(fake_edge_rule)
    return (internal_config, edge_config)
        
def mk_versioned_policies(policy, version, priority, topology, 
                          old_version=None,
                          fake_edge_ports=None):
    """ Constructs internal and edge policies from policy and version """
    # initialize fresh policy objects
    internal_policy = NetworkPolicy()
    edge_policy = NetworkPolicy()
    # for each switch mentioned in the policy
    for switch, config in policy:
        # FIXME: Am I supposed to pass through the fake_edge_ports
        # arg? How does this work again?
        internal_config, edge_config = \
          mk_versioned_configs(switch, config, version, priority, topology,
                               old_version=old_version, fake_edge_ports=None)
        internal_policy[switch] = internal_config
        edge_policy[switch] = edge_config
    return (internal_policy, edge_policy)

#####################
# UPDATE INTERFACES #
#####################

def per_packet_update(topology, new_policy, use_extension=True, 
                      use_subspace=True, use_island=False):
    """
    Updates to new policy using versioning + two-phase commit and
    optimizations when safe topology: nxtopo.NXTopo object
    representing topology new_policy: policy.NetworkPolicy object
    count: boolean signaling to count initial empty install
    use_extension: boolean denoting signaling to use extension
    optimization use_partial: boolean denoting signaling to use
    partial update optimization
    """
    # if current policy empty
    if (inst.current_internal_policy.is_empty() 
        and inst.current_edge_policy.is_empty 
        and inst.current_abstract_policy.is_empty()):
        # use empty_update
        update = empty_update(topology, new_policy)
    else:
        minus_delta = inst.current_abstract_policy - new_policy        
        plus_delta = new_policy - inst.current_abstract_policy        
        # If retraction
        if use_extension and new_policy <= inst.current_abstract_policy and \
          is_not_reachable(minus_delta, inst.current_abstract_policy - minus_delta,
                           topology):
            update = retraction_update(topology, new_policy, minus_delta)
        # else if extension
        elif use_extension and inst.current_abstract_policy <= new_policy and \
          is_not_reachable(plus_delta, inst.current_abstract_policy, topology):
            update = extension_update(topology, new_policy, plus_delta)
    
        # otherwise
        elif use_subspace:
            update = subspace_update(topology, new_policy)
            # partial_per_packet_update(topology, new_policy, 
            #                           inst.current_abstract_policy)
        elif use_island:
            update = island_update(topology, new_policy)
        else:
            update = full_per_packet_update(topology, new_policy)
    
    two_phase_update(topology, update)
    inst.current_abstract_policy = new_policy
    return

def per_flow_update(topology, new_policy, flow_window, refine, refine_window,
                    use_extension=True, use_subspace=True, use_island=False):
    """
    Updates to new policy using versioning + two-phase commit
    topology: nxtopo.NXTopo object representing topology
    new_policy: policy.NetworkPolicy object 
    flow_window: time window between flows
    refine: function from a pattern to a list of patterns
      - must denotes the same fragment of flowspace!
    refine_window: timer for invoking refine_flows
    """
    # if current policy empty
    if (inst.current_internal_policy.is_empty() 
        and inst.current_edge_policy.is_empty()):
        # use empty_update
        update = empty_update(topology, new_policy)
        
    # otherwise        
    else:
        return

def two_phase_update_flows(topology, update):
        
    # if necessary, garbage collect priorities
    if inst.current_priority == 0:
        priority_garbage_collect()

    # retrieve current data from stats
    current_internal_policy = inst.current_internal_policy
    current_edge_policy = inst.current_edge_policy
    current_version = inst.current_version
    current_priority = inst.current_priority

    # calculate new versions
    new_version = current_version + 1

    # calculate new priorities:
    #   - flow_priority for active flows from old policy
    #   - new priority (lower) for new policy
    flow_priority = current_priority - 1
    new_priority = current_priority - 2

    # create versioned policies for internal and edge traffic
    internal_policy, edge_policy = \
      mk_versioned_policies(new_policy, new_version, new_priority, 
                            topology)

    # calculate flows for current edge policy
    active_flows = current_edge_policy.flows()

    # (1) install internal policy
    install(internal_policy)

    # (2) reinstall current policy at flow_priority, using
    # flow_window as idle_timeout
    # TODO: Now that we use rule priorities, make sure each rule
    # is at flow_priority
    install(current_internal_policy, idle_timeout=flow_window)
    install(current_edge_policy, idle_timeout=flow_window)

    # (3) install edge policy
    install(edge_policy)

    # (4) remove old edge policy 
    # TODO: Removed old priority argument (=
    # current_priority). Verify this is not needed
    uninstall(current_edge_policy)

    # (5) remove old internal policy
    uninstall(current_internal_policy)

    # update inst with old data
    inst.active_flows = active_flows
    inst.current_internal_policy = internal_policy
    inst.current_edge_policy = edge_policy
    inst.current_version = new_version
    inst.current_priority = new_priority
    inst.post_callback(refine_window, 
                       lambda:refine_flows(flow_window, refine, 
                                           refine_window, flow_priority))
    
def priority_garbage_collect():
    """ Resets priority to maximum value """
    # retrieve current data from inst
    current_internal_policy = inst.current_internal_policy
    current_edge_policy = inst.current_edge_policy
    active_flows = inst.active_flows

    # reset priority
    new_priority = MAX_PRIORITY

    # if active_flows exist
    if active_flows:
        flow_priority = MAX_PRIORITY
        new_priority = flow_priority - 1

        # modify them to be at flow priority
        for switch, flows in active_flows:
            for (pattern, actions) in flows:
                modify_rule(switch, pattern, actions, flow_priority)

    # reinstall current policy at new priority
    modify_policy(current_internal_policy, new_priority)
    modify_policy(current_edge_policy, new_priority)

    # # uninstall old policies
    # uninstall(current_internal_policy)
    # uninstall(current_edge_policy)

    # update inst with new data
    inst.current_internal_policy.set_priority(new_priority)
    inst.current_edge_policy.set_priority(new_priority)
    inst.current_priority = new_priority
    return

########################
# UPDATE OPTIMIZATIONS #
########################

# TODO: Restore 'count' argument? Still needed?
def empty_update(topology, new_policy):
    """
    precondition: current policy has no rules
    provides per-packet and per-flow (vacuously)  
    """
    assert not (inst.current_internal_policy or 
                inst.current_edge_policy or
                inst.current_abstract_policy)
    log.debug("Empty update")
    # update stats
    inst.stats.tally_update(new_policy)
    if DEBUG:
        log.debug("New policy: \n" + str(new_policy))
        
    # retrieve current version from inst
    current_version = inst.current_version

    # reset priority to maximum value and bump version number
    new_priority = MAX_PRIORITY
    new_version = current_version + 1

    # create versioned policies for internal and edge traffic
    internal_policy, edge_policy = \
      mk_versioned_policies(new_policy, new_version, new_priority, topology)

    return UpdateObject(internal_policy, edge_policy, None, None, 
                        new_priority, new_version)
    
def extension_update(topology, new_policy, plus_delta):
    """
    precondition: plus_delta is unreachable from current policy
    provides per-packet    
    """
    plus_internal_delta, plus_edge_delta = \
      mk_versioned_policies(plus_delta, inst.current_version, 
                            inst.current_priority, topology)
    
    # update stats
    inst.stats.tally_update(new_policy)
    log.debug("Extension update!")

    current_version = inst.current_version
    current_priority = inst.current_priority

    return UpdateObject(plus_internal_delta, plus_edge_delta,
                        NetworkPolicy(), NetworkPolicy(),
                        current_priority, current_version)

def retraction_update(topology, new_policy, minus_delta):
    """
    precondition: minus_delta is unreachable from current policy - minus_delta
    provides per-packet    
    """
    minus_internal_delta, minus_edge_delta = concrete_rules(minus_delta)
    
    # update stats
    inst.stats.tally_update(new_policy)
    log.debug("Retraction update!")

    current_version = inst.current_version
    current_priority = inst.current_priority

    return UpdateObject(NetworkPolicy(), NetworkPolicy(),
                        minus_internal_delta, minus_edge_delta,
                        current_priority, current_version)
     

# FIXME: I suspect this is broken since we ignore the induced subgraph
# and induced subpolicy
def island_update(topology, new_policy):
    """
    precondition: Assumes that only one island update is performed,
    and no subspace updates have been performed. This assumption is
    forced by our use of VLAN tags instead of MPLS labels
    provides per-packet
    """
    inst.stats.tally_update(new_policy)
    log.info("Island update")

    old_policy = inst.current_abstract_policy

    # Switches which didn't change in new policy
    nops = set( s1 for s1, c1 in old_policy \
                if switch_covered(c1, new_policy[s1]))
    # Everything else
    new =  set(topology.switches()) - nops
    old = set()

    fixpoint = island_fixpoint(topology, new_policy)
    while new:
        additions = fixpoint(new, old)
        old |= new
        new = additions
        
    mods = old

    subpolicy = restrict_policy(mods, new_policy)

    boundary = nx.edge_boundary(topology, mods)
    fake_edge_ports = \
      [topology.node[x]['ports'][y] for (x,y) in boundary \
       if topology.node[y]['isSwitch']]

    # retrieve current data from inst        
    current_internal_policy = inst.current_internal_policy
    current_edge_policy = inst.current_edge_policy
    current_version = inst.current_version
    current_priority = inst.current_priority

    # calculate new version and priority
    new_version = current_version + 1
    new_priority = current_priority - 1

    # Have to manually construct the correct edge policies by
    # distinguishing between "true" edge ports to hosts and "fake"
    # edge ports to other switches running the old version.
    internal_policy, edge_policy = \
      mk_versioned_policies(subpolicy, new_version, new_priority, topology,
                            old_version=current_version, 
                            fake_edge_ports=fake_edge_ports)

    old_internal_policy = restrict_policy(mods, current_internal_policy)
    old_edge_policy = restrict_policy(mods, current_edge_policy)
    
    return UpdateObject(internal_policy, edge_policy,
                        old_internal_policy,
                        old_edge_policy,
                        new_priority, new_version)
    
def subspace_update(topology, new_policy):
    """ 
    precondition: none
    provides per-packet
    """
    log.info("Fixpoint subspace update")
    inst.stats.tally_update(new_policy)
    if DEBUG:
        log.debug("Installing new policy: " + str(new_policy))

    old_policy = inst.current_abstract_policy

    # Correctness argument:
    # * dels[s] = { r in c[s] | not covered(r) }
    # * nops[s] = { r in c[s] | covered(r) } (* = c[s] \ dels[s] *)
    # * mods[s] = { r' in c'[s] | not exist a rule r in nops[s]. 
    #                                    r ~ r' and actions(r) = actions(r') }

    # Note that we can derive dels and nops from mods:
    # nops'[s] = { r in c[s] | forall r' in c'[s] - mods'[s].
    #                             if r' ~ r then actions(r) = actions(r')
    # dels' = c \ nops'
    # Lemma: if mods' = mods, then nops' = nops and dels' = dels
    
    # Next, close mods under forwards and backwards reachability
    # By construction, every rule in nops covers some rule in new
    dels = NetworkPolicy()
    for s1, c1 in old_policy:
        dels[s1] = SwitchConfiguration([r for r in c1 \
                                        if not covered(r, new_policy[s1])])

    nops = NetworkPolicy()

    for s1, c1 in old_policy:
        nops[s1] = c1 - dels[s1]

    mods = NetworkPolicy()
    for s1, c1 in new_policy:
        mods[s1] = SwitchConfiguration([r1 for r1 in c1 \
                                        if not covered(r1, nops[s1])])

    fixpoint = subspace_fixpoint(topology)

    remainder = new_policy - mods
    edge = mods
    while True:

        log.debug("Entering fixpoint")
        remainder, edge = fixpoint(remainder, edge)
        log.debug("Finished fixpoint")

        if (not edge):
            break

    # Need to compute mapping from new rules to old rules that cover
    
    mods = new_policy - remainder

    new_version = inst.current_version + 1
    new_priority = inst.current_priority - 1
    plus_internal_delta, plus_edge_delta = \
      mk_versioned_policies(mods, new_version, new_priority, topology)
    minus_internal_delta, minus_edge_delta = concrete_rules(dels)

    return UpdateObject(plus_internal_delta, plus_edge_delta,
                        minus_internal_delta, minus_edge_delta,
                        new_priority, new_version)

def full_per_packet_update(topology, new_policy, old_version=None):
    """
    * precondition: none
    * provides per-packet
    """

    # update stats
    log.debug("Full update!")
    if DEBUG:
        log.debug("New policy:" + str(new_policy))
    inst.stats.tally_update(new_policy)

    # calculate new version and priority
    new_version = inst.current_version + 1
    new_priority = inst.current_priority - 1

    # create versioned policies for internal and edge traffic
    internal_policy, edge_policy = \
      mk_versioned_policies(new_policy, new_version, new_priority, topology,
                            old_version=old_version)
          
    return UpdateObject(internal_policy, edge_policy, 
                        inst.current_internal_policy, 
                        inst.current_edge_policy,
                        new_priority, new_version)

#############################
# OPTIMIZATIONS SUBROUTINES #
#############################

def connects(r1, s1, r2, s2, topology):
    """
    We say that a rule r1 on switch s1 "connects" to a rule r2 on a switch s2
    under a configuration c if:
    * r1's actions forward packets to output port p1
    * the topology connects output port p1 on s1 to input port p2 on s2
    * the in_port constraint in r2's pattern is either p2 or wildcard
    * updating r1's pattern with modifications mentioned in r1's actions
      yields a pattern whose intersection with r2's pattern is non-empty
    """
    for pkt, out_port in r1.apply(r1.pattern):
        new_switch, in_port = topology.node[s1]['port'][out_port]
        if new_switch == s2:
            if r2.pattern.intersects(pkt):
                return True
    return False

# Need to know how many ports this switch has to see if the in_port
# wildcard is covered
def covered(r, config):
    """
    Given a rule r in c[s], we say that r is covered, written covered(r)
    if the following condition holds:
        there exists a subset rs' of c'[s]. 
        (for every rule r' in rs'. actions(r) = actions(r')) and
            pattern(rs') == pattern(r) 
    """
    # FIXME: We cheat for optimization here. I know that I never split rules, so a rule is covered exactly when there is a new rule with the exact same pattern and action
    return config.contains_matching_rule(r)
    # return set_covers(covers(r, config), r)

def set_covers(rs, r):
    ps = []
    for r1 in rs:
        if not list_eq(r1.actions, r.actions):
            return False
        else:
            ps.append(r1.pattern)
    return set_covers_pattern(ps, r.pattern)

def set_covers_pattern(ps, p):
    """
    Approximates set covering. If p has a wildcard, then one of the
    patterns must have a wildcard
    """
    for header, value in p:
        match = False
        if value == Pattern.WILD:
            for p1 in ps:
                if p1[header] == Pattern.WILD:
                    match = True
                    break
        else:
            for p1 in ps:
                if p1[header] == value:
                    match = True
                elif p1[header] != value:
                    match = False
                    break
        if not match:
            return False
    return True

def covers(r, config):
    """
    Given a rule r in c[s], we say r' is in covers(r) if: r' is in
    c'[s] and actions(r) = actions(r') and pattern(r') ~ pattern(r)
    """
    assert(isinstance(r, Rule))
    covering = set()
    for rule in config:
        if rule.pattern <= r.pattern:
            if not list_eq(rule.actions, r.actions):
                return set()
            covering.add(rule)    
    return covering

def list_of_covers(rs, config):
    return set(rule for r in rs for rule in covers(r, config))

class flow_space(object):

    def __init__(self, flows=None):
        if isinstance(flows, list):
            self.__pkts__ = defaultdict(set)            
            for sw, p, pkt, rule in flows:
                if pkt.in_port != p:
                    new_pkt = Pattern(pkt, in_port=p)
                else:
                    new_pkt = pkt
                self.__pkts__[sw].add((new_pkt, rule))
        elif isinstance(flows, dict):
            self.__pkts__ = flows.copy()
        else:
            self.__pkts__ = defaultdict(set)

    def add(self, sw, pkt, rule):
        self.__pkts__[sw].add((pkt, rule))
        
    def __getitem__(self, switch):
        return self.__pkts__[switch]

    def __setitem__(self, switch, value):
        self.__pkts__[switch] = value

    def __iter__(self):
        return self.__pkts__.iterkeys()

    def __and__(self, other):
        """ Right biased intersection: takes rules from other """
        intersection = flow_space()
        for switch in self:
            for pkt, _ in self[switch]:
                for pkt2, rule2 in other[switch]:
                    if pkt.intersects(pkt2):
                        if pkt <= pkt2:
                            intersection.add(switch, pkt, rule2)
                        else:
                            intersection.add(switch, pkt2, rule2)
        return intersection

    def __or__(self, other):
        union = flow_space()
        for switch in self:
            union[switch] = self[switch] | other[switch]
        return union
        

    def apply_topology(self, topology):
        """
        Transfers each located packets lp = (port, pkt) in outgoing to
        port' such that (port, port') is in graph
        """

        for switch in self:
            outgoing = self[switch]
            output = flow_space([])
            for pkt, rule in outgoing:
                port = pkt.IN_PORT
                (target_switch, target_port) = topology.node[switch]['port'][port]
                if not (target_switch in topology.node
                    and topology.node[target_switch]['isSwitch']):
                    continue
                pkt = Pattern(pkt, IN_PORT=target_port)
                output.add(target_switch, pkt, rule)

        return output

    def rules(self):
        """
        Returns a policy representing the rules contributing to the flow space
        """
        policy = NetworkPolicy()
        for switch in self:
            config = SwitchConfiguration()
            for _, rule in self[switch]:
                config.add_rule(rule)
            policy[switch] = config
        return policy

def rng(policy, topology):
    _range = flow_space()
    for switch in policy:
        for rule in policy[switch]:
            for port, pkt in rule.apply(rule.pattern):
                (target_switch, target_port) = topology.node[switch]['port'][port]
                pkt = Pattern(pkt, IN_PORT=target_port)
                _range.add(target_switch, pkt, rule)
    return _range

def dom(policy):
    _dom = flow_space()
    for switch in policy:
        for rule in policy[switch]:
            _dom.add(switch, rule.pattern, rule)
    return _dom

def subspace_fixpoint(topology):

    def fixpoint(rest, edge):
        edge_domain = dom(edge)
        edge_range = rng(edge, topology)
        rest_domain = dom(rest)
        rest_range = rng(rest, topology)

        new_edge = ((edge_domain & rest_range) | (edge_range & rest_domain)).rules()

        return (rest - new_edge, new_edge)

    return fixpoint
        
def switch_covered(old_config, new_config):
    """
    Given a switch s, we say that s is covered, written covered(s)
    if the following condition holds:
        for every r' in c'[s], r' is in covers(r) for some r in c[s]
        for every r in c[s], covered(r)
    """
    covering = []
    for r1 in old_config:
        if not covered(r1, new_config):
            return False
        cover = covers(r1, new_config)
        covering += cover
    for r2 in new_config:
        if not r2 in covering:
            return False
    return True    


# TODO: Figure out how to make edge_ports and edge_switches work
# Idea: The set-at-a-time algorithm for subset update was super fast, but it's not clear how to do the same for island, 
def island_fixpoint(topology, new_policy):

    def fixpoint(new, old):
        mods_set = new | old
        addition = set()
        for a in (new | old):
            mods_set.remove(a)
            for b in (new | old):
                if (a in old and b in old):
                    continue
                if a != b:                
                    mods_set.remove(b)
                for rule in new_policy[a]:
                    p = rule.pattern
                    path = find_path(topology, new_policy, mods_set, p, a, b)
                    if path:
                        mods_set |= path
                        addition |= path
                mods_set.add(b)
            mods_set.add(a)
        return addition

    return fixpoint

def restrict_policy(switches, policy):
    new_policy = NetworkPolicy()
    for s in switches:
        new_policy[s] = policy[s]
    return new_policy


def rules_intersect(r1, r2):
    return r1.pattern.intersects(r2.pattern)

def sorted_list_diff(l1, l2):
    """ Computes l1 - l2. Assumes l1 and l2 are sorted """
    # TODO: This would be much simpler as a loop or fold
    diff = []
    l1_iter = iter(l1)
    l2_iter = iter(l2)
    l1_done = False
    l2_done = False

    # Get the first item from each list
    try:
        item1 = l1_iter.next()
    except StopIteration:
        l1_done = True
    try:
        item2 = l2_iter.next()
    except StopIteration:
        l2_done = True

    
    while not (l1_done or l2_done):
        if item1 < item2:
            diff.append(item1)
            try:
                item1 = l1_iter.next()
            except StopIteration:
                l1_done = True
                break
        elif item1 == item2:
            try:
                item1 = l1_iter.next()
            except StopIteration:
                l1_done = True
                break
        else:
            try:
                item2 = l2_iter.next()
            except StopIteration:
                l2_done = True
                break
    # post condition: l1_done \/ l2_done
            
    if l1_done:
        return diff
    else:
        while not l1_done:
            try:
                diff.append(l1_iter.next())
            except StopIteration:
                l1_done = True
    return diff


def two_phase_update(topology, update):
    # if necessary, garbage collect priorities
    if inst.current_priority == 0:
        priority_garbage_collect()


    plus_edge_policy = update.plus_edge_policy
    minus_edge_policy = update.minus_edge_policy
    plus_internal_policy = update.plus_internal_policy
    minus_internal_policy = update.minus_internal_policy
    new_priority = update.new_priority
    new_version = update.new_version
    
    modify_edge_policy = \
      plus_edge_policy.pattern_intersect(inst.current_edge_policy)
    install_edge_policy = \
      plus_edge_policy.pattern_diff(inst.current_edge_policy)
    uninstall_edge_policy = minus_edge_policy.pattern_diff(modify_edge_policy)
        
    # (1) install internal policy
    if DEBUG:
        log.debug("Installing new internal policy: \n" + str(plus_internal_policy))
    install(plus_internal_policy)

    # TODO: Wait for rules to be installed
    # (2) install edge policy
    if DEBUG:
        log.debug("Installing new edge policy: \n" + str(install_edge_policy))
    install(install_edge_policy)
    if DEBUG:
        log.debug("Modifying old edge policy: \n" + str(modify_edge_policy))
    modify_policy(modify_edge_policy)

    # (3) remove old edge policy
    if DEBUG:
        log.debug("Uninstalling old edge policy: \n" + str(uninstall_edge_policy))
    uninstall(uninstall_edge_policy)
        
    # TODO: Wait for packets to leave
    # (4) remove old internal policy
    if DEBUG:
        log.debug("Uninstalling old internal policy: \n" \
                  + str(minus_internal_policy))
    uninstall(minus_internal_policy)

    # update inst with new data
    inst.current_internal_policy = \
      (inst.current_internal_policy + plus_internal_policy).pattern_diff(minus_internal_policy)
    inst.current_edge_policy = \
      (inst.current_edge_policy + install_edge_policy + modify_edge_policy).pattern_diff(uninstall_edge_policy)
    inst.current_version = new_version
    inst.current_priority = new_priority
    inst.currrent_topo = topology
    return    
    


def end_flow(switch, flow):
    """
    * called by NOX when a flow is removed from a switch 
    * deletes flow if it is in inst.active_flows
    * note that not all flows are tracked in inst.active_flows
    """

    active_flows = inst.active_flows
    if (active_flows.has_key(switch) and flow in active_flows[switch]):
        active_flows[switch].remove(flow)    
        if active_flows[switch] == []:
            del active_flows[switch]
    return

def refine_flows(flow_window, refine, refine_window, priority):
    """
    * refines active flows into smaller flows 
    * invoked on a timer from per_flow_update 
    * flow_window: time window between flows 
    * refine: function from a pattern to a list of patterns
      - must denotes the same fragment of flowspace!
    * refine_window: timer for invoking refine_flows
    * priority: priority  flows currently installed at 
    """

    new_active_flows = {}
    for switch, flows in inst.active_flows:
        new_flows = []
        for (pattern, actions) in flows:
            for new_pattern in refine(pattern):
                new_flows.append(new_pattern, actions)
                install_rule(switch, new_pattern, actions, priority, 
                             flow_window)
            delete_rules(switch, pattern.to_dict(), priority)
        if new_flows:
            new_active_flows[switch] = new_flows    
    inst.active_flows = new_active_flows
    if new_active_flows:
        inst.post_callback(refine_window, 
                           lambda:refine_flows(flow_window, refine, 
                                               refine_window, priority))
    return


def config_domain(config):
    """
    The domain of a configuration is the flow-space that matches a rule
    in the configuration. For efficiency, should change this to be
    sorted
    """
    return set( rule.pattern for rule in config )
    # return reduce_flow_space(domain)
    
def config_range(config):
    return [ pat for rule in config for pat in rule.apply(rule.pattern) ]
        
def concrete_rules(policy):
    concrete_edge_policy = NetworkPolicy()
    concrete_internal_policy = NetworkPolicy()    
    for switch, config in policy:
        concrete_edge_policy[switch] = SwitchConfiguration()
        concrete_internal_policy[switch] = SwitchConfiguration()
        for rule in config:
            for conc_rule in inst.concrete_policy[switch][rule]:
                if conc_rule.edge:
                    concrete_edge_policy[switch].add_rule(conc_rule)
                else:
                    concrete_internal_policy[switch].add_rule(conc_rule)
    return concrete_internal_policy, concrete_edge_policy

    
def is_not_reachable(delta, old, graph):
    """
    Checks that no traffic from the old configuration can reach new rules
    """
    old_domain = defaultdict(set)
    old_range = defaultdict(set)
    new_domain = defaultdict(set)
    new_range = defaultdict(set)
    # Check non-intersecting domains
    for switch, config in old:
        if not switch in delta:
            # new_domain[switch] = []
            # new_range[switch] = []            
            continue
        else:
            old_domain[switch] = config_domain(config)
            old_range[switch] = config_range(config)            
            new_domain[switch] = config_domain(delta[switch])
            new_range[switch] = config_range(delta[switch])          

    # Check non-reachability
    for switch, rng in old_range.iteritems():
        one_hop = apply_topology(switch, rng, graph)
        for new_switch in one_hop:
            if flows_intersecting(new_domain[new_switch], one_hop[new_switch]):
                return False
    return True

def find_path(graph, policy, forbidden, patt, src, dst):
    assert isinstance(patt, Pattern)
    # Does a DFS search
    stack = [(set(), src, patt)]
    while stack:
        path, sw, pkt  = stack.pop()
        conf = policy[sw]
        rule = conf[pkt]
        outgoing = rule.apply(pkt)
        try:
            incoming = apply_topology(sw, outgoing, graph)
        except KeyError:
            continue
        for sw, pkts in incoming.iteritems():
            if sw == dst:
                return path
            if sw in forbidden:
                continue
            for pkt in pkts:
                new_path = path.copy()
                new_path.add(sw)
                stack.append((new_path, sw, pkt))
    return None
            
            
    
def apply_topology(switch, outgoing, graph):
    """
    Transfers each located packets lp = (port, pkt) in outgoing to
    port' such that (port, port') is in graph
    """
    output = defaultdict(set)
    for pkt, port in outgoing:
        (target_switch, target_port) = graph.node[switch]['port'][port]
        if not (target_switch in graph.node
                and graph.node[target_switch]['isSwitch']):
            continue
        pkt = Pattern(pkt, IN_PORT=target_port)
        output[target_switch].add(pkt)

    return output
            
def flows_intersecting(flows1, flows2):
    """ 
    Tests whether any of the patterns in flow1 and flow2 have packets
    in common
    """
    # TODO: Make args ordered
    # TODO: Right now this assumes that patterns have the same "granularity" as in our examples. Need to uncomment to return to general case. 
    # for flow1 in flows1:
    #     for flow2 in flows2:
    #         if flow1 <= flow2 or flow2 <= flow1:
    #             return True
    # return False
    return bool(flows1 & flows2)
