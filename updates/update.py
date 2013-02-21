from policy import NetworkPolicy

class UpdateObject(object):
    """ Represents sequence of NOX commands to perform an update """

    def __init__(self, plus_internal_policy, plus_edge_policy, 
                 minus_internal_policy, minus_edge_policy, 
                 new_priority, new_version):
        if (plus_internal_policy == None):
            self.plus_internal_policy = NetworkPolicy()
        else:
            self.plus_internal_policy = plus_internal_policy
        if (plus_edge_policy == None):
            self.plus_edge_policy = NetworkPolicy()
        else:
            self.plus_edge_policy = plus_edge_policy
        if (minus_internal_policy == None):
            self.minus_internal_policy = NetworkPolicy()
        else:
            self.minus_internal_policy = minus_internal_policy
        if (minus_edge_policy == None):
            self.minus_edge_policy = NetworkPolicy()
        else:
            self.minus_edge_policy = minus_edge_policy
        self.new_priority = new_priority
        self.new_version = new_version
