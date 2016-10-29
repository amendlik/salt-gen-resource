import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
from SaltGenResource import ResourceGenerator


class TestNodeGenerator(unittest.TestCase):

    _base_args = []
    required_attributes = ['hostname', 'osArch', 'osFamily',
                           'osName', 'osVersion']

    def test_glob_targeting(self):
        args = self._base_args + ['*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)

    def test_cidr_targeting(self):
        args = self._base_args + ['-S', '0.0.0.0/0']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)

    def test_grain_targeting(self):
        args = self._base_args + ['-G', 'os:*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)

    def test_pcre_targeting(self):
        args = self._base_args + ['-E', '.*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)

    def test_grain_pcre_targeting(self):
        args = self._base_args + ['-P', 'os:.*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)

    def test_single_attribute(self):
        optional_attributes = ['os']
        args = self._base_args + ['-a', optional_attributes[0], '*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)
        self._test_attributes(resources, optional_attributes)

    def test_multiple_attributes1(self):
        optional_attributes = ['os', 'os_family']
        args = self._base_args + ['-a', ' '.join(optional_attributes), '*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)
        self._test_attributes(resources, optional_attributes)

    def test_multiple_attributes2(self):
        optional_attributes = ['os', 'os_family']
        args = self._base_args + ['-a', ','.join(optional_attributes), '*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)
        self._test_attributes(resources, optional_attributes)

    def test_single_tag(self):
        tags = ['os']
        args = self._base_args + ['-t', tags[0], '*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)
        self._test_tags(resources, tags)

    def test_multiple_tags1(self):
        tags = ['os', 'os_family']
        args = ['-t', ' '.join(tags), '*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)
        self._test_tags(resources, tags)

    def test_multiple_tags1(self):
        tags = ['os', 'os_family']
        args = self._base_args + ['-t', ','.join(tags), '*']
        resources = ResourceGenerator(args).run()
        self._test_attributes(resources, self.required_attributes)
        self._test_tags(resources, tags)

    def _test_attributes(self, resources, needed):
        for host, attributes in resources.iteritems():
            for attribute in needed:
                self.assertIn(attribute, attributes)
                self.assertIsNotNone(attributes[attribute])
                self.assertNotEqual(attributes[attribute], '')

    def _test_tags(self, resources, needed):
        for host, attributes in resources.iteritems():
            self.assertIn('tags', attributes)
            self.assertIsNotNone(attributes['tags'])
            self.assertTrue(len(attributes['tags']) >= len(needed))

class TestServerNodeGenerator(TestNodeGenerator):
    _base_args = ['--include-server-node']

    def _test_attributes(self, resources, needed):
        super(TestServerNodeGenerator, self)._test_attributes(resources, needed)
        self.assertIn(ResourceGenerator._server_node_name, resources)
        self.assertEqual(
            resources[ResourceGenerator._server_node_name]['hostname'],
            ResourceGenerator._server_node_name)


if __name__ == '__main__':
    unittest.main()
