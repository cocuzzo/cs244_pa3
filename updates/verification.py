from print_smv import *
from subprocess import Popen, PIPE

# USING verification.py
# 
#     The verification.py file contains the KripkeModel class.  KripkeModel
#     objects represent a network topology and policy as a Kripke structure, for
#     use with a model checker and temporal logic formulas.
# 
#     The following python code builds a Kripke model from a topology and policy
#     and checks whether the topology + policy are packet loop-free.
# 
#         #/usr/bin/python
#         model = verification.KripkeModel(topology, policy)
# 
#     verification.py defines general network properties, like NO_LOOPS, that the
#     verify() function can check against a particular model.  
#     
#         boolean_result = model.verify(verification.NO_LOOPS)
#         if boolean_result then:
#             print 'Topology and policy do not contain packet loops.'
# 
#     In addition to predefined properties, KripkeModels can also verify raw CTL
#     formulas with the verify_ctl_string() function.
# 
#         # "AF DROP" : All packets are dropped.
#         boolean_result = model.verify_ctl_string("AF DROP") 
# 

#-----------------------------------------------------------------------------#
# Network properties                                                          #
#-----------------------------------------------------------------------------#

# Utility function for generating all (switch, port) ingress points.
def _generate_ingresses(model):
    ingress_pairs = []
    for edge_switch in model.topology.edge_switches():
        for edge_port in model.topology.edge_ports(edge_switch):
            ingress_pairs.append((edge_switch, edge_port))
    return ingress_pairs

# Generate a predicate that holds iff a state is an ingress state.
def _generate_ingress_starting_conditions(model):
    ingress_pairs = _generate_ingresses(model)
    starting_conditions = ['(switch = %s & in_port = %s)' % (s,int_to_nusmvbitfield(IN_PORT, p)) for s,p in ingress_pairs]
    if len(starting_conditions) == 0:
        return 'TRUE'
    return ' | '.join(starting_conditions)

# Turn a pattern object into a predicate string.
def _format_pattern(pat):
    assert(type(pat) == type(Pattern()))
    pred = ' & '.join( ['%s = %s' % (field,int_to_nusmvbitfield(field,val)) for field,val in pat.to_dict().iteritems()])
    if pred == '':
        return 'TRUE'
    return pred

# All packets entering a network eventually leave.
def NO_LOOPS(model):
    starting_conditions = _generate_ingress_starting_conditions(model)
    prop = '(%s) -> AF (switch = WORLD | switch = DROP)' % starting_conditions
    return prop

# All packets that may exist anywhere in the network matching 'pattern' are
# dropped.
# ingress: only consider packets matching 'pattern' at ingress switches.
def MATCH_DROP(pattern, ingress=True):
    def f(model):
        starting_conditions = 'TRUE'
        if ingress:
            starting_conditions = _generate_ingress_starting_conditions(model)
        if type(ingress) == type(''):
            starting_conditions = '(%s) & %s' % (starting_conditions, ingress)
        pat_pred = _format_pattern(pattern)
        prop = '((%s) & (%s)) -> AF switch = DROP' % (starting_conditions, pat_pred)
        return prop
    return f

# All packets that may exist anywhere in the network matching 'pattern' 
# eventually leave the network.
# ingress: only consider packets matching 'pattern' at ingress switches.
def MATCH_EGRESS(pattern, ingress=True):
    def f(model):
        starting_conditions = 'TRUE'
        if ingress:
            starting_conditions = _generate_ingress_starting_conditions(model)
        if type(ingress) == type(''):
            starting_conditions = '(%s) & %s' % (starting_conditions, ingress)
        pat_pred = _format_pattern(pattern)
        prop = '((%s) & (%s)) -> AF switch = WORLD' % (starting_conditions, pat_pred)
        return prop
    return f

# All packets that match 'pattern' eventually pass through every switch in the
# list 'switches'.  
# ingress: only consider packets matching 'pattern' at ingress switches.
def WAYPOINT_SWITCHES(pattern, switches, ingress=True):
    assert(type(switches) == type([]))
    assert(len(switches) > 0)
    def f(model):
        starting_conditions = 'TRUE'
        if ingress:
            starting_conditions = _generate_ingress_starting_conditions(model)
        if type(ingress) == type(''):
            starting_conditions = '(%s) & %s' % (starting_conditions, ingress)
        pat_pred = _format_pattern(pattern)
        switch_pred = ' & '.join(['AF switch = %s' % switch for switch in switches])
        prop = '((%s) & (%s)) -> (%s)' % (starting_conditions, pat_pred, switch_pred)
        return prop
    return f

# All packets that match 'pattern' never reach any switch in 'switches'.
# ingress: only consider packets matching 'pattern' at ingress switches.
def BLACKLIST_SWITCHES(pattern, switches, ingress=True):
    assert(type(switches) == type([]))
    assert(len(switches) > 0)
    def f(model):
        starting_conditions = 'TRUE'
        if ingress:
            starting_conditions = _generate_ingress_starting_conditions(model)
        if type(ingress) == type(''):
            starting_conditions = '(%s) & %s' % (starting_conditions, ingress)
        pat_pred = _format_pattern(pattern)
        switch_pred = ' & '.join(['AF switch != %s' % switch for switch in switches])
        prop = '((%s) & (%s)) -> (%s)' % (starting_conditions, pat_pred, switch_pred)
        return prop
    return f

# All packets that match 'pattern' eventually pass through every edge in 
# 'edges'.
# edges: list of pairs representing edges in the topology, consisting of
#        (switch1, switch2).
# ingress: only consider packets matching 'pattern' at ingress switches.
def WAYPOINT_EDGES(pattern, edges, ingress=True):
    def f(model):
        starting_conditions = 'TRUE'
        if ingress:
            starting_conditions = _generate_ingress_starting_conditions(model)
        if type(ingress) == type(''):
            starting_conditions = '(%s) & %s' % (starting_conditions, ingress)
        pat_pred = _format_pattern(pattern)
        edge_pred = ' & '.join(['EF (switch = %s -> (AX switch = %s))' % (s1, s2) for s1,s2 in edges])
        prop = '((%s) & (%s)) -> (%s)' % (starting_conditions, pat_pred, edge_pred)
        return prop
    return f

# All packets that match 'pattern' never pass through any edge in 'edges'.
# edges: list of pairs representing edges in the topology, consisting of
#        (switch1, switch2).
# ingress: only consider packets matching 'pattern' at ingress switches.
def BLACKLIST_EDGES(pattern, edges, ingress=True):
    def f(model):
        starting_conditions = 'TRUE'
        if ingress:
            starting_conditions = _generate_ingress_starting_conditions(model)
        if type(ingress) == type(''):
            starting_conditions = '(%s) & %s' % (starting_conditions, ingress)
        pat_pred = _format_pattern(pattern)
        edge_pred = ' & '.join(['AG (switch = %s -> -(EX switch = %s))' % (s1, s2) for s1,s2 in edges])
        prop = '((%s) & (%s)) -> (%s)' % (starting_conditions, pat_pred, edge_pred)
        return prop
    return f


#-----------------------------------------------------------------------------#
# Kripke Model of a network                                                   #
#-----------------------------------------------------------------------------#

class KripkeModel():

    def __init__(self, topology, policy):
        self.topology = topology
        self.policy = policy
        self.nusmv_file_body = encode(topology, policy)

    def verify(self, prop_fun):
        prop = prop_fun(self)
        return self.verify_ctl_string(prop)

    def verify_ctl_string(self, prop_str):
        model = self.nusmv_file_body + '\nCTLSPEC %s\n' % prop_str
        proc = Popen(['NuSMV'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate(input=model)
        msg = 'NuSMV stdout: %s\nNuSMV stderr: %s\n' % (out, err)
        msg += 'File:\n%s\n' % model
        if 'is true' not in out or 'is false' in out or err:
            return (False, msg)
        return (True, msg)

