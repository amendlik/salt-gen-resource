# -*- coding: utf-8 -*-

import sys
import os.path as path
import argparse
from unittest import TestCase, TextTestRunner, main

import six
import yaml
import salt.version as version
from SaltGenResource import ResourceGenerator, SaltNodesCommandParser

if six.PY2:
    from mock import patch, Mock
else:
    from unittest.mock import patch, Mock

# pylint: disable=protected-access,missing-function-docstring
class TestMapping(TestCase):
    def test_os_family_map1(self):
        os_family = ResourceGenerator._os_family("Linux")
        self.assertEqual(os_family, "unix")

    def test_os_family_map2(self):
        os_family = ResourceGenerator._os_family("unknown")
        self.assertEqual(os_family, "unknown")

    def test_os_arch_map1(self):
        os_arch = ResourceGenerator._os_arch("x86_64")
        self.assertEqual(os_arch, "amd64")

    def test_os_arch_map2(self):
        os_arch = ResourceGenerator._os_arch("AMD64")
        self.assertEqual(os_arch, "amd64")

    def test_os_arch_map3(self):
        os_arch = ResourceGenerator._os_arch("unknown")
        self.assertEqual(os_arch, "unknown")


class TestNodeGenerator(TestCase):

    include_server_node = False
    required_attributes = ["hostname", "osArch", "osFamily", "osName", "osVersion"]
    default_args = ["mine.get", "*", "grains.items"]
    default_kwargs = {}

    @classmethod
    def setUpClass(cls):

        # Set expected kwargs for minion call
        if version.__saltstack_version__ >= version.SaltStackVersion.from_name(
            "Nitrogen"
        ):
            cls.default_kwargs = {"tgt_type": "glob"}
        else:
            cls.default_kwargs = {"expr_form": "glob"}

        cls.mine = load_test_data("mine.yaml")
        cls.server_grains = load_test_data("config.yaml")["grains"]

    def test_single_attribute(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:

                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.attributes = ["os"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_multiple_attributes(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:

                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.attributes = ["os", "os_family"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_list_attribute(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:

                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.attributes = ["colors"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

                for _, resource in six.iteritems(resources):
                    self.assertEqual(resource["colors"], "red")

    def test_nested_list_attribute(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:

                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.attributes = ["instruments"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

                for _, resource in six.iteritems(resources):
                    self.assertEqual(resource["instruments"], "oboe")

    def test_falsy_attribute(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:

                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.attributes = ["virtual"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_attributes(resources, parser.options.attributes)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

                for _, resource in six.iteritems(resources):
                    self.assertIs(resource["virtual"], False)

    def test_single_tag(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.tags = ["os"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_tags(resources, parser.options.tags)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_multiple_tags(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.tags = ["os", "kernelrelease"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_tags(resources, parser.options.tags)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_list_tag(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.options.tags = ["colors"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

                for _, attributes in six.iteritems(resources):
                    self.assertTrue(len(attributes["tags"]) > 1)

    def test_static_attributes(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.args = ["color=yellow", "pattern='polka dot'"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_attributes(resources, ["color", "pattern"])

                for host, _ in six.iteritems(resources):
                    self.assertEqual(resources[host]["color"], "yellow")
                    self.assertEqual(resources[host]["pattern"], "polka dot")

                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_static_username(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()) as caller:
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.args = ["username=root"]
                resources = ResourceGenerator().as_dict()

                self._test_required_attributes(resources)
                self._test_attributes(resources, ["username"])

                for host, _ in six.iteritems(resources):
                    if host == ResourceGenerator._server_node_name:
                        self.assertEqual(
                            resources[host]["username"], parser.options.server_node_user
                        )
                    else:
                        self.assertEqual(resources[host]["username"], "root")

                caller.cmd.assert_called_once_with(*self.default_args, **call_kwargs)

    def test_unicode(self):
        with patch("SaltGenResource.SaltNodesCommandParser", MockParser()) as parser:
            with patch("salt.client.Caller", MockCaller()):
                call_kwargs = dict.copy(self.default_kwargs)
                parser.options.include_server_node = self.include_server_node
                call_kwargs["exclude_minion"] = self.include_server_node

                parser.args = [u"color=⋐⊮⊰⟒"]
                output = ResourceGenerator().as_yaml()
                self.assertNotIn("!!python/unicode", output)

    def _test_required_attributes(self, resources):
        self.assertTrue(len(resources) > 0)
        for host, attributes in six.iteritems(resources):
            for attribute in self.required_attributes:
                self.assertIn(attribute, attributes)
                self.assertIsNotNone(attributes[attribute])
                self.assertNotEqual(attributes[attribute], "")

            if host == ResourceGenerator._server_node_name:
                expected = self.server_grains
                self.assertIn(host, resources)
                self.assertEqual(resources[host]["hostname"], host)
            else:
                expected = self.mine[host]
                self.assertIn(host, resources)
                self.assertEqual(resources[host]["hostname"], expected["fqdn"])

            self.assertEqual(
                resources[host]["osArch"],
                ResourceGenerator._os_arch(expected["cpuarch"]),
            )
            self.assertEqual(
                resources[host]["osFamily"],
                ResourceGenerator._os_family(expected["kernel"]),
            )
            self.assertEqual(resources[host]["osName"], expected["kernel"])
            self.assertEqual(resources[host]["osVersion"], expected["kernelrelease"])

    def _test_attributes(self, resources, needed):
        self.assertTrue(len(resources) > 0)
        self.assertNotIn("!!", ResourceGenerator._dump_yaml(resources))
        for _, attributes in six.iteritems(resources):
            for attribute in needed:
                self.assertIn(attribute, attributes)
                self.assertIsNotNone(attributes[attribute])
                self.assertNotEqual(attributes[attribute], "")

    def _test_tags(self, resources, needed):
        self.assertTrue(len(resources) > 0)
        self.assertNotIn("!!", ResourceGenerator._dump_yaml(resources))
        for _, attributes in six.iteritems(resources):
            self.assertIn("tags", attributes)
            self.assertIsNotNone(attributes["tags"])
            self.assertEqual(len(attributes["tags"]), len(needed))


class TestServerNodeGenerator(TestNodeGenerator):
    """
    This test case runs all the same tests as TestNodeGenerator,
    but as if the --include-server-node option was passed.
    """

    include_server_node = True


class MockParser:

    ignore_attributes = SaltNodesCommandParser.ignore_attributes
    ignore_servernode = SaltNodesCommandParser.ignore_servernode

    def __call__(self, *args, **kwargs):
        return self

    def __init__(self):
        self.config = load_test_data("config.yaml")
        self.options = argparse.Namespace(**load_test_data("options.yaml"))
        self.args = ""

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
    def parse_args(self, *args, **kwargs):
        return self.options, self.args

    def setup_logfile_logger(self):
        pass


class MockMinion:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.opts = load_test_data("config.yaml")


class MockCaller:  # pylint: disable=too-few-public-methods
    def __call__(self, *args, **kwargs):
        return self

    def __init__(self):
        self.sminion = MockMinion()
        self.cmd = Mock(return_value=load_test_data("mine.yaml"))


def load_test_data(dataset):
    filename = path.join(path.dirname(path.abspath(__file__)), "tests", "data", dataset)
    with open(filename, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


if __name__ == "__main__":
    main(testRunner=TextTestRunner(stream=sys.stdout, verbosity=2), buffer=True)
