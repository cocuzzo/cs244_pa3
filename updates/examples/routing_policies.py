from policy import *
import networkx as nx
from collections import defaultdict

import logging

log = logging.getLogger("frenetic.update.examples.routing_policy")

def ip(h):
    return "10.0.0." + str(h)

def shortest_path_policy(graph1, graph2):
    # Take two graphs as arguments, one with all the switches and one
    # with some removed. For each host, flip a coin to decide if it
    # will be routed using the full or partial graph.
    # Because hosts are single-homed, we can save a lot of computation
    # by computing shortest paths on the subgraph of switches instead
    # the full graph of switches and hosts
    raw = defaultdict(lambda:[])
    sub_graph1 = graph1.copy()
    sub_graph1.remove_nodes_from(sub_graph1.hosts())
    sub_graph2 = graph2.copy()
    sub_graph2.remove_nodes_from(sub_graph2.hosts())
    paths1 = nx.all_pairs_shortest_path(sub_graph1)
    paths2 = nx.all_pairs_shortest_path(sub_graph2)
    hosts = graph1.hosts()
    for src in hosts:
        for dst in hosts:
            if src != dst:
                if hash(src + dst) % 5:
                    paths = paths1
                    graph = graph1
                else:
                    paths = paths2
                    graph = graph2
                # Grab hosts' switches
                try:
                    if len(graph1.neighbors(src)) > 1:
                        log.debug(str(src) + " nbrs: " + str(graph1.neighbors(src)))
                    src_sw = graph1.neighbors(src)[0]
                except IndexError:
                    # log.debug("Index error! src host " + str(src))
                    break
                try:                    
                    dst_sw = graph1.neighbors(dst)[0]
                except IndexError:
                    # log.debug("Index error! dst host " + str(dst))
                    continue
                try:
                    path = [src] + paths[src_sw][dst_sw] + [dst]
                except KeyError:
                    # log.debug("Key error! switches " + str(src_sw) + " and " + str(dst_sw))
                    continue
                last = path.pop(0)
                curr = path.pop(0)
                for next in path:
                    inport = graph1.node[curr]['ports'][last]
                    outport = graph1.node[curr]['ports'][next]
                    pat = { IN_PORT:inport, DL_TYPE:0x800, \
                            NW_SRC:ip(src), NW_DST:ip(dst) }
                    acts = [forward(outport)]
                    raw[curr].append((pat,acts))
                    last = curr
                    curr = next
    return policy_of_dict(raw)

def spanning_tree_policy1(graph, address):
    raw = defaultdict(lambda:[])    
    tree = nx.minimum_spanning_tree(graph)
    switches = [ n for n in tree.nodes() if tree.node[n]['isSwitch'] ]
    for switch in switches:
        neighbors = tree.neighbors(switch)
        all_ports_assoc = tree.node[switch]['ports'].items()
        tree_ports = [ p for (s,p) in all_ports_assoc if s in neighbors ]
        for p in tree_ports:
            pattern = {DL_TYPE:0x800,NW_DST:address, IN_PORT:p}
            actions = [forward(q) for q in tree_ports if q != p]
            raw[switch].append((pattern,actions))
    return policy_of_dict(raw)

def spanning_tree_policy(graph1, graph2):
    # This assumes NetworkX 1.6, but 1.2 is installed by default. Upgrade if this line causes a problem
    graph1.remove_nodes_from(graph1.hosts()[::2])
    graph2.remove_nodes_from(graph2.hosts()[1::2])
    policy1 = spanning_tree_policy1(graph1, "239.0.0.1")
    policy2 = spanning_tree_policy1(graph2, "239.0.0.2")
    return policy1 + policy2

# def fattree_policy(graph):
#     raw = defaultdict(lambda:[])

#     edgeSwitches = set(graph.edge_switches())
#     try:
#         coreSwitch = (set(graph.switches()) - edgeSwitches).pop()
#     except KeyError:
#         coreSwitch = None
    
    
#     for switch in edgeSwitches:
#         nbrs = set(graph.neighbors(switch))
#         for src in nbrs:
#             if graph.node[nbr]['isSwitch']:
#                 continue
#             for dst in graph.hosts():
#                 if dst not in nbrs:
#                     inport = graph.node[switch]['ports'][src]
#                     # Assume that if there is a coreswitch, then it is
#                     # fully connected to edge switches
#                     outport = graph.node[switch]['ports'][coreSwitch]
#                     pat = { IN_PORT:inport, DL_TYPE:0x800, \
#                             NW_SRC:ip(src), NW_DST:ip(dst) }
#                     acts = [forward(outport)]
#                     raw[curr].append((pat,acts))
#                 else:
#                     inport = graph.node[switch]['ports'][src]
#                     # Assume that if there is a coreswitch, then it is
#                     # fully connected to edge switches
#                     outport = graph.node[switch]['ports'][dst]
#                     pat = { IN_PORT:inport, DL_TYPE:0x800, \
#                             NW_SRC:ip(src), NW_DST:ip(dst) }
#                     acts = [forward(outport)]
#                     raw[curr].append((pat,acts))                    
            
        
    
def hosts_to_remove(version, graph):
    if version == 0:
        return graph.hosts()[::11]
    if len(graph.hosts()) < 2:
        return []
    if version == 1:
        return graph.hosts()[::8]
    if version == 2:
        return graph.hosts()[::5]
