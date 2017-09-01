# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # Define a VM to test Salt 2016.11
  config.vm.define "carbon" do |carbon|
    carbon.vm.box = "bento/ubuntu-16.04"
    carbon.vm.box_check_update = false

    carbon.vm.provision :salt do |salt|
      salt.install_master = true
      salt.install_type = "git"
      salt.install_args = "v2016.11.6"
      salt.minion_config = "config/minion"
      salt.master_config = "config/master"
      salt.verbose = false
    end

    carbon.vm.provision :shell do |test|
      test.name = "run tests"
      test.inline = <<-SHELL
        apt-get -y install python-mock
        salt-call -l quiet mine.update True
        python2 "/vagrant/test.py"
      SHELL
    end

  end

  # Define a VM to test Salt 2017.7
  config.vm.define "nitrogen" do |nitrogen|
    nitrogen.vm.box = "bento/ubuntu-16.04"
    nitrogen.vm.box_check_update = false

    nitrogen.vm.provision :salt do |salt|
      salt.install_master = true
      salt.install_type = "git"
      salt.install_args = "v2017.7.0"
      salt.minion_config = "config/minion"
      salt.master_config = "config/master"
      salt.verbose = false
    end

    nitrogen.vm.provision :shell do |test|
      test.name = "run tests"
      test.inline = <<-SHELL
        apt-get -y install python-mock
        salt-call -l quiet mine.update True
        python2 "/vagrant/test.py"
      SHELL
    end
  end

end
