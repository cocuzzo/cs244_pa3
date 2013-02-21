from waxman_topo import Topology

global networkSize

networkSize = None
def set_size(size):
    global networkSize
    networkSize = size

def links_to_remove(version, graph):
    if version == 0:
        return []
    if len(graph.coreSwitches) < 2:
        return []
    return [ (graph.coreSwitches[idx], graph.edgeSwitches[idx+version]) for idx in range(len(graph.coreSwitches))]

def nodes_to_remove(version, graph):
    if version == 0:
        return []
    return [ host for host in graph.hosts() if host % 10 == (version + 1) ]

edges_to_remove = [ [(101,107),(103,108),(104,108)],
                    [(101,108),(103,107),(105,108)],
                    [] ]
def switches_to_remove(version, graph):
    if version == 0:
        return []
    return [ core for core in graph.coreSwitches if core % 5 == (version + 1) ]

def _topology1(version, topology=Topology):
    global networkSize
    graph = topology(networkSize).nx_graph()
    graph.remove_nodes_from(nodes_to_remove(version, graph))
    graph.remove_edges_from(edges_to_remove[0])
    return graph

def _topology2(version, topology=Topology):
    global networkSize    
    graph = topology(networkSize).nx_graph()
    graph.remove_nodes_from(nodes_to_remove(0, graph))
    graph.remove_edges_from(edges_to_remove[version])
    return graph

def _topology3(version, topology=Topology):
    global networkSize        
    graph = topology(networkSize).nx_graph()
    graph.remove_nodes_from(nodes_to_remove(version, graph))
    graph.remove_edges_from(edges_to_remove[version])
    return graph

topologies = [ _topology1,
               _topology2,
               _topology3 ]
