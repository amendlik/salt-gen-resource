## Synopsis

A script that uses Mine function of SaltStack to populate nodes
in Rundeck. In addition to providing nodes, any Salt Grain can be
added as a node attribute.

You must have a Salt Minion running on the Rundeck server.

## Installation

### Resource Model Provider Script

The only file required from this repository is [salt-nodes.py](salt-nodes.py). Copy it to your Rundeck server, in the location where your keep your Rundeck configuration scripts (e.g. `/opt/rundeck/scripts`). You can also clone this entire repository to your scripts location to make future updates easy.

### Sudo policy

Because the script is essentially running the Salt Minion, it must be run as root. Add this to your sudoers policy to permit Rundeck to run it:
```
rundeck ALL=(root) NOPASSWD: /opt/rundeck/scripts/salt-nodes.py
Defaults!/opt/rundeck/scripts/salt-nodes.py !requiretty
```

### Project configuration

The project configuration can be edited through the web UI, or by editing the file on disk. I recommend using the UI for several reasons:

1. The UI works whether you are using filesystem-backed projects or database-backed projects. If you are using database-backed projects, there is no file on disk to edit.
2. The UI knows the location of the file. Rundeck can be installed in a variety of configurations, and all of them place configuration files in different places.
3. The UI handles string escaping. If you insist on editing the file directly, you must follow the escaping rules of Java .props files.

Edit your Rundeck project configuration to include a new node source script. Change the `file` parameter to match the location where you installed `salt-nodes.py`.
```
resources.source.2.config.args=-G virtual:kvm
resources.source.2.config.file=/opt/rundeck/scripts/salt-nodes.py
resources.source.2.config.format=resourceyaml
resources.source.2.config.interpreter=sudo
resources.source.2.type=script
```
**Note:** Do not delete the existing node source in your configuration file. That file usually contains the 'server node', which is necessary for certiain Rundeck workflows. The server node is **not** implemented by `salt-nodes.py`. Instead, configure this script as an additional node source.

### Salt Mine
This resource model provider depends on the Salt Mine having access to the `grains.items` function on all minions. To enable this, the `mine_functions` options need to be applied to all Minions, either through the Minion configuration files, or using Pillar. The simplist `mine_functions` that would work is this:
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

See the [online documentation](https://docs.saltstack.com/en/latest/topics/mine/#the-salt-mine) for more detail.

## Configuration

Running `salt-nodes.py --help` will tell you just about everything you need to know:
```
Usage: salt-nodes.py [options] '<target>'

Salt Mine node source for Rundeck.

Options:
  --version             show program's version number and exit
  --versions-report     Show program's dependencies version number and exit.
  -h, --help            show this help message and exit
  --mine-function=MINE_FUNCTION
                        Set the function name for Salt Mine to execute to
                        retrive grains. Default value is grains.items but this
                        could be different if mine function aliases are used.
  --grains=GRAINS       Override the default list of grains mapped to Rundeck
                        node tags. The default list is: os, os_family,
                        osrelease, osmajorrelease, saltversion, virtual,
                        manufacturer.
  --add-grains=ADD_GRAINS
                        Add grains to the default list of grains mapped to
                        Rundeck node tags. Multiple grains may be specified
                        when separated by a space or comma. Grains that are
                        nested in a dictionary can be matched by adding a
                        colon for each level that is traversed. The following
                        grains may not be added because they conflict with
                        Rundeck expected attributes: hostname, osName,
                        osVersion, osFamily, osArch.
  --ignore-grains=IGNORE_GRAINS
                        Remove grains from the default list of grains mapped
                        to Rundeck node tags. Multiple grains may be specified
                        when separated by a space or comma.

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
### Grains
By default, this script will map these grains to Rundeck node attributes: `os`, `os_family`, `osrelease`, `osmajorrelease`, `saltversion`, `virtual`, and `manufacturer`. Use the `--grains`, `--add-grains`, and `--ignore-grains` options to gather different grains.
### Mine function
By default, this script depends on Salt Mine having access to `grains.items` on every minion. If you have an alias in place for that function, specify it using the `--mine-function` option.
### Example
A more complete example might look like this:
```
resources.source.2.config.args=--mine-function allgrains --add-grains domain,selinux:enabled --ignore-grains manufacturer -S 10.0.1.0/24
```
1. Use the mine function alias `allgrains` instead of `grains.items`.
2. Create node tags in Rundeck for grains `domain` and `selinux:enabled`.
3. Do not create node tags in Rundeck for the `manufacturer` grain.
4. Only create Rundeck nodes for those minions on the 10.0.1.0/24 subnet.

### Validation

This script can be run at any time from a shell. This can be useful when testing options. The result should be a YAML document sent to stdout, formatted according the Rundeck [resource-yaml specification](http://rundeck.org/docs/man5/resource-yaml.html). For example:
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
  virtual: kvm
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
  virtual: kvm
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
  virtual: kvm
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
  virtual: kvm
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