import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
from SaltGenResource import ResourceGenerator


class TestResourceGenerator(unittest.TestCase):

    required_attributes = ['hostname', 'osArch', 'osFamily',
                           'osName', 'osVersion']

    def test_glob_targeting(self):
        args = ['*']
        resources = ResourceGenerator(args).get_nodes()
        self._test_required_attributes(resources)

    def test_cidr_targeting(self):
        args = ['-S', '0.0.0.0/0']
        resources = ResourceGenerator(args).get_nodes()
        self._test_required_attributes(resources)

    def test_grain_targeting(self):
        args = ['-G', 'os:*']
        resources = ResourceGenerator(args).get_nodes()
        self._test_required_attributes(resources)

    def _test_required_attributes(self, resources):
        for host, attributes in resources.iteritems():
            for attribute in self.required_attributes:
                self.assertIn(attribute, attributes)
                self.assertIsNotNone(attributes[attribute])
                self.assertNotEqual(attributes[attribute], '')

if __name__ == '__main__':
    unittest.main()
