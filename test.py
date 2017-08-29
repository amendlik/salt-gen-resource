import sys
import yaml
import unittest
import optparse
from SaltGenResource import ResourceGenerator
from mock import patch, MagicMock


class TestMapping(unittest.TestCase):

    def test_os_family_map1(self):
        os_family = ResourceGenerator._os_family('Linux')
        self.assertEqual(os_family, 'unix')

    def test_os_family_map2(self):
        os_family = ResourceGenerator._os_family('unknown')
        self.assertEqual(os_family, 'unknown')

    def test_os_arch_map1(self):
        os_arch = ResourceGenerator._os_arch('x86_64')
        self.assertEqual(os_arch, 'amd64')

    def test_os_arch_map1(self):
        os_arch = ResourceGenerator._os_arch('AMD64')
        self.assertEqual(os_arch, 'amd64')

    def test_os_arch_map2(self):
        os_arch = ResourceGenerator._os_arch('unknown')
        self.assertEqual(os_arch, 'unknown')


class TestNodeGenerator(unittest.TestCase):

    _base_args = ['-l', 'quiet']
    required_attributes = ['hostname', 'osArch', 'osFamily',
                           'osName', 'osVersion']
    mine = {
        'linmin': {
            'fqdn': 'minion1.example.com',
            'kernel': 'Linux',
            'kernelrelease':  '4.4.0-75-generic',
            'cpuarch': 'x86_64',
            'os': 'RedHat'
        },
        'winmin': {
            'fqdn': 'minion2.example.com',
            'kernel': 'Windows',
            'kernelrelease':  '6.3.9600',
            'cpuarch': 'AMD64',
            'os': 'Windows'
        }
    }


    def test_single_attribute(self):

        with patch('SaltGenResource.SaltNodesCommandParser', MockParser()) as parser:
            with patch('salt.client.Caller', MagicMock()) as caller:

                caller.return_value.cmd.return_value = self.mine
                caller.return_value.opts.return_value = parser.config
                parser.options.attributes = ['os']

                resources = ResourceGenerator().run()
                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)


    @unittest.skip("temporary")
    def test_multiple_attributes1(self, caller):
        caller.return_value.cmd.return_value = self.mine
        optional_attributes = ['os', 'os_family']
        args = self._base_args + ['-a', ' '.join(optional_attributes), '*']
        resources = ResourceGenerator(args).run()
        self._test_required_attributes(resources)
        #self._test_attributes(resources, optional_attributes)

    @unittest.skip("temporary")
    def test_multiple_attributes2(self, caller):
        caller.return_value.cmd.return_value = self.mine
        optional_attributes = ['os', 'os_family']
        args = self._base_args + ['-a', ','.join(optional_attributes), '*']
        resources = ResourceGenerator(args).run()
        self._test_required_attributes(resources)
        #self._test_attributes(resources, optional_attributes)

    @unittest.skip("temporary")
    def test_single_tag(self, caller):
        caller.return_value.cmd.return_value = self.mine
        tags = ['os']
        args = self._base_args + ['-t', tags[0], '*']
        resources = ResourceGenerator(args).run()
        self._test_required_attributes(resources)
        #self._test_tags(resources, tags)

    @unittest.skip("temporary")
    def test_multiple_tags1(self, caller):
        caller.return_value.cmd.return_value = self.mine
        tags = ['os', 'os_family']
        args = self._base_args + ['-t', ' '.join(tags), '*']
        resources = ResourceGenerator(args).run()
        self._test_required_attributes(resources)
        #self._test_tags(resources, tags)

    @unittest.skip("temporary")
    def test_multiple_tags1(self, caller):
        caller.return_value.cmd.return_value = self.mine
        tags = ['os', 'os_family']
        args = self._base_args + ['-t', ','.join(tags), '*']
        resources = ResourceGenerator(args).run()
        self._test_required_attributes(resources)
        #self._test_tags(resources, tags)

    @unittest.skip("temporary")
    def test_static_attributes(self, caller):
        caller.return_value.cmd.return_value = self.mine
        args = self._base_args + ['*', 'username=root', 'password=\'pw\'']
        resources = ResourceGenerator(args).run()
        self._test_required_attributes(resources)
        #self._test_attributes(resources, ['username', 'password'])

    def _test_required_attributes(self, resources):
        self.assertTrue(len(resources) > 0)
        for host, attributes in resources.iteritems():
            for attribute in self.required_attributes:
                self.assertIn(attribute, attributes)
                self.assertIsNotNone(attributes[attribute])
                self.assertNotEqual(attributes[attribute], '')

            self.assertIn(host, resources)
            self.assertEqual(
                resources[host]['hostname'],
                self.mine[host]['fqdn'])
            self.assertEqual(
                resources[host]['osArch'],
                ResourceGenerator._os_arch(self.mine[host]['cpuarch']))
            self.assertEqual(
                resources[host]['osFamily'],
                ResourceGenerator._os_family(self.mine[host]['kernel']))
            self.assertEqual(
                resources[host]['osName'],
                self.mine[host]['kernel'])
            self.assertEqual(
                resources[host]['osVersion'],
                self.mine[host]['kernelrelease'])

    def _test_attributes(self, resources, needed):
        self.assertTrue(len(resources) > 0)
        for host, attributes in resources.iteritems():
            for attribute in needed:
                self.assertIn(attribute, attributes)
                self.assertIsNotNone(attributes[attribute])
                self.assertNotEqual(attributes[attribute], '')

    def _test_tags(self, resources, needed):
        self.assertTrue(len(resources) > 0)
        for host, attributes in resources.iteritems():
            self.assertIn('tags', attributes)
            self.assertIsNotNone(attributes['tags'])
            self.assertTrue(len(attributes['tags']) >= len(needed))


class TestNodeTargeting(unittest.TestCase):

    _base_args = ['-l', 'quiet']
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


class MockParser:

    def __call__(self, *args, **kwargs):
        return self

    def __init__(self):
        with open("test_config.yaml", 'r') as stream:
            try:
                self.config = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open("test_options.yaml", 'r') as stream:
            try:
                self.options = optparse.Values(yaml.load(stream))
            except yaml.YAMLError as exc:
                print(exc)

        self.args = ''

    def parse_args(self, *args, **kwargs):
        return self.options, self.args

'''
@unittest.skip("skipping")
class TestServerNodeGenerator(TestNodeGenerator):
    _base_args = TestNodeGenerator._base_args + ['--include-server-node']

    def _test_attributes(self, resources, needed):
        super(TestServerNodeGenerator, self)._test_attributes(resources, needed)
        self.assertIn(ResourceGenerator._server_node_name, resources)
        self.assertEqual(
            resources[ResourceGenerator._server_node_name]['hostname'],
            ResourceGenerator._server_node_name)
'''


def unit_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNodeGenerator))
    suite.addTest(unittest.makeSuite(TestMapping))
    return suite


def integration_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNodeTargeting))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)

    result = runner.run(unit_tests())
    #runner.run(integration_tests())

    sys.exit(not result.wasSuccessful())
