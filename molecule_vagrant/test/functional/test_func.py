#  Copyright (c) 2015-2018 Cisco Systems, Inc.
#  Copyright (c) 2018 Red Hat, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import pytest
import os
import sh
import distro
from shutil import which
import vagrant

from molecule import util
from molecule import logger
from molecule.test.conftest import run_command, change_dir_to

LOG = logger.get_logger(__name__)


# @pytest.mark.xfail(reason="need to fix template path")
def test_command_init_scenario(temp_dir):
    role_directory = os.path.join(temp_dir.strpath, "test-init")
    options = {}
    cmd = sh.molecule.bake("init", "role", "test-init", **options)
    run_command(cmd)

    with change_dir_to(role_directory):
        molecule_directory = pytest.helpers.molecule_directory()
        scenario_directory = os.path.join(molecule_directory, "test-scenario")
        options = {"role_name": "test-init", "driver-name": "vagrant"}
        cmd = sh.molecule.bake("init", "scenario", "test-scenario", **options)
        run_command(cmd)

        assert os.path.isdir(scenario_directory)
        confpath = os.path.join(scenario_directory, "molecule.yml")
        conf = util.safe_load_file(confpath)
        env = os.environ
        if "TESTBOX" in env:
            conf["platforms"][0]["box"] = env["TESTBOX"]
        if not os.path.exists("/dev/kvm"):
            if distro.name() == "Ubuntu" and distro.codename() == "bionic":
                conf["platforms"][0]["box"] = "centos/7"
            conf["driver"]["provider"] = {"name": "libvirt"}
            for p in conf["platforms"]:
                p["provider_options"] = {"driver": '"qemu"'}
        util.write_file(confpath, util.safe_dump(conf))

        cmd = sh.molecule.bake("--debug", "test", "-s", "test-scenario")
        run_command(cmd)


@pytest.mark.parametrize("scenario", [("vagrant_root"), ("config_options")])
def test_scenario(temp_dir, scenario):
    options = {"scenario_name": scenario}

    env = os.environ
    if not os.path.exists("/dev/kvm"):
        env.update({"VIRT_DRIVER": "'qemu'"})
        if distro.name() == "Ubuntu" and distro.codename() == "bionic":
            env.update({"TESTBOX": "centos/7"})

    scenario_directory = os.path.join(
        os.path.dirname(util.abs_path(__file__)), os.path.pardir, "scenarios"
    )

    with change_dir_to(scenario_directory):
        cmd = sh.molecule.bake("test", **options)
        run_command(cmd)


@pytest.mark.parametrize("scenario", [("provider_config_options_libvirt")])
@pytest.mark.skipif(
    next(
        (p for p in vagrant.Vagrant().plugin_list() if p.name == "vagrant-libvirt"),
        None,
    )
    is None,
    reason="vagrant-libvirt not installed",
)
def test_scenario_libvirt(temp_dir, scenario):
    options = {"scenario_name": scenario}

    env = os.environ
    if not os.path.exists("/dev/kvm"):
        env.update({"VIRT_DRIVER": "'qemu'"})
        if distro.name() == "Ubuntu" and distro.codename() == "bionic":
            env.update({"TESTBOX": "centos/7"})

    scenario_directory = os.path.join(
        os.path.dirname(util.abs_path(__file__)), os.path.pardir, "scenarios"
    )

    with change_dir_to(scenario_directory):
        cmd = sh.molecule.bake("test", **options)
        run_command(cmd)


@pytest.mark.parametrize("scenario", [("provider_config_options_vbox")])
@pytest.mark.skipif(which("VBoxManage") is None, reason="Virtualbox not installed")
def test_scenario_vbox(temp_dir, scenario):
    options = {"scenario_name": scenario}

    scenario_directory = os.path.join(
        os.path.dirname(util.abs_path(__file__)), os.path.pardir, "scenarios"
    )

    with change_dir_to(scenario_directory):
        cmd = sh.molecule.bake("test", **options)
        run_command(cmd)
