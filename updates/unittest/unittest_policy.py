import unittest
from policy import Action, Pattern, Rule, SwitchConfiguration, NetworkPolicy, openflow

# TODO:
#     SwitchConfiguration
#     NetworkPolicy

class testAction(unittest.TestCase):
    """
    Test class for Action objects
    """

    # TODO:
    #     apply()
    def testActionConvertToNox(self):
        act = Action("forward", [1])

        self.assertEqual(act.convert_to_nox_action(),
                         [openflow.OFPAT_OUTPUT, [0, 1]])

    def testActionEqual(self):
        act1 = Action("strip", ["vlan"])
        act2 = Action("strip", ["vlan"])

        self.assertEqual(act1, act2)

    def testActionInequal(self):
        act1 = Action("modify", ["srcip", "10.0.0.1"])
        act2 = Action("modify", ["srcip", "10.0.0.2"])

        self.assertNotEqual(act1, act2)
        
class testPattern(unittest.TestCase):
    """
    Test class for Pattern objects
    """

    # TODO:
    #     __getitem__
    #     to_dict
    #     __iter__
    #     __set_attr__
    #     __le__
    #     __le__ on IP wildcards
    #     versioning caching crap
    def testPatternIntersectionReflexive(self):
        patt = Pattern(nw_src="10.0.0.1")

        self.assertTrue(patt.intersects(patt))
        
    def testPatternIntersection(self):
        pattern1 = Pattern(nw_src="10.0.0.1")
        pattern2 = Pattern(in_port=1)

        self.assertTrue(pattern1.intersects(pattern2))
        self.assertTrue(pattern2.intersects(pattern1))
        
class testRule(unittest.TestCase):
    """
    Test class for Rule objects
    """

    def testRuleEquality(self):
        pat1 = Pattern(in_port=3, dl_type=2048, nw_src="10.0.0.2", nw_dst="10.0.0.12")
        act1 = Action("forward", [1])

        pat2 = Pattern(in_port=3, dl_type=2048, nw_src="10.0.0.2", nw_dst="10.0.0.12")
        act2 = Action("forward", [1])

        r1 = Rule(pat1, [act1])
        r2 = Rule(pat2, [act2])

        self.assertEqual(r1, r2)

    def testRuleEqualityReflexive(self):
        pat1 = Pattern(nw_src="10.0.0.1")
        act1 = Action("modify", ["vlan", 1])
        act2 = Action("forward", [2])

        r1 = Rule(pat1, [act1, act2])
        r2 = Rule(pat1, [act1, act2])

        self.assertEqual(r1, r2)

    def testRuleInequality(self):
        pat1 = Pattern(nw_dst="192.168.2.1", in_port=1)
        act1 = Action("modify", ["nw_dst", "192.168.2.2"])
        act2 = Action("forward", [2])

        r1 = Rule(pat1, [act1,act2])
        r2 = Rule(pat1, [act1])

        self.assertNotEqual(r1, r2)

class testConfig(unittest.TestCase):
    """
    Test class for SwitchConfiguration objects
    """

    def testConfigMembership(self):
        pat1 = Pattern(in_port=3, dl_type=2048, nw_src="10.0.0.2", nw_dst="10.0.0.12")
        act1 = Action("forward", [1])
        r1 = Rule(pat1, [act1])
        c = SwitchConfiguration([r1])

        self.assertTrue(r1 in c)

    def testConfigAddRule(self):
        pat1 = Pattern(in_port=3, dl_type=2048, nw_src="10.0.0.2", nw_dst="10.0.0.12")
        act1 = Action("forward", [1])
        r1 = Rule(pat1, [act1])

        c1 = SwitchConfiguration([r1])
        c2 = SwitchConfiguration()
        c2.add_rule(r1)

        self.assertEqual(c1,c2)

    def testConfigSum(self):
        pat1 = Pattern(in_port=3, nw_src="10.0.0.2", nw_dst="10.0.0.12")
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        pat2 = Pattern(nw_src="10.0.0.1", nw_dst="10.0.0.10")
        r2 = Rule(pat2, [])

        c1 = SwitchConfiguration([r1])
        c2 = SwitchConfiguration([r2])
        c3 = SwitchConfiguration([r1,r2])

        self.assertEqual(c1 + c2, c3)

    def testConfigDiff(self):
        pat1 = Pattern(in_port=3, nw_src="10.0.0.2", nw_dst="10.0.0.12")
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        pat2 = Pattern(nw_src="10.0.0.1", nw_dst="10.0.0.10")
        r2 = Rule(pat2, [])

        c1 = SwitchConfiguration([r1,r2])        
        c2 = SwitchConfiguration([r1])
        c3 = SwitchConfiguration([r2])

        self.assertEqual(c1 - c2, c3)

class testPolicy(unittest.TestCase):
    """
    Test class for NetworkPolicy objects
    """

    def testPolicyGetConfig(self):
        pat1 = Pattern(in_port=2)
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        c1 = SwitchConfiguration([r1])
        pol1 = NetworkPolicy({1:c1})

        self.assertEqual(c1, pol1[1])

    def testPolicySetConfig(self):
        pat1 = Pattern(in_port=2)
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        c1 = SwitchConfiguration([r1])
        pol1 = NetworkPolicy({1:c1})

        pol2 = NetworkPolicy()

        pol2[1] = c1

        self.assertEqual(pol1, pol2)

    def testPolicyNotEmpty(self):
        pat1 = Pattern(in_port=2)
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        c1 = SwitchConfiguration([r1])
        pol1 = NetworkPolicy({1:c1})

        self.assertFalse(pol1.is_empty())

    def testPolicyEmpty(self):
        pol1 = NetworkPolicy()

        self.assertTrue(pol1.is_empty())

    def testPolicyBool(self):
        pat1 = Pattern(in_port=2)
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        c1 = SwitchConfiguration([r1])
        pol1 = NetworkPolicy({1:c1})

        self.assertTrue(pol1)

    def testPolicySum1(self):
        pat1 = Pattern(in_port=2)
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        c1 = SwitchConfiguration([r1])
        pol1 = NetworkPolicy({1:c1})

        pat2 = Pattern(in_port=3)
        r2 = Rule(pat2, [])
        c2 = SwitchConfiguration([r2])
        pol2 = NetworkPolicy({2:c2})

        pol3 = NetworkPolicy({1:c1, 2:c2})

        self.assertEqual(pol1 + pol2, pol3)

    def testPolicySum2(self):
        pat1 = Pattern(in_port=2)
        act1 = Action("forward", [3])
        r1 = Rule(pat1, [act1])
        c1 = SwitchConfiguration([r1])
        pol1 = NetworkPolicy({1:c1})

        pat2 = Pattern(in_port=3)
        r2 = Rule(pat2, [])
        c2 = SwitchConfiguration([r2])
        pol2 = NetworkPolicy({1:c2})

        pol3 = NetworkPolicy({1: c1 + c2})

        self.assertEqual(pol1 + pol2, pol3)

    def testPatternIntersect(self):
        pat1 = Pattern(dl_vlan=1)
        pat2 = Pattern(dl_vlan=2)
        act = Action("forward", [3])

        r1 = Rule(pat1, [act])
        r2 = Rule(pat2, [act])

        c1 = SwitchConfiguration([r1])
        c2 = SwitchConfiguration([r2])

        pol1 = NetworkPolicy({1: c1})
        pol2 = NetworkPolicy({1: c2})

        self.assertEqual(pol1.pattern_intersect(pol2), NetworkPolicy())
        
        
if __name__ == '__main__':

    unittest.main()
