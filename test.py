import sys
import yaml
import unittest
import optparse
from SaltGenResource import ResourceGenerator, SaltNodesCommandParser
from mock import patch, Mock


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

    def test_os_arch_map2(self):
        os_arch = ResourceGenerator._os_arch('AMD64')
        self.assertEqual(os_arch, 'amd64')

    def test_os_arch_map3(self):
        os_arch = ResourceGenerator._os_arch('unknown')
        self.assertEqual(os_arch, 'unknown')


class TestNodeGenerator(unittest.TestCase):

    include_server_node = False
    required_attributes = ['hostname', 'osArch', 'osFamily',
                           'osName', 'osVersion']
    default_args = ['mine.get', '*', 'grains.items']
    default_kwargs = {'tgt_type': 'glob'}

    @classmethod
    def setUpClass(cls):

        # Load mine return data
        with open("test_mine.yaml", 'r') as stream:
            try:
                cls.mine = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        # Load grains for server node
        with open("test_config.yaml", 'r') as stream:
            try:
                cls.server_grains = yaml.load(stream)['grains']
            except yaml.YAMLError as exc:
                print(exc)

    def test_single_attribute(self):
        with patch('SaltGenResource.SaltNodesCommandParser', MockParser()) as parser:
            with patch('salt.client.Caller', MockCaller()) as caller:

                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs['exclude_minion'] = self.include_server_node

                parser.options.attributes = ['os']
                resources = ResourceGenerator().run()

                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_multiple_attributes(self):
        with patch('SaltGenResource.SaltNodesCommandParser', MockParser()) as parser:
            with patch('salt.client.Caller', MockCaller()) as caller:

                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs['exclude_minion'] = self.include_server_node

                parser.options.attributes = ['os', 'os_family']
                resources = ResourceGenerator().run()

                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_single_tag(self):
        with patch('SaltGenResource.SaltNodesCommandParser', MockParser()) as parser:
            with patch('salt.client.Caller', MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs['exclude_minion'] = self.include_server_node

                parser.options.tags = ['os']
                resources = ResourceGenerator().run()

                self._test_required_attributes(resources)
                self._test_tags(resources, parser.options.tags)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_multiple_tags(self):
        with patch('SaltGenResource.SaltNodesCommandParser', MockParser()) as parser:
            with patch('salt.client.Caller', MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs['exclude_minion'] = self.include_server_node

                parser.options.tags = ['os', 'kernelrelease']
                resources = ResourceGenerator().run()

                self._test_required_attributes(resources)
                self._test_tags(resources, parser.options.tags)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_static_attributes(self):
        with patch('SaltGenResource.SaltNodesCommandParser', MockParser()) as parser:
            with patch('salt.client.Caller', MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs['exclude_minion'] = self.include_server_node

                parser.args = ['color=yellow', 'pattern=\'polka dot\'']
                resources = ResourceGenerator().run()

                self._test_required_attributes(resources)
                self._test_attributes(resources, ['color', 'pattern'])

                for host, attributes in resources.iteritems():
                    self.assertEqual(resources[host]['color'], 'yellow')
                    self.assertEqual(resources[host]['pattern'], 'polka dot')

                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_static_username(self):
        with patch('SaltGenResource.SaltNodesCommandParser', MockParser()) as parser:
            with patch('salt.client.Caller', MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs['exclude_minion'] = self.include_server_node

                parser.args = ['username=root']
                resources = ResourceGenerator().run()

                self._test_required_attributes(resources)
                self._test_attributes(resources, ['username'])

                for host, attributes in resources.iteritems():
                    if host == ResourceGenerator._server_node_name:
                        self.assertEqual(resources[host]['username'], parser.options.server_node_user)
                    else:
                        self.assertEqual(resources[host]['username'], 'root')

                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def _test_required_attributes(self, resources):
        self.assertTrue(len(resources) > 0)
        for host, attributes in resources.iteritems():
            for attribute in self.required_attributes:
                self.assertIn(attribute, attributes)
                self.assertIsNotNone(attributes[attribute])
                self.assertNotEqual(attributes[attribute], '')

            if host == ResourceGenerator._server_node_name:
                expected = self.server_grains
                self.assertIn(host, resources)
                self.assertEqual(resources[host]['hostname'], host)
            else:
                expected = self.mine[host]
                self.assertIn(host, resources)
                self.assertEqual(
                    resources[host]['hostname'],
                    expected['fqdn'])

            self.assertEqual(
                resources[host]['osArch'],
                ResourceGenerator._os_arch(expected['cpuarch']))
            self.assertEqual(
                resources[host]['osFamily'],
                ResourceGenerator._os_family(expected['kernel']))
            self.assertEqual(
                resources[host]['osName'],
                expected['kernel'])
            self.assertEqual(
                resources[host]['osVersion'],
                expected['kernelrelease'])

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
            self.assertEqual(len(attributes['tags']), len(needed))

'''
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
'''


class MockParser:

    ignore_attributes = SaltNodesCommandParser.ignore_attributes
    ignore_servernode = SaltNodesCommandParser.ignore_servernode

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


class MockMinion:

    def __init__(self):
        with open("test_config.yaml", 'r') as stream:
            try:
                self.opts = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)


class MockCaller:

    def __call__(self, *args, **kwargs):
        return self

    def __init__(self):
        self.sminion = MockMinion()
        self.cmd = Mock()

        with open("test_mine.yaml", 'r') as stream:
            try:
                self.cmd.return_value = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)


class TestServerNodeGenerator(TestNodeGenerator):
    include_server_node = True


if __name__ == '__main__':
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    unittest.main(testRunner=runner, buffer=True)
