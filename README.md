## Synopsis

A script that uses Mine function of SaltStack to populate nodes
in Rundeck. In addition to providing nodes, any Salt Grain can be
added as a node attribute or tag.

This script requires that a Salt Minion be running on the Rundeck server.

## Installation

### Resource Model Provider Script

The only file required from this repository is [SaltGenResource.py](SaltGenResource.py). Copy it to the Rundeck server, in the location where Rundeck configuration scripts are stored (e.g. `/opt/rundeck/scripts`). As an alternative, this entire repository can be cloned to make future updates easy.

### Sudo policy

Because the script is essentially running the Salt Minion, it must be run as root. Add the following snippet to the sudoers policy to permit Rundeck to run it. Change the path to match the installed location of the script.
```
Cmnd_Alias SALT_GEN_RESOURCE = /opt/rundeck/scripts/salt-gen-resource/SaltGenResource.py
rundeck ALL=(root) NOPASSWD: SALT_GEN_RESOURCE
Defaults!SALT_GEN_RESOURCE !requiretty
```

### Project configuration

The project configuration can be edited through the web UI, or by editing the file on disk. The web UI is recommended for several reasons:

1. It works whether using filesystem-backed projects or database-backed projects. If using database-backed projects, there is no file on disk to edit.
2. It knows the location of the file. Rundeck can be installed in a variety of configurations, and all of them place configuration files in different places.
3. It handles string escaping. If editing the file directly, the escaping rules of Java `.properties` files must be followed.

Edit the Rundeck project configuration to include a new node source script. Change the `file` parameter to match the installed location of `SaltGenResource.py`.
```
resources.source.2.type=script
resources.source.2.config.format=resourceyaml
resources.source.2.config.interpreter=sudo
resources.source.2.config.file=/opt/rundeck/scripts/SaltGenResource.py
resources.source.2.config.args=-G virtual:kvm
```
**Note:** Be careful about deleting an existing node source from the configuration file. One of those sources usually provides the 'server node', which is necessary for certain Rundeck workflows. The server node is **not** provided by `SaltGenResource.py` by default. 
Add additional node sources as necessary, by using another number in the properties (resources.source._#_.config), or configure `SaltGenResource.py` to provide the server node with `--include-server-node`.

### Salt Mine
This resource model provider depends on the Salt Mine having access to the `grains.items` function on all minions. To enable this, the `mine_functions` options need to be applied to all Minions, either through the Minion configuration files, or using Pillar. The simplest `mine_functions` that would work is this:
```
mine_functions:
  grains.items: []
```
It is also possible to create an alias to the `grains.items` function using this syntax:
```
mine_functions:
  allgrains:
    mine_function: grains.items
```
When using a function alias (`allgrains`, in the example above), be sure to supply the name with `--mine-function`.

**Note:** Salt Mine values are refreshed according to the interval defined by the `mine_interval` option (60 minutes, by default). When the mine configuration is created or changed, the values will not be updated until the next interval elapses. To force an immediate update, use the [`mine.update`](https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.mine.html#salt.modules.mine.update) function.

See the Salt Mine [online documentation](https://docs.saltstack.com/en/latest/topics/mine/#the-salt-mine) for more detail.

## Configuration

For usage instructions, run `SaltGenResource.py --help`:
```
Usage: SaltGenResource.py [options] <target> [<attr>=<value> ...]

Salt Mine node source for Rundeck.

Options:
  --version             show program's version number and exit
  -V, --versions-report
                        Show program's dependencies version number and exit.
  -h, --help            show this help message and exit
  -c CONFIG_DIR, --config-dir=CONFIG_DIR
                        Pass in an alternative configuration directory.
                        Default: '/etc/salt'.
  -m MINE_FUNCTION, --mine-function=MINE_FUNCTION
                        Set the function name for Salt Mine to execute to
                        retrieve grains. Default value is grains.items but
                        this could be different if mine function aliases are
                        used.
  -s, --include-server-node
                        Include the Rundeck server node in the output. The
                        server node is required for some workflows and must be
                        provided by exactly one resource provider.
  -u SERVER_NODE_USER, --server-node-user=SERVER_NODE_USER
                        Specify the user name to use when running jobs on the
                        server node. This would typically be the same user
                        that the Rundeck service is running as. Default:
                        'rundeck'.
  -a ATTRIBUTES, --attributes=ATTRIBUTES
                        Create Rundeck node attributes from the values of
                        grains. Multiple grains may be specified when
                        separated by a space or comma.
  -t TAGS, --tags=TAGS  Create Rundeck node tags from the values of grains.
                        Multiple grains may be specified when separated by a
                        space or comma.

  Logging Options:
    Logging options which override any settings defined on the
    configuration files.

    -l LOG_LEVEL, --log-level=LOG_LEVEL
                        Console logging log level. One of 'all', 'garbage',
                        'trace', 'debug', 'profile', 'info', 'warning',
                        'error', 'critical', 'quiet'. Default: 'warning'.
    --log-file=RESOURCE_GENERATOR_LOGFILE
                        Log file path. Default: '/var/log/salt/resource-
                        generator'.
    --log-file-level=RESOURCE_GENERATOR_LOG_LEVEL_LOGFILE
                        Logfile logging log level. One of 'all', 'garbage',
                        'trace', 'debug', 'profile', 'info', 'warning',
                        'error', 'critical', 'quiet'. Default: 'warning'.

  Target Options:
    Target selection options.

    -E, --pcre          Instead of using shell globs to evaluate the target
                        servers, use pcre regular expressions.
    -L, --list          Instead of using shell globs to evaluate the target
                        servers, take a comma or space delimited list of
                        servers.
    -G, --grain         Instead of using shell globs to evaluate the target
                        use a grain value to identify targets, the syntax for
                        the target is the grain key followed by a
                        globexpression: "os:Arch*".
    -P, --grain-pcre    Instead of using shell globs to evaluate the target
                        use a grain value to identify targets, the syntax for
                        the target is the grain key followed by a pcre regular
                        expression: "os:Arch.*".
    -N, --nodegroup     Instead of using shell globs to evaluate the target
                        use one of the predefined nodegroups to identify a
                        list of targets.
    -R, --range         Instead of using shell globs to evaluate the target
                        use a range expression to identify targets. Range
                        expressions look like %cluster.
    -C, --compound      The compound target option allows for multiple target
                        types to be evaluated, allowing for greater
                        granularity in target matching. The compound target is
                        space delimited, targets other than globs are preceded
                        with an identifier matching the specific targets
                        argument type: salt 'G@os:RedHat and webser* or
                        E@database.*'.
    -I, --pillar        Instead of using shell globs to evaluate the target
                        use a pillar value to identify targets, the syntax for
                        the target is the pillar key followed by a glob
                        expression: "role:production*".
    -J, --pillar-pcre   Instead of using shell globs to evaluate the target
                        use a pillar value to identify targets, the syntax for
                        the target is the pillar key followed by a pcre
                        regular expression: "role:prod.*".
    -S, --ipcidr        Match based on Subnet (CIDR notation) or IP address.

  Additional Target Options:
    Additional options for minion targeting.

    --delimiter=DELIMITER
                        Change the default delimiter for matching in multi-
                        level data structures. Default: ':'.
```
Command line options will be provided to Rundeck using the `resources.source.#.config.args` line in the project configuration. 

### Targeting
The only required argument is a targeting expression. This has the effect of limiting which Salt Minions are presented as Rundeck nodes. This script supports the [same targeting methods and syntax](https://docs.saltstack.com/en/latest/topics/targeting/) as the `salt` command.

**Note:** Rundeck will not pass this command through any shell command interpreters, so **do not** add shell escape characters. For example, to target all minions with the `*` glob expression, use this configuration:
```
resources.source.2.config.args=*
```

### Node Attributes
Node attributes can be added by including the `--attributes` argument. This can be used to add any grain value as a node attribute in Rundeck. Note that the value of the grain must not be a dictionary. If the requested grain is a list, the first element of the list will be used as the attribute value. Nested grains can be specified using `:` as a delimiter, such as `--attributes locale_info:defaultlanguage`. The delimiter can be changed using the `--delimiter` command-line argument.
Requesting an attribute for a grain that does not exist will emit a warning and continue without adding the attribute.

### Node Tags
Node tags can be added by including the `--tags` argument. This is particularly useful when the value of a grain is a list, because a tag will be created for each item in the list. A common example of this is a `roles` grain. Tags will also be created for single value grains. For example, `--tags=init` will tag every Linux system with `systemd`, `upstart`, etc.
Requesting a tag for a grain that does not exist will emit a warning and continue without adding the tag.

### Mine Function
By default, this script depends on Salt Mine having access to `grains.items` on every minion. If an alias is configured for that function, specify it using the `--mine-function` option.

### Static Attributes
Additional attributes that are not provided by a grain can be specified by including key value pairs on the command line, after the targeting expression. These static attributes will be added to all generated node resources. For example:
```
SaltGenResource.py '*' username='rduser'
```

### Configuration File
SaltGenResource loads its configuration from the standard Minion configuration files, normally located at `/etc/salt/minion` and `/etc/salt/minion.d/*.conf` on Linux. This path is different on other operating systems, and can be overridden using the `-c` or `--config-dir` command-line options.
In addition to the normal, [documented](https://docs.saltstack.com/en/latest/ref/configuration/minion.html) configuration, there are two additional options to control file-based logging:

| Option | Default Value | Description |
|--------|---------------|-------------|
| `resource_generator_logfile` | `/var/log/salt/resource-generator` | Log file path. This path will be prepended with `root_dir` at runtime. |
| `resource_generator_log_level_logfile` | `warning` | Logfile logging log level. One of `all`, `garbage`, `trace`, `debug`, `profile`, `info`, `warning`, `error`, `critical`, `quiet`. |

### Example
A more complete example might look like this:
```
resources.source.2.type=script
resources.source.2.config.format=resourceyaml
resources.source.2.config.interpreter=sudo
resources.source.2.config.file=/opt/rundeck/scripts/SaltGenResource.py
resources.source.2.config.args=--mine-function allgrains --attributes domain,selinux:enabled --tags roles,init -S 10.0.1.0/24 username=rduser
```
1. Use the mine function alias `allgrains` instead of `grains.items`.
2. Create node attributes in Rundeck for grains `domain` and `selinux:enabled`.
3. Create tags for every element of the `roles` grain, and a tag for the value of the `init` grain.
4. Only create Rundeck nodes for those minions on the 10.0.1.0/24 subnet.
5. Add the `username` attribute to every node with a value of `rduser`.

### Validation
This script can be run at any time from a shell. This can be useful when testing command line arguments. The result should be a YAML document sent to stdout, formatted according the Rundeck [resource-yaml specification](http://rundeck.org/docs/man5/resource-yaml.html). For example:
```
app01:
  hostname: app01.example.org
  manufacturer: OpenStack Foundation
  os: CentOS
  osArch: amd64
  osFamily: unix
  osName: Linux
  osVersion: 3.10.0-327.36.2.el7.x86_64
  os_family: RedHat
  osmajorrelease: '7'
  osrelease: 7.2.1511
  saltversion: 2016.3.3
  tags:
    - kvm
app02:
  hostname: app02.example.org
  manufacturer: OpenStack Foundation
  os: CentOS
  osArch: amd64
  osFamily: unix
  osName: Linux
  osVersion: 3.10.0-327.36.2.el7.x86_64
  os_family: RedHat
  osmajorrelease: '7'
  osrelease: 7.2.1511
  saltversion: 2016.3.3
  tags:
    - kvm
db01:
  hostname: db01.example.org
  manufacturer: OpenStack Foundation
  os: CentOS
  osArch: amd64
  osFamily: unix
  osName: Linux
  osVersion: 3.10.0-327.36.2.el7.x86_64
  os_family: RedHat
  osmajorrelease: '7'
  osrelease: 7.2.1511
  saltversion: 2016.3.3
  tags:
    - kvm
db02:
  hostname: db02.example.org
  manufacturer: OpenStack Foundation
  os: CentOS
  osArch: amd64
  osFamily: unix
  osName: Linux
  osVersion: 3.10.0-327.36.2.el7.x86_64
  os_family: RedHat
  osmajorrelease: '7'
  osrelease: 7.2.1511
  saltversion: 2016.3.3
  tags:
    - kvm
```

## License

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.