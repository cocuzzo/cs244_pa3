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
# /updates/policy.py                                                           #
# Actions, Rules, Configurations, Policies                                     #
################################################################################

import string
import sys
import os
sys.path.append(os.environ['NOX_CORE_DIR'])
import nox.lib.openflow as openflow
import logging
import weakref
from abc import ABCMeta

log = logging.getLogger("frenetic.update.policy")


class Action(object):
    """ OpenFlow Action class.  """

    # TODO: Push the caching code into __new__()
    # Dictionaries for caching Action objects. One forward()
    # instance for each port, one instance for each other action
    _strip_vlan = None
    _forward = {}
    _flood = None
    _inport = None
    
    def __init__(self, tag, subexprs):
        self.tag = tag
        if isinstance(subexprs, list):
            self.subexprs = subexprs
        else:
            self.subexprs = list(subexprs)
            
    def __str__(self):
        return str(self.tag) + ": " + str(self.subexprs)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self is other:
            return True            
        if (self.tag == other.tag and
            len(self.subexprs) == len(self.subexprs)):
            for i in range(len(self.subexprs)):
                if not (self.subexprs[i] == other.subexprs[i]):
                    return False
            return True
        else:
            return False

    def __hash__(self):
        return hash((self.tag, tuple(self.subexprs)))

    nox_mod = { "srcmac": openflow.OFPAT_SET_DL_SRC,
               "dstmac": openflow.OFPAT_SET_DL_DST,
               "srcport": openflow.OFPAT_SET_TP_SRC,
               "dstport": openflow.OFPAT_SET_TP_DST,
               "srcip": openflow.OFPAT_SET_NW_SRC,
               "dstip": openflow.OFPAT_SET_NW_DST,
               "vlan": openflow.OFPAT_SET_VLAN_VID }
    
    nox_strip = { "vlan": openflow.OFPAT_STRIP_VLAN } 

    nox_field = { "vlan" : "dl_vlan",
                  "srcip" : "nw_src",
                  "dstip" : "nw_dst",
                  "srcmac" : "dl_src",
                  "dstmac" : "dl_dst" }

    def convert_to_nox_action(self):
        """ Returns a representation of the action in NOX format """
        
        if self.tag == "forward":
            [port] = self.subexprs
            return [openflow.OFPAT_OUTPUT, [0, port]]
        elif self.tag == "inport":
            port = openflow.OFPP_IN_PORT
            return [openflow.OFPAT_OUTPUT, [0, port]]
        elif self.tag == "flood":
            port = openflow.OFPP_FLOOD
            return [openflow.OFPAT_OUTPUT, [0, port]]
        elif self.tag == "modify":
            [field, val] = self.subexprs
            return [self.nox_mod[field], val]
        elif self.tag == "strip":
            [field] = self.subexprs
            return [self.nox_strip[field]]
        else:
            assert False

    def apply(self, pkt):
        if self.tag == "forward":
            [port] = self.subexprs
            output = Pattern(pkt, IN_PORT=Pattern.WILD)
            # output[IN_PORT] = Pattern.WILD
            return ((output, port), pkt)
        elif self.tag == "modify":
            [field, val] = self.subexprs
            if field in self.nox_field:
                field = self.nox_field[field]
            output = Pattern(pkt, {field:val})                    
            # output[field] = val
            return (None, output)
        elif self.tag == "strip":
            [field] = self.subexprs
            if field in self.nox_field:
                field = self.nox_field[field]
            output = Pattern(pkt, {field:val})                    
            return (None, output)
        else:
            assert False

def ipstr_to_int(a):
    octets = a.split('.')
    return int(octets[0]) << 24 |\
           int(octets[1]) << 16 |\
           int(octets[2]) <<  8 |\
           int(octets[3])


class VersionedPattern(object):
    """ 
    Wrapper that keeps a Pattern object, but sets the VLAN tags
    here.  This allows reuse on the "important" pattern fields with a
    minimal cost for keeping versions 
    """

    _instances = weakref.WeakValueDictionary()
    def __new__(cls, pattern, version):
        if (pattern, version) in VersionedPattern._instances:
            return VersionedPattern._instances[(pattern, version)]
        else:
            return super(VersionedPattern, cls).__new__(cls)
        
    def __init__(self, pattern, version):
        self.pattern = pattern
        self.DL_VLAN = version

        
    def __getattr__(self, key):
        if key == "DL_VLAN":
            return self.__dict__[key]
        else:
            return self.__dict__["pattern"].__dict__(key)

    def to_dict(self):
        _dict = self.__dict__["pattern"].to_dict()
        _dict["dl_vlan"] = self.DL_VLAN
        return _dict

    def __hash__(self):
        return hash((self.__dict__["pattern"], self.DL_VLAN))

    def __str__(self):
        return string.join(str(self.__dict__["pattern"]), ", DL_VLAN: " +
                           str(self.DL_VLAN))
            
class Pattern(object):
    """ 
    Packet pattern representation. Use Pattern.WILD in any field to wildcard
    """

    __metaclass__ = ABCMeta
    
    # Max int is signed, but IP addrs convert to L, so this needs to be L
    # WILD = (1 << 33) - 1 
    WILD = None
    HEADERS = [ "IN_PORT",
                "NW_SRC",
                "NW_DST",
                "AP_SRC",
                "AP_DST",
                "DL_SRC",
                "DL_DST",
                "DL_VLAN",
                "DL_VLAN_PCP",
                "DL_TYPE",
                "NW_SRC_N_WILD",
                "NW_DST_N_WILD",
                "NW_PROTO",
                "TP_SRC",
                "TP_DST" ]

    _instances = {}
    
    def __new__(cls, old=None, **kwargs):
        if old:
            if isinstance(old, dict):
                old_dict = old.copy()
            else:
                old_dict = old.to_dict().copy()
        else:
            old_dict = {}

        for header in kwargs:
            header_name = intern(header.lower())
            header_value = kwargs[header]
            if isinstance(header_value, str):
                header_value = intern(header_value)
            old_dict[header_name] = header_value

        # version = None
        # if "dl_vlan" in old_dict:
        #     version = old_dict["dl_vlan"]
        #     del old_dict["dl_vlan"]
        dict_items = old_dict.items()
        dict_items.sort()
        
        _hash = hash(tuple(dict_items))
        if _hash in Pattern._instances:
            # if not version is None:
            #     return VersionedPattern(Pattern._instances[_hash], version)
            # else:
            return Pattern._instances[_hash]
        else:
            new_inst = super(Pattern, cls).__new__(cls)
            super(Pattern, new_inst).__setattr__("_initialized", False)
            Pattern._instances[_hash] = new_inst
            # if not version is None:
            #     new_inst.__init__(old_dict)
            #     return VersionedPattern(new_inst, version)
            # else:
            return new_inst
        
                        
    def __init__(self, old=None, **kwargs):
        if self._initialized:
            return
        else:
            self.__dict__["_initialized"] = True
        self.__dict__["_dict"] = {}
        if not old:
            for header in Pattern.HEADERS:
                self.__dict__[header] = Pattern.WILD
        elif isinstance(old, dict):
            for header in Pattern.HEADERS:
                header_name = intern(header.lower())
                if header_name in old:
                    header_value = old[header_name]
                    # if isinstance(header_value, str):
                    #     header_value = intern(header_value)
                    self.__dict__[header] = header_value
                    if header_value:
                        self._dict[header_name] = header_value
                else:
                    self.__dict__[header] = Pattern.WILD
        elif isinstance(old, Pattern):
            for header in Pattern.HEADERS:
                header_value = old.__dict__[header]
                self.__dict__[header] = header_value
                if header_value:
                    self._dict[intern(header.lower())] = header_value
        else:
            assert(False)

        if kwargs:
            for header in kwargs:
                header_value = kwargs[header]
                # if isinstance(header_value, str):
                #     header_value = intern(header_value)
                self.__dict__[header] = header_value
                self._dict[intern(header.lower())] = header_value

        tmp_hash = hash(tuple(self.__dict__[header] for header in
                              Pattern.HEADERS))
        super(Pattern, self).__setattr__('_hash', tmp_hash)


    def intersects(self, other):
        """ Tests if the two patterns have packets in common """
        
        for header in [ header for header in Pattern.HEADERS if
                        (header not in ["NW_SRC", "NW_DST"]) ]:
                                       # "NW_SRC_N_WILD",
                                       # "NW_DST_N_WILD"]) ]:
            if not other.__dict__[header] == Pattern.WILD or \
                self.__dict__[header] == Pattern.WILD:
                if other.__dict__[header] != self.__dict__[header]:
                    return False
        return True



    def __getitem__(self, key):
        return self._dict[key]

    NON_WILDCARD_HEADERS = filter( lambda h: h not in [ # "NW_SRC",
                                                        # "NW_DST",
                                                        "NW_SRC_N_WILD",
                                                        "NW_DST_N_WILD"],
                                                        HEADERS)
    def __le__(self, other):
        """ 
        Partial ordering with full wildcard pattern at top,
        microflows at bottom 
        """
        
        # TODO: IP address prefix wildcarding
        for header in Pattern.NON_WILDCARD_HEADERS:
            # Optimization: relies on the fact that WILD == None
            if other.__dict__[header]:
                if other.__dict__[header] != self.__dict__[header]:
                    return False

        # for wild, ip in [("NW_SRC_N_WILD", "NW_SRC"),
        #                  ("NW_DST_N_WILD", "NW_DST")]:
        #     other_wild = other.__dict__[wild]
        #     other_ip = other.__dict__[ip]
        #     self_wild = self.__dict__[wild]
        #     self_ip = self.__dict__[ip]
            
        #     if other_wild != Pattern.WILD:
        #         shift = other_wild
        #         if self_wild != Pattern.WILD:
        #             if self_wild > shift:
        #                 return False
        #             else:
        #                 if self_ip == Pattern.WILD:
        #                     return False
        #                 elif not (other_ip >> shift) == (self_ip >> shift):
        #                     return False
        #     elif self_wild != Pattern.WILD:
        #         return False
        #     else:
        #         if other_ip != Pattern.WILD:
        #             if not other_ip == self_ip:
        #                 return False
                    
        # return self._tuple <= other._tuple
        return True

    def __setattr__(self, name, value):
        raise TypeError("can't modify immutable Pattern objects")

    def to_dict(self):
        """ Returns a dictionary suitable for passing to NOX """
        return self._dict.copy()

    def __iter__(self):
        return self._dict.iteritems()

    def __str__(self):
        return string.join([str(header) + ": " +
                            str(self.__dict__[header]) \
                            for header in Pattern.HEADERS \
                            if self.__dict__[header] != Pattern.WILD], ', ')

    def __hash__(self):
        return self._hash
        
Pattern.register(VersionedPattern)
           
def forward(port):
    """ Returns a forward Action(), cached by port """
    if not port in Action._forward:
        Action._forward[port] = Action("forward", [port])
    return Action._forward[port]

def flood():
    """ Returns a flood Action(), cached """    
    if not Action._flood:
        Action._flood = Action("flood", [])
    return Action._flood

def inport():
    """ Returns an inport Action(), cached """        
    if not Action._inport:
        Action._inport = Action("inport", [])    
    return Action._inport

def modify((field, val)):
    """ Returns a modify Action() """
    return Action("modify", [field, val])

def strip(field):
    """ Returns a strip() object. strip_vlan object is cached """
    if field == "vlan":
        if Action._strip_vlan is None:
            Action._strip_vlan = Action("strip", [field])
        return Action._strip_vlan
    return Action("strip", [field])

# patterns
IN_PORT = "in_port"
AP_SRC = "ap_src"
AP_DST = "ap_dst"
DL_SRC = "dl_src"
DL_DST = "dl_dst"
DL_VLAN = "dl_vlan"
DL_VLAN_PCP = "dl_vlan_pcp"
DL_TYPE = "dl_type"
NW_SRC = "nw_src"
NW_DST = "nw_dst"
NW_SRC_N_WILD = "nw_src_n_wild"
NW_DST_N_WILD = "nw_dst_n_wild"
NW_PROTO = "nw_proto"
TP_SRC = "tp_src"
TP_DST = "tp_dst"

PATTERN_LENGTHS = \
  { IN_PORT : 16,
    AP_SRC : 48,
    AP_DST : 48,
    DL_SRC : 48,
    DL_DST : 48,
    DL_VLAN : 16,
    DL_VLAN_PCP : 8,
    DL_TYPE : 16,
    NW_SRC : 32,
    NW_DST : 32,
    NW_PROTO : 8,
    TP_SRC : 16,
    TP_DST : 16 }

def pattern_to_int(pattern, val):
    """ Convert a value of type pattern into an integer equivalent """
    if pattern in [IN_PORT, DL_TYPE]:
        return val
    elif pattern in [NW_SRC, NW_DST]:
        assert(isinstance(val, str))
        # val should have type x.x.x.x
        places = val.split('.')
        assert(len(places) == 4)
        rv = 0
        for i in xrange(0, 4):
            rv += i * 256 + int(places[i])
        return rv
    else:
        print >> sys.stderr, '(%s, %s) not yet implemented.' % (pattern, 
                                                                str(val))
        assert()

def list_eq(l1, l2):
    """ Compares two lists for extensional equality """
    if l1 == l2:
        return True
    elif len(l1) != len(l2):
        return False
    else:
        for i in range(len(l1)):
            if l1[i] != l2[i]:
                return False
        return True

class Rule(object):
    """ Class for representing OpenFlow rules """
    def __init__(self, pattern, actions, priority=0xffff, parent=None, 
                 edge=False):
        assert(isinstance(pattern, Pattern) and isinstance(actions, list))
        self.pattern = pattern
        self.actions = list(actions)
        self.parent = parent
        self.priority = priority
        self.edge = edge

    def __str__(self):
        return "(" + str(self.priority) + ", " + \
          str(self.pattern) + ", " + str(self.actions) + ")"

    def __eq__(self, other):
        if (isinstance(other, Rule) 
            and self.pattern == other.pattern
            and list_eq(self.actions, other.actions)):
            return True
        else:
            return False
        
    def convert_to_nox_rule(self):
        """ Returns representation suitable to pass to NOX """
        nox_pattern = self.pattern.to_dict()
        nox_actions = [ a.convert_to_nox_action() for a in self.actions ]
        return (nox_pattern, nox_actions)

    def apply(self, flow):
        output = []
        current_packet = flow
        for action in self.actions:
            (out, current_packet) = action.apply(current_packet)
            if out:
                output.append(out)
        return output

    def size(self):
        return { 'Patterns' : len(self.pattern), 'Actions' : len(self.actions)}

    def __hash__(self):
        return (self.pattern, tuple(self.actions)).__hash__()

class SwitchConfiguration(object):
    """ Wrapper class for list of rules """
    
    def __init__(self, rules=None):
        if not rules:
            self.rules = {}
        elif isinstance(rules, SwitchConfiguration):
            self.rules = dict(rules.rules)
        else:
            self.rules = dict([(rule.pattern, rule) for rule in rules])
            
    def __iter__(self):
        return self.rules.values().__iter__()

    def __len__(self):
        return len(self.rules.values())
        
    def add_rule(self, rule):
        """ Installs new rule in config. If a rule with the exact same
        pattern already exists, the new rule overwrites it """
        
        assert(isinstance(rule, Rule))
        # TODO: keep rules in sorted order
        # Not just rule equality, but we need to remove rules with the
        # same pattern to avoid ambiguity
        self.rules[rule.pattern] = rule

    def __contains__(self, pkt):
        if isinstance(pkt, Pattern):
            return pkt in self.rules
        elif isinstance(pkt, Rule):
            return self.contains_matching_rule(pkt)
        
    def __getitem__(self, pkt):
        return self.rules[pkt]

    def contains_matching_rule(self, other_rule):
        """ Returns true if config contains a rule that exactly matches """
        assert(isinstance(other_rule, Rule))
        # MJR: dict equality is reference equality, we want extensional equality
        if other_rule.pattern in self.rules:
            return other_rule == self.rules[other_rule.pattern]

    def contains_pattern_matching_rule(self, other_rule):
        """ 
        Returns true if config contains a rule with the exact same pattern 
        """
        assert(isinstance(other_rule, Rule))
        # MJR: dict equality is reference equality, we want extensional equality
        return other_rule.pattern in self.rules

    def convert_to_nox_configuration(self):
        """ Returns a representation suitable for passing to NOX """
        return [rule.convert_to_nox_rule() for rule in self.rules.values()]

    def __str__(self):
        return "C:" + '\t' + string.join([rule.__str__() \
                                          for rule in self.rules.values()], '\n\t')
    
    def is_empty(self):
        """ Returns if config contains no rules """
        return self.rules == {}

    def size(self):
        if len(self.rules) > 0:
            sum_patterns, sum_actions = \
              reduce(lambda (p1,a1),(p2,a2): (p1+p2,a1+a2), 
                     [(d['Patterns'],d['Actions']) \
                      for d in [ r.size() for r in self.rules.values()]])
        else:
            sum_patterns, sum_actions = 0, 0
        return {'Rules' : len(self.rules.values()), 
                'Patterns' : sum_patterns, 
                'Actions' : sum_actions}

    def remove(self, rule):
        assert(isinstance(rule, Rule))
        assert(rule in self)
        del self.rules[rule.pattern]

    def diff(self, other):
        """ Returns self - other """
        diff = SwitchConfiguration()
        for r in self:
            if r not in other:
                diff.add_rule(r)
        return diff
    
    def __sub__(self, other):
        return self.diff(other)

    def __add__(self, other):
        config = SwitchConfiguration(self.rules.values())
        for rule in other:
            config.add_rule(rule)
        return config

    def __len__(self):
        return len(self.rules.values())

    def __eq__(self, other):
        assert(isinstance(other, SwitchConfiguration))
        for rule1 in self:
            if not rule1 in other:
                return False
        for rule2 in other:
            if not rule2 in self:
                return False
        return True

    def __le__(self, other):
        assert isinstance(other, SwitchConfiguration)
        for rule in self:
            if not rule in other:
                return False
        return True
                
class NetworkPolicy(object): 
    """ Collection of SwitchConfigurations """
   
    def __init__(self, configs=None):
        if not configs:
            self.configs = {}
        else:
            self.configs = dict(configs)

    def set_priority(self, priority):
        """ Hack to set default priority for each rule in each config """
        for switch, config in self:
            for rule in config:
                rule.priority = priority

    def switches(self):
        """ Switches in network policy """
        return self.configs.keys()

    def get_configuration(self, switch):
        """ Returns config for switch. Returns empty config by default """
        if switch in self.configs:
            return self.configs[switch]
        else:
            return SwitchConfiguration([])

    def __getitem__(self, switch):
        return self.get_configuration(switch)

    def __contains__(self, switch):
        return switch in self.configs

    def set_configuration(self, switch, config):
        """ Sets switch configuration to config """
        assert(isinstance(config, SwitchConfiguration))
        self.configs[switch] = config

    def __setitem__(self, switch, config):
        self.set_configuration(switch, config)
        
    def __iter__(self):
        return self.configs.iteritems()

    def __str__(self):        
        l = sorted(self.configs.items())
        return string.join([str(switch) + "\n" + str(config) \
                            for switch, config in l], "\n")

    def is_empty(self):
        """ Is every config in network empty() """
        return reduce(lambda b, c: b and c.is_empty(), 
                      self.configs.values(), True)

    def __len__(self):
        length = 0
        for switch, config in self:
            length += len(config)
        return length

    def _diff(self, other, comp_fun):
        """ 
        Helper function that abstracts out the comparison function for
        computing diff of two policies
        """
        diff_policy = NetworkPolicy()
        for switch, config in self:
            diff_config = SwitchConfiguration()
            other_config = other[switch]
            for rule in config:
                if not comp_fun(other_config, rule):
                    diff_config.add_rule(rule)
            if diff_config:
                diff_policy[switch] = diff_config
        return diff_policy
        
    def diff(self, other):
        """ Rules in self - other priorities come from self """
        return self._diff(other, SwitchConfiguration.contains_matching_rule)

    def pattern_diff(self, other):
        """ Normal diff works on rule equality, this works on rule
        pattern equality """
        return self._diff(other, 
                          SwitchConfiguration.contains_pattern_matching_rule)

    def pattern_intersect(self, other):
        """ 
        Returns policy of configurations consisting of rules in common
        (by pattern) in both policies
        """
        return (other + self).pattern_diff(self.pattern_diff(other)).pattern_diff(other.pattern_diff(self))

    def __sub__(self, other):
        return self.diff(other)

    def __add__(self, other):
        union_policy = NetworkPolicy()
        union_switches = set(self.switches()).union(set(other.switches()))
        
        for switch in union_switches:
            config = SwitchConfiguration()
            other_config = SwitchConfiguration()
            
            if switch in self:
                config = self[switch]
            if switch in other:
                other_config = other[switch]

            union_policy[switch] = config + other_config
        
        return union_policy

    def convert_to_nox_policy(self):
        """ Representation of policy suitable for passing to NOX """
        policy = {}
        for switch, config in self.configs.iteritems():
            policy[switch] = config.convert_to_nox_configuration()
        return policy

    def flows(self):
        flows = {}
        for switch, config in self.configs.iteritems():
            flows[switch] = [ (rule.pattern, rule.actions) for rule in config ]
        return flows

    def size(self):
        if len(self.configs) > 0:
            sum_rules, sum_patterns, sum_actions = \
              reduce(lambda (r1, p1, a1), (r2, p2, a2): (r1+r2, p1+p2, a1+a2),
                     [(d['Rules'], d['Patterns'], d['Actions']) \
                      for d in [ x.size() for x in self.configs.values()]])
        else:
            sum_rules, sum_patterns, sum_actions = 0, 0, 0
        return {'SwitchConfigurations' : len(self.configs),
                'Rules' : sum_rules,
                'Patterns' : sum_patterns,
                'Actions' : sum_actions}

    def __eq__(self, other):
        if not isinstance(other, NetworkPolicy):
            return False
        if set(self.switches()) != set(other.switches()):
            return False
        for switch, config in self:
            if not other[switch] == config:
                return False
        return True

    def __le__(self, other):
        if not isinstance(other, NetworkPolicy):
            return False
        if not set(self.switches()) <= set(other.switches()):
            return False
        for switch, config in self:
            if not config <= other[switch]:
                return False
        return True
        
            
def policy_of_dict(d):
    """ Converts dictionary (NOX) representation of policy into objects. """
    # FIXME: Redundant w/ __init__()?
    policy = NetworkPolicy()
    for switch, l in d.iteritems():
        config = SwitchConfiguration()
        for p, a in l:
            config.add_rule(Rule(Pattern(p), a))
        policy[switch] = config
    return policy
