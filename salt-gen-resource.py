#!/usr/bin/env python2

import salt.client
import salt.utils
import salt.grains
import salt.utils.parsers
import salt.ext.six as six
import salt.syspaths as syspaths
import yaml
import logging
import os

log = logging.getLogger(__name__)

def list_callback(option, opt, value, parser): # pylint: disable=unused-argument
    if ',' in value:
        setattr(parser.values, option.dest, value.replace(' ', '').split(','))
    else:
        setattr(parser.values, option.dest, value.split())


class SaltNodesCommand(
        six.with_metaclass(
            salt.utils.parsers.OptionParserMeta,
            salt.utils.parsers.OptionParser,
            salt.utils.parsers.ExtendedTargetOptionsMixIn,
            salt.utils.parsers.ConfigDirMixIn,
            salt.utils.parsers.LogLevelMixIn)):
    usage = '%prog [options] \'<target>\''
    description = 'Salt Mine node source for Rundeck.'
    epilog = None

    _config_filename_ = 'minion'
    _server_node_name = 'localhost'
    _default_logging_logfile_ = os.path.join(
        syspaths.LOGS_DIR, 'salt-gen-resources.log')
    _setup_mp_logging_listener_ = False

    # Define lists of defaullt grains to add and ignore
    default_grains = ['os', 'os_family', 'osrelease', 'osmajorrelease',
                      'saltversion', 'virtual', 'manufacturer']
    ignore_grains = ['hostname', 'osName', 'osVersion', 'osFamily', 'osArch']

    # Define maps from grain values into expected strings
    os_family_map = {'Linux': 'unix', 'Windows': 'windows'}
    os_arch_map = {'x86_64': 'amd64', 'x86': 'x86'}

    def get_nodes(self):
        resources = {}
        self.parse_args()

        caller = salt.client.Caller(
            os.path.join(self.options.config_dir, self._config_filename_))

        # Call Salt Mine to retrive grains for all nodes
        mine = caller.cmd(
            'mine.get', self.config['tgt'],
            self.options.mine_function,
            expr_form=self.config['selected_target_option'],
            exclude_minion=self.options.include_server_node)

        # Special handling for server node
        if self.options.include_server_node:
            local_grains = salt.loader.grains(caller.opts)
            resources[self._server_node_name] = {
                'hostname':    self._server_node_name,
                'description': 'Rundeck server node',
                'username':    self.options.server_node_user,
                'osName':      local_grains['kernel'],
                'osVersion':   local_grains['kernelrelease'],
                'osFamily':    self.os_family_map[local_grains['kernel']],
                'osArch':      self.os_arch_map[local_grains['osarch']]
            }
            # Create additional attributes from grains
            resources[self._server_node_name].update(
                self.create_attributes(self._server_node_name, local_grains))

        # Map grains into a Rundeck resource dict
        for minion, minion_grains in mine.iteritems():
            # Map required node attributes from grains
            resources[minion] = {
                'hostname':   minion_grains['fqdn'],
                'osName':     minion_grains['kernel'],
                'osVersion':  minion_grains['kernelrelease'],
                'osFamily':   self.os_family_map[minion_grains['kernel']],
                'osArch':     self.os_arch_map[minion_grains['osarch']]
            }
            # Create additional attributes from grains
            resources[minion].update(
                self.create_attributes(minion, minion_grains))
            # Create tags from grains
            resources[minion]['tags'] = self.create_tags(
                minion, minion_grains)

        return resources

    def create_attributes(self, minion, grains):
        attributes = {}
        for grain in self.config['grains']:
            try:
                key, value = self.attribute_from_grain(grain, grains)
                attributes[key] = value
            except TypeError:
                log.warning('Minion \'{0}\' grain \'{1}\' ignored because '
                            'it contains nested items.'
                            .format(minion, grain))
        return attributes

    def attribute_from_grain(self, item, grains):
        key = item.replace(':', '_')
        value = salt.utils.traverse_dict_and_list(
            grains, item, default='',
            delimiter=self.options.delimiter)
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif hasattr(value, '__iter__'):
            raise TypeError
        return (key, value)

    def create_tags(self, minion, grains):
        tags = set()
        for item in self.options.tags:
            try:
                map(tags.add, self.tags_from_grain(item, grains))
            except TypeError:
                log.warning('Minion \'{0}\' grain \'{1}\' ignored because '
                            'it contains nested items.'
                            .format(minion, item))
        return list(tags)

    def tags_from_grain(self, item, grains):
        #key = item.replace(':', '_')
        tags = set()
        value = salt.utils.traverse_dict_and_list(
            grains, item, default='',
            delimiter=self.options.delimiter)
        if isinstance(value, unicode):
            tags.add(value.encode('utf-8'))
        elif isinstance(value, basestring):
            tags.add(value)
        elif isinstance(value, dict):
            raise TypeError
        elif hasattr(value, '__iter__'):
            map(tags.add, value)
        else:
            tags.add(value)
        return tags

    def _mixin_setup(self):
        self.add_option(
            '--mine-function',
            default='grains.items',
            type=str,
            help=('Set the function name for Salt Mine to execute '
                  'to retrive grains. Default value is grains.items '
                  'but this could be different if mine function '
                  'aliases are used.')
        )
        self.add_option(
            '--include-server-node',
            action="store_true",
            help=('Include the Rundeck server node in the output. '
                  'The server node is required for some workflows '
                  'and must be provided by exactly one resource provider.')
        )
        self.add_option(
            '-u', '--server-node-user',
            type=str,
            default='rundeck',
            help=('Specify the user name to use when running jobs on the '
                  'server node. This would typically be the same user that '
                  'the Rundeck service is running as. Default: \'rundeck\'.')
        )
        self.add_option(
            '--grains',
            type=str,
            default=self.default_grains,
            action='callback',
            callback=list_callback,
            help=('Override the default list of grains mapped to '
                  'Rundeck node attributes. The default list is: {0}.'
                  .format(', '.join(self.default_grains)))
        )
        self.add_option(
            '--add-grains',
            type=str,
            action='callback',
            callback=list_callback,
            help=('Add grains to the default list of grains mapped to '
                  'Rundeck node attributes. Multiple grains may be specified '
                  'when separated by a space or comma. '
                  'Grains that are nested in a dictionary can be matched '
                  'by adding a colon for each level that is traversed. '
                  'The following grains may not be added because they '
                  'conflict with Rundeck expected attributes: {0}.'
                  .format(', '.join(self.ignore_grains)))
        )
        self.add_option(
            '--ignore-grains',
            type=str,
            action='callback',
            callback=list_callback,
            help=('Remove grains from the default list of grains mapped to '
                  'Rundeck node attributes. Multiple grains may be specified '
                  'when separated by a space or comma.')
        )
        self.add_option(
            '-t', '--tags',
            type=str,
            action='callback',
            callback=list_callback,
            help=('Create tags from grains')
        )

    def _mixin_after_parsed(self):
        # Extract targeting expression
        try:
            if self.options.list:
                if ',' in self.args[0]:
                    self.config['tgt'] = \
                        self.args[0].replace(' ', '').split(',')
                else:
                    self.config['tgt'] = self.args[0].split()
            else:
                self.config['tgt'] = self.args[0]
        except IndexError:
            self.exit(42, ('\nCannot execute command without '
                           'defining a target.\n\n'))

        # Set default targeting option
        if self.config['selected_target_option'] is None:
            self.config['selected_target_option'] = 'glob'

        # Add additional grains
        self.config['grains'] = self.options.grains
        if self.options.add_grains is not None:
            self.config['grains'] = sorted(list(set(
                self.config['grains']).union(set(self.options.add_grains))))

        # Remove unneeded grains
        if self.options.ignore_grains is not None:
            self.ignore_grains.extend(self.options.ignore_grains)
        self.config['grains'] = [x for x in self.config[
            'grains'] if x not in self.ignore_grains]

    def setup_config(self):
        return salt.config.minion_config(self.get_config_file_path(),  # pylint: disable=no-member
            cache_minion_id=True, ignore_config_errors=False)

if __name__ == '__main__':
    # Print dict as YAML on stdout
    print(yaml.dump(SaltNodesCommand().get_nodes(), default_flow_style=False))


