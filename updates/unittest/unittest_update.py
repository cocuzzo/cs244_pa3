import unittest
from update_lib import empty_update, can_use_extension_update, extension_update, subspace_update, island_update, full_per_packet_update


# TODO:
#     SwitchConfiguration
#     NetworkPolicy

class testUpdate(unittest.TestCase):
    """
    Test class for update_lib
    """

    # TODO:
    #     empty_update
    #     can_use_extension_update
    #     extension_update
    #     subspace_update
    #     island_update
    #     full_per_packet_update
    def testActionConvertToNox(self):
        act = Action("forward", [1])

        self.assertEqual(act.convert_to_nox_action(),
                         [openflow.OFPAT_OUTPUT, [0, 1]])

if __name__ == '__main__':

    unittest.main()
    # suiteFew = unittest.TestSuite()
    # suiteFew.addTest(testBlogger("testPostNewEntry"))
    # suiteFew.addTest(testBlogger("testDeleteAllEntries"))
    # #unittest.TextTestRunner(verbosity=2).run(suiteFew)
    # unittest.TextTestRunner(verbosity=2).run(suite())
