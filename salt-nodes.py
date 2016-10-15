#!/bin/python2

import salt.client
import salt.utils
import salt.utils.parsers
import salt.ext.six as six
import yaml


def list_callback(option, opt, value, parser):
    if ',' in value:
        setattr(parser.values, option.dest, value.replace(' ', '').split(','))
    else:
        setattr(parser.values, option.dest, value.split())


class SaltNodesCommand(six.with_metaclass(
                       salt.utils.parsers.OptionParserMeta,
                       salt.utils.parsers.OptionParser,
                       salt.utils.parsers.ExtendedTargetOptionsMixIn)
                       ):
    usage = '%prog [options] \'<target>\''
    description = 'Salt Mine node source for Rundeck.'
    epilog = None
    config = {}
    default_grains = ['os', 'os_family', 'osrelease', 'osmajorrelease',
                      'saltversion', 'virtual', 'manufacturer']
    ignore_grains = ['hostname', 'osName', 'osVersion', 'osFamily', 'osArch']

    def run(self):
        options, args = self.parse_args()

        # Map grain values into expected strings
        osFamily = {'Linux': 'unix', 'Windows': 'windows'}
        osArch = {'x86_64': 'amd64', 'x86': 'x86'}

        # Call Salt Mine to retrive grains for all nodes
        mine = salt.client.Caller().cmd(
            'mine.get', self.config['tgt'],
            self.options.mine_function,
            expr_form=self.config['selected_target_option'])

        # Map grains into a Rundeck resource dict
        resources = {}
        for minion, minion_grains in mine.iteritems():
            # Map required node attributes from grains
            resources[minion] = {
                'hostname':   minion_grains['fqdn'],
                'osName':     minion_grains['kernel'],
                'osVersion':  minion_grains['kernelrelease'],
                'osFamily':   osFamily[minion_grains['kernel']],
                'osArch':     osArch[minion_grains['osarch']]
            }
            # Create optional tags from grains
            map(lambda x: resources[minion].update(
                {x.replace(':', '_'): salt.utils.traverse_dict_and_list(
                    minion_grains, x, default='', delimiter=options.delimiter)
                }), self.config['grains'])

        # Print dict as YAML on stdout
        print(yaml.dump(resources, default_flow_style=False))

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
            '--grains',
            type=str,
            default=self.default_grains,
            action='callback',
            callback=list_callback,
            help=('Override the default list of grains mapped to '
                  'Rundeck node tags. The default list is: {0}.'
                  .format(', '.join(self.default_grains)))
        )
        self.add_option(
            '--add-grains',
            type=str,
            action='callback',
            callback=list_callback,
            help=('Add grains to the default list of grains mapped to '
                  'Rundeck node tags. Multiple grains may be specified '
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
                  'Rundeck node tags. Multiple grains may be specified '
                  'when separated by a space or comma.')
        )


    def _mixin_after_parsed(self):

        # Extract targeting expression
        if self.options.list:
            try:
                if ',' in self.args[0]:
                    self.config['tgt'] = \
                        self.args[0].replace(' ', '').split(',')
                else:
                    self.config['tgt'] = self.args[0].split()
            except IndexError:
                self.exit(
                    42,
                    '\nCannot execute command without defining a target.\n\n')
        else:
            try:
                self.config['tgt'] = self.args[0]
            except IndexError:
                self.exit(
                    42,
                    '\nCannot execute command without defining a target.\n\n')

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

SaltNodesCommand().run()
