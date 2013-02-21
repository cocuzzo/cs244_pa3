# -----------------------------------------------------------------------------
# This file contains utility functions for encoding a network topology and
# forwarding policy as a Kripke structure in the NuSMV model checker.
#

# Policy
# The network policy (forwarding and modification rules for switches) is
# defined in frenetic-code/updates/policy.py.
from policy import *

# NXTopo
# nxtopo.py defines a custom NetworkX topology.
import nxtopo as nxt

# Ordered dictionaries preserve priorities on forwarding policies.
from util import OrderedDict

# Special switch labels in the NuSMV model.
special_switches = ['WORLD', 'CONTROLLER', 'DROP']

# Cast integer constants n to NuSMV bit field constants 0ud<field_width>_n.
def int_to_nusmvbitfield(field, val):
    return '0ud%s_%s' % (PATTERN_LENGTHS[field], pattern_to_int(field,val))

# Return an (action, [vals]) pair, where action is a string and [vals] is a
# list of values operated on by the action, as specified in the definition of
# the class Action.
def unpack_action(action): 
    return (action.tag, action.subexprs)

# Generate transition relations
# See encode() for more details.
# Return (switch_transitions, header_transitions), where
# switch_transitions is an OrderedDict : {condition : next switch} and
# header_transitions is a dict : {field : OrderedDict({condition : next val})}.
def generate_transitions(topology, policy):
    # switch_transition: dictionary of "boolean formula" : "transition".
    # This will become the case statement in the NuSMV file for the
    # switch transition.
    switch_transition = OrderedDict()

    # header_transitions: 
    # dictionary of "header" : {"boolean formula" : "transition"}
    # This will define the transition relation on the headers in the NuSMV
    # file.  Headers with no transitions will become FROZENVARS.
    header_transitions = {}

    # For each switch configuration: 
    # 1. add the fowarding rules to the switch_transition dictionary as
    #    "string representation of boolean condition" : "new switch".
    # 2. add the modification rules to header_transitions.
    for switch, switch_config in policy:
        assert(switch in topology)

        # Ignore rules for hosts
        if switch in topology.hosts():
            continue
        
        for rule in switch_config:
            # Convert patterns to boolean formula
            bform = ' & '.join(
                ['%s = %s' % (field,int_to_nusmvbitfield(field,val)) for field,val in rule.pattern.to_dict().iteritems() if val is not None])
            if bform == '':
                bform = 'switch = %s' % switch
            else:
                bform += ' & switch = %s' % switch
            for action,vals in [unpack_action(a) for a in rule.actions]:
                if action == 'modify':
                    # Generate transition rule
                    if vals[0] not in header_transitions:
                        header_transitions[vals[0]] = OrderedDict()
                    header_transitions[vals[0]][bform] = int_to_nusmvbitfield(vals[0], vals[1])
                elif action == 'forward':
                    if vals == ['OFPP_FLOOD']:
                        # TODO: implement flood
                        print "print_smv: flood not yet implemented."
                        assert(False)
                    elif vals == ['OFPP_CONTROLLER']:
                        switch_transition[bform] = 'CONTROLLER'
                    else:
                        # Find the next switch/port
                        out_port = vals[0]
                        next_switch = [sw for sw,p in topology.node[switch]['ports'].iteritems() if p == out_port]
                        assert(len(next_switch) == 1)
                        next_switch = next_switch[0]
                        new_in_port = topology.node[next_switch]['ports'][switch]
                        new_nusmv_in_port = int_to_nusmvbitfield(IN_PORT, new_in_port)

                        # Generate switch transition
                        if next_switch in topology.hosts():
                            switch_transition[bform] = 'WORLD'
                        else:
                            switch_transition[bform] = next_switch

                        # Generate in_port transition
                        if IN_PORT not in header_transitions:
                            header_transitions[IN_PORT] = OrderedDict()
                        header_transitions[IN_PORT][bform] = new_nusmv_in_port
                else:
                    # TODO: better error handling
                    assert(False)

    # Ensure all switch transition cases are covered
    for sw in topology:
        default = 'switch = %s' % sw
        if default not in switch_transition:
            switch_transition[default] = 'DROP'
    for sw in special_switches:
        switch_transition['switch = %s' % sw] = sw

    # Ensure all header transition cases are covered
    for header in header_transitions:
        header_transitions[header]['TRUE'] = header

    return switch_transition, header_transitions
        
# Return a string representation of a NuSMV file encoding the given 
# network topology and fowarding policy.
# @input topology: an NXTopo graph.
# @input policy: a network policy from policy.py.
def encode(topology, policy):
    switch_transition, header_transitions = generate_transitions(topology, policy)

    smv_vars = ['%s : unsigned word[%s];' % (h,PATTERN_LENGTHS[h]) for h in header_transitions]
    smv_vars.append('switch : {%s};' % ', '.join([str(sw) for sw in topology] + special_switches))

    smv_frozenvars = ['%s : unsigned word[%s];' % (h,PATTERN_LENGTHS[h]) for h in PATTERN_LENGTHS if h not in header_transitions]

    smv_assignments = []

    # Add switch transitions
    switch_assignment = '''
    next(switch) := 
        case
            %s
        esac;
''' % '\n            '.join(
    ['%s : %s;' % (b,m) for b,m in switch_transition.iteritems()])
    smv_assignments.append(switch_assignment)

    # Add transitions for each field
    for field in header_transitions:
        assignment = '''
    next(%s) :=
        case
            %s
        esac;
''' % (field,
       '\n            '.join(
           ['%s : %s;' % (b,m) for b,m in header_transitions[field].iteritems()]))
        smv_assignments.append(assignment)

    smv_text = '''
MODULE main

VAR
%s

FROZENVAR
%s

ASSIGN
%s

''' % ('\n'.join(smv_vars), 
       '\n'.join(smv_frozenvars), 
       '\n'.join(smv_assignments))

    return smv_text

def test():
    # Test: first example from the HotNets paper.
    G = nxt.NXTopo()
    G.add_nodes_from(["s", "f1", "f2", "f3", "d"])
    G.add_edges_from([("s", "f1", {'port':1}), ("s", "f2", {'port':2}), 
                      ("s", "f3", {'port':3}), ("f1", "d", {'port':1}), 
                      ("f2", "d", {'port':1}), ("f3", "d", {'port':1}),
                      ("f1", "s", {'port':2}), ("f2", "s", {'port':2}), 
                      ("f3", "s", {'port':2}), ("d", "f1", {'port':1}), 
                      ("d", "f2", {'port':2}), ("d", "f3", {'port':3})])

    s = SwitchConfiguration([
        Rule({'in_port':1, NW_DST:0}, [forward(1)]),
        Rule({'in_port':1}, [forward(2)]),
        Rule({'in_port':2, NW_DST:0}, [forward(1)]),
        Rule({'in_port':2}, [forward(1)]),
        Rule({'in_port':3}, [forward(2)]),
        Rule({'in_port':4}, [forward(2)]),
        Rule({'in_port':5}, [forward(3)]),
        Rule({'in_port':6}, [forward(3)])])
    f1 = SwitchConfiguration([Rule({}, [forward(1)])])
    f2 = SwitchConfiguration([Rule({}, [forward(1)])])
    f3 = SwitchConfiguration([Rule({}, [forward(1)])])

    policy = NetworkPolicy()
    policy.set_configuration("s", s)
    policy.set_configuration("f1", f1)
    policy.set_configuration("f2", f2)
    policy.set_configuration("f3", f3)

    smv_text = encode(G, policy, ['d'])
    print smv_text

