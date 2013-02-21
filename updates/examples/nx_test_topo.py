import networkx as nx

class Foo(nx.Graph):

    def __init__(self, foo):
        super(Foo, self).__init__(self)

G = Foo(1)
G.subgraph([])    
    
