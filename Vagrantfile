# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "bento/ubuntu-16.04"
  config.vm.box_check_update = false

  config.vm.provision :salt do |salt|
    salt.install_master = true
    salt.install_type = "stable"
    salt.minion_config = "config/minion"
    salt.master_config = "config/master"
    salt.verbose = false
  end

  config.vm.provision :shell do |test|
    test.name = "run tests"
    test.inline = <<-SHELL
      salt-call -l quiet mine.update True
      python2 "/vagrant/test.py"
    SHELL
  end

end
