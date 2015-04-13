import unittest
from libs.funcs import cache

class TestCache(unittest.TestCase):

    def setUp(self):
        cache.flush()
        cache.collectStats = True
        cache.debug = True

    @cache.store
    def collecting(self):
        pass

    def test_cache(self):
        for _ in range(0, 9):
            self.collecting()
        okTxt = "Total collecting((<test_cache.TestCache testMethod=test_cache>,)) Hits: 8 -- Miss: 1"
        self.failUnlessEqual(cache.getStatistics(), okTxt)
        cache.getStatistics(detailed=False)
        cache.collectStats = False

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCache))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
