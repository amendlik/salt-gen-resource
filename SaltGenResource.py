#!/usr/bin/env python2

import salt.client
import salt.utils
import salt.grains
import salt.version as version
import salt.utils.parsers
import salt.ext.six as six
import salt.syspaths as syspaths
import salt.config as config
import salt.utils.args as saltargs
import yaml
import logging
import os
import sys

log = logging.getLogger('salt-gen-resource')


# noinspection PyClassHasNoInit
class SaltNodesCommandParser(
        six.with_metaclass(
            salt.utils.parsers.OptionParserMeta,
            salt.utils.parsers.OptionParser,
            salt.utils.parsers.ConfigDirMixIn,
            salt.utils.parsers.ExtendedTargetOptionsMixIn,
            salt.utils.parsers.LogLevelMixIn)):
    '''
    Argument parser used by SaltGenResource to generate
    Rundeck node definitions.
    '''

    usage = '%prog [options] <target> [<attr>=<value> ...]'
    description = 'Salt Mine node source for Rundeck.'
    epilog = None

    _config_filename_ = 'minion'
    _logfile_config_setting_name_ = 'resource_generator_logfile'
    _logfile_loglevel_config_setting_name_ = 'resource_generator_log_level_logfile'
    _default_logging_logfile_ = os.path.join(syspaths.LOGS_DIR, 'resource-generator')
    _setup_mp_logging_listener_ = False
    _default_logging_level_ = 'warning'

    # Ignore requests to provide reserved attribute names
    ignore_attributes = ['hostname', 'osName', 'osVersion', 'osFamily', 'osArch', 'tags']
    ignore_servernode = ['username', 'description']

    def _mixin_setup(self):
        '''
        Define arguments specific to SaltGenResource
        '''

        self.add_option(
            '-m', '--mine-function',
            default='grains.items',
            type=str,
            help=('Set the function name for Salt Mine to execute '
                  'to retrieve grains. Default value is grains.items '
                  'but this could be different if mine function '
                  'aliases are used.')
        )
        self.add_option(
            '-s', '--include-server-node',
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
            '-a', '--attributes',
            type=str,
            default=[],
            action='callback',
            callback=self.set_callback,
            help=('Create Rundeck node attributes from the values of grains. '
                  'Multiple grains may be specified '
                  'when separated by a space or comma.')
        )
        self.add_option(
            '-t', '--tags',
            type=str,
            default=[],
            action='callback',
            callback=self.set_callback,
            help=('Create Rundeck node tags from the values of grains. '
                  'Multiple grains may be specified '
                  'when separated by a space or comma.')
        )

    def _mixin_after_parsed(self):
        '''
        Validate and process arguments
        '''
        if not os.path.isfile(self.get_config_file_path()):
            log.critical("Configuration file not found")
            sys.exit(-1)

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

        if self.options.log_level:
            self.config['log_level'] = self.options.log_level
        else:
            self.config['log_level'] = self._default_logging_level_

        # Set default targeting option
        if self.config['selected_target_option'] is None:
            self.config['selected_target_option'] = 'glob'

        # Remove conflicting grains
        self.options.attributes = [x for x in self.options.attributes
                                   if x not in self.ignore_attributes]

    def setup_config(self):
        config_opts = config.minion_config(
            self.get_config_file_path(),
            cache_minion_id=True,
            ignore_config_errors=False)

        # Make file based logging work
        if getattr(self.options, self._logfile_config_setting_name_, 'None') is None:

            # Copy the default log file path into the config dict
            if self._logfile_config_setting_name_ not in config_opts:
                config_opts[self._logfile_config_setting_name_] = self._default_logging_logfile_

            # Prepend the root_dir setting to the log file path
            config.prepend_root_dir(config_opts, [self._logfile_config_setting_name_])

            # Copy the altered path back to the options or it will revert to the default
            setattr(self.options, self._logfile_config_setting_name_, config_opts[self._logfile_config_setting_name_])

        else:
            # Copy the provided log file path into the config dict
            if self._logfile_config_setting_name_ not in config_opts:
                config_opts[self._logfile_config_setting_name_] = \
                    getattr(self.options, self._logfile_config_setting_name_, self._default_logging_logfile_)

        return config_opts

    # noinspection PyUnusedLocal
    @staticmethod
    def set_callback(option, opt, value, parser):  # pylint: disable=unused-argument
        '''
        Argument parser callback for handling multi-value sets.
        This callback converts comma-delimited or space-delimited strings
        to list types.
        '''
        if ',' in value:
            setattr(parser.values, option.dest,
                    set(value.replace(' ', '').split(',')))
        else:
            setattr(parser.values, option.dest, set(value.split()))


class ResourceGenerator(object):
    '''
    Provide a dictionary of node definitions.
    When written to stdout in YAML format, this dictionary is consumable
    by Rundeck.
    '''

    # Define maps from grain values into expected strings
    _os_family_map = {'Linux': 'unix', 'Windows': 'windows'}
    _os_arch_map = {'x86_64': 'amd64', 'AMD64': 'amd64'}
    _server_node_name = 'localhost'
    _mine_func = 'mine.get'

    def __init__(self, args=None):
        '''
        Parse command arguments
        '''
        # Call the configuration parser
        parser = SaltNodesCommandParser()
        parser.parse_args(args)

        # Removing 'conf_file' prevents the file from being re-read when rendering grains
        parser.config.pop('conf_file', None)

        # Parse the static attribute definitions
        self.static = saltargs.parse_input(parser.args, False)[1]

        # Setup file logging
        parser.setup_logfile_logger()

        # Create local references to the parser data
        self.config = parser.config
        self.options = parser.options

    def run(self):
        '''
        The main entry point for SaltGenResource. This method calls the Salt Mine
        and converts the returned data into a dictionary that conforms to the Rundeck
        specification for an external resource generator.

        The return is a Python dictionary. The caller is responsible for converting
        the dictionary into YAML for consumption by Rundeck.
        '''
        resources = {}

        # Create a Salt Caller object
        caller = salt.client.Caller(c_path=None, mopts=self.config)

        # Account for an API change in Salt Nitrogen (2017.7)
        kwargs = {'exclude_minion': self.options.include_server_node}
        if version.__saltstack_version__ >= version.SaltStackVersion.from_name('Nitrogen'):
            kwargs['tgt_type'] = self.config['selected_target_option']
        else:
            kwargs['expr_form'] = self.config['selected_target_option']

        # Call Salt Mine to retrieve grains for all nodes
        log.debug(
            'Calling {0} with target: \'{1}\' type: \'{2}\''
            .format(self._mine_func, self.config['tgt'], self.config['selected_target_option']))
        mine = caller.cmd(
            self._mine_func,
            self.config['tgt'],
            self.options.mine_function,
            **kwargs)
        log.debug(
            'Salt Mine function \'{0}\' returned {1} minion{2}'
            .format(self._mine_func, len(mine), '' if len(mine) == 1 else 's'))

        # Special handling for server node
        if self.options.include_server_node is True:
            # Map required node attributes from grains
            local_grains = caller.sminion.opts['grains']
            resources[self._server_node_name] = {
                'hostname':    self._server_node_name,
                'description': 'Rundeck server node',
                'username':    self.options.server_node_user,
                'osName':      local_grains['kernel'],
                'osVersion':   local_grains['kernelrelease'],
                'osFamily':    self._os_family(local_grains['kernel']),
                'osArch':      self._os_arch(local_grains['cpuarch'])
            }
            # Create additional attributes from grains
            resources[self._server_node_name].update(
                self._create_attributes(self._server_node_name, local_grains))

            # Create static attributes
            resources[self._server_node_name].update({
                k: v for k, v in self.static.iteritems()
                if k not in SaltNodesCommandParser.ignore_attributes + SaltNodesCommandParser.ignore_servernode})

            # Create tags from grains
            tags = self._create_tags(self._server_node_name, local_grains)
            if len(tags) > 0:
                resources[self._server_node_name]['tags'] = tags

        # Map grains into a Rundeck resource dict
        for minion, minion_grains in mine.iteritems():
            # Map required node attributes from grains
            resources[minion] = {
                'hostname':   minion_grains['fqdn'],
                'osName':     minion_grains['kernel'],
                'osVersion':  minion_grains['kernelrelease'],
                'osFamily':   self._os_family(minion_grains['kernel']),
                'osArch':     self._os_arch(minion_grains['cpuarch'])
            }
            # Create additional attributes from grains
            resources[minion].update(
                self._create_attributes(minion, minion_grains))
            # Create static attributes
            resources[minion].update({
                k: v for k, v in self.static.iteritems()
                if k not in SaltNodesCommandParser.ignore_attributes})
            # Create tags from grains
            tags = self._create_tags(minion, minion_grains)
            if len(tags) > 0:
                resources[minion]['tags'] = tags

        if not resources:
            log.warning('No resources returned.')

        return resources

    def _create_attributes(self, minion, grains):
        '''
        Loop over requested attributes and request a value for each
        '''
        attributes = {}
        for item in self.options.attributes:
            try:
                key, value = self._attribute_from_grain(item, grains)
                if value:
                    log.debug(
                        'Adding attribute for minion: \'{0}\' '
                        'grain: \'{1}\', attribute: \'{2}\', value: \'{3}\''
                        .format(minion, item, key, value))
                    attributes[key] = value
                else:
                    log.warning(
                        'Requested grain \'{0}\' is not available '
                        'on minion: {1}'.format(item, minion))
            except TypeError:
                log.warning('Minion \'{0}\' grain \'{1}\' ignored '
                            'because it contains nested items.'
                            .format(minion, item))
        return attributes

    def _attribute_from_grain(self, item, grains):
        '''
        Provide the value for a single attribute from a grain
        '''
        key = item.replace(':', '_')
        value = salt.utils.traverse_dict_and_list(
            grains, item, default='',
            delimiter=self.options.delimiter)
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif hasattr(value, '__iter__'):
            raise TypeError
        return key, value

    def _create_tags(self, minion, grains):
        '''
        Loop over requested tags and request a value for each
        '''
        tags = set()
        for item in self.options.tags:
            try:
                new_tags = self._tags_from_grain(item, grains)
                if new_tags:
                    log.debug(
                        'Adding tag for minion: \'{0}\' '
                        'grain: \'{1}\', tag(s): \'{2}\''
                        .format(minion, item, ','.join(str(x) for x in new_tags)))
                    map(tags.add, new_tags)
                else:
                    log.warning(
                        'Requested grain \'{0}\' is not available '
                        'on minion: {1}'.format(item, minion))
            except TypeError:
                log.warning('Minion \'{0}\' grain \'{1}\' ignored '
                            'because it contains nested items.'
                            .format(minion, item))
        return list(tags)

    def _tags_from_grain(self, item, grains):
        '''
        Define a single tag from a grain value
        '''
        tags = set()
        value = salt.utils.traverse_dict_and_list(
            grains, item, default=None, delimiter=self.options.delimiter)
        if value is None:
            pass
        elif not value:
            pass
        elif isinstance(value, unicode):
            tags.add(value.encode('utf-8'))
        elif isinstance(value, str):
            tags.add(value)
        elif isinstance(value, dict):
            raise TypeError
        elif hasattr(value, '__iter__'):
            for nesteditem in value:
                if hasattr(nesteditem, '__iter__'):
                    pass
                elif isinstance(nesteditem, unicode):
                    tags.add(nesteditem.encode('utf-8'))
                else:
                    tags.add(nesteditem)
        else:
            tags.add(value)
        return tags

    @classmethod
    def _os_family(cls, value):
        '''
        Map the os_family used by Salt to one used by Rundeck
        '''
        if value in cls._os_family_map:
            return cls._os_family_map[value]
        else:
            return value

    @classmethod
    def _os_arch(cls, value):
        '''
        Map the os_arch used by Salt to one used by Rundeck
        '''
        if value in cls._os_arch_map:
            return cls._os_arch_map[value]
        else:
            return value


if __name__ == '__main__':
    # Print dict as YAML on stdout
    print(yaml.safe_dump(ResourceGenerator().run(), default_flow_style=False))
