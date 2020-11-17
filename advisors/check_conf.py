#!/usr/bin/python3
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [openeuler-jenkins] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# Author:
# Create: 2020-09-23
# Description: pkgship and check_abi
# **********************************************************************************
"""
import os
import argparse
import logging
import shutil
import tempfile
import subprocess

class CheckConfig():
    """check config file"""
    def __init__(self, old_rpm, new_rpm, work_path="/var/tmp",
                 output_file="/var/tmp/config_change.md"):
        self.output_file = output_file
        self._old_rpm = old_rpm
        self._new_rpm = new_rpm
        self._work_path = work_path
        self._add_configs = {}
        self._delete_configs = {}
        self._changed_configs = {}

    def do_check(self, name, config_files):
        """
        Check files
        """
        new_dict = {}
        old_dict = {}
        old_conf = open(config_files[0])
        under_configs = ""
        old_under_configs = make_dict(old_conf, "old", new_dict, under_configs)
        old_conf.close()

        new_conf = open(config_files[1])
        understand_configs = make_dict(new_conf, "new", new_dict, old_under_configs)
        new_conf.close()
        not_understand_configs = {}
        if understand_configs:
            not_understand_configs[name] = understand_configs
            logging.debug("\n---not_understand_configs:%s----", not_understand_configs)

        changed_configs = ""
        add_configs = ""
        del_configs = ""
        for key in new_dict:  # 修改的内容
            if old_dict.get(key) is not None:
                if old_dict[key] != new_dict[key]:
                    changed_configs = changed_configs + "Key:" + key + "  Old_value:" +\
                     old_dict[key] + "  New_value:" + new_dict[key] + "\n"
                old_dict.pop(key)
            else:
                add_configs = add_configs + "Key:" + key + "  Value:" + new_dict[key] + "\n"
        if changed_configs:
            self._changed_configs[name] = changed_configs
            logging.debug("\n---changed_configs:%s----", self._changed_configs)
        if add_configs:
            self._add_configs[name] = add_configs
            logging.debug("\n---add_configs:%s----", self._add_configs)
        for key in old_dict:  # 删除的内容
            del_configs = del_configs + "Key:" + key + "  Value:" + old_dict[key] + "\n"
        if del_configs:
            self._delete_configs[name] = del_configs
            logging.debug("\n---delete_configs:%s----", self._delete_configs)
        return not_understand_configs

    def _check_diff(self, old_and_new_path, need_check_file):
        """
        Check diff file
        """
        for name in need_check_file:
            name = name.split("/", 1)[-1].split()[0]
            logging.debug("path:%s", old_and_new_path)
            if md5_check(os.path.join(old_and_new_path[0], name),
                               os.path.join(old_and_new_path[1], name)):
                print("The md5 values are the same.")
            else:
                config_files = [os.path.join(x, name) for x in old_and_new_path]
                not_understand_configs = self.do_check(name, config_files)
        return not_understand_configs

    def _prepare(self, temp_path):
        """
        Prepare for rpm2cpio
        """
        old_and_new_path = [os.path.join(temp_path, x) for x in ["old", "new"]]
        _ = [os.makedirs(x) for x in old_and_new_path]
        rpms = [self._old_rpm, self._new_rpm]
        _ = [subprocess.call('cd {}; rpm2cpio {} | cpio -di > /dev/null 2>&1'.format(x[0], x[1]),
             shell=True) for x in zip(old_and_new_path, rpms)]
        logging.debug("\n---old version path:%s   new version path:%s----",
                      old_and_new_path[0], old_and_new_path[1])
        return old_and_new_path

    def _write_result(self, remove_file, add_file, not_understand_configs):
        """
        Write result
        """
        ofile = open(self.output_file, "a+")
        have_found_changed_info = False
        if remove_file:
            ofile.write("# Delete config files:\n")
            ofile.writelines(remove_file)
        if add_file:
            ofile.write("# Add config files:\n")
            ofile.writelines(add_file)
        if self._add_configs:
            ofile.write("# Add configs:\n")
            have_found_changed_info = True
            write_content(ofile, self._add_configs)
        if self._delete_configs:
            ofile.write("# Delete configs:\n")
            have_found_changed_info = True
            write_content(ofile, self._delete_configs)
        if self._changed_configs:
            ofile.write("# Changed configs:\n")
            have_found_changed_info = True
            write_content(ofile, self._changed_configs)
        if not_understand_configs:
            ofile.write("# No understand configs:\n")
            have_found_changed_info = True
            write_content(ofile, not_understand_configs)
        if have_found_changed_info:
            logging.info("\n---Change infos write at:%s----", self.output_file)
        else:
            logging.info("\n---Configs are same----")
        ofile.close()

    def conf_check(self):
        """
        Begin check
        """
        temp_path = os.path.abspath(tempfile.mkdtemp(dir=self._work_path))
        self._old_rpm = get_rpms(self._old_rpm, temp_path)
        self._new_rpm = get_rpms(self._new_rpm, temp_path)
        try:
            if md5_check(self._old_rpm, self._new_rpm):
                logging.info("Same RPM")
                return
            old_config = subprocess.run(['rpm', '-qpc', self._old_rpm],
                                        stdout=subprocess.PIPE, check=True)
            new_config = subprocess.run(['rpm', '-qpc', self._new_rpm],
                                        stdout=subprocess.PIPE, check=True)
            remove_file = set()
            add_file = set()
            need_check_file = set()
            not_understand_configs = {}
            for line in old_config.stdout.split():
                remove_file.add(line)
            for line in new_config.stdout.split():
                if line in remove_file:
                    remove_file.remove(line)
                    need_check_file.add(line)
                else:
                    add_file.add(line)

            if need_check_file:
                old_and_new_path = self._prepare(temp_path)
                not_understand_configs = self._check_diff(old_and_new_path, need_check_file)
            self._write_result(remove_file, add_file, not_understand_configs)
        except FileNotFoundError:
            logging.error("file not found")
        shutil.rmtree(temp_path)


def write_content(ofile, infos):
    """
    Write file
    """
    for name in infos:
        ofile.write("In " + name + ":\n")
        ofile.write(infos[name])
    ofile.write("\n")


def get_rpms(rpm_url, dest):
    """
    Get rpm path
    """
    rpm_path = ""
    if os.path.isfile(rpm_url):
        rpm_path = os.path.abspath(rpm_url)
    else:
        rpm_name = os.path.basename(rpm_url)
        rpm_path = os.path.join(dest, rpm_name)
        logging.info("downloading %s ...", rpm_name)
        subprocess.run("wget -t 5 -c -P {} {}".format(dest, rpm_url), shell=True, check=True)
    return rpm_path


def md5_check(old_rpm, new_rpm):
    """
    Check md5sum
    """
    old_md5 = subprocess.run(['md5sum', old_rpm], stdout=subprocess.PIPE, check=True)
    new_md5 = subprocess.run(['md5sum', new_rpm], stdout=subprocess.PIPE, check=True)
    return old_md5.stdout.split()[0] == new_md5.stdout.split()[0]


def make_dict(conf_file, status, dict_file, understand_configs):
    """
    Make a dict in check conf, and return the understand_configs
    """
    for line in conf_file:  # 建立字典
        if "=" in line and line.split()[0] != "#":
            a_b = line.split('=', 1)
            if len(a_b) == 2:
                dict_file[a_b[0].strip()] = a_b[1].strip()
            elif len(a_b) != 1:
                understand_configs = understand_configs + \
                                     "in {} file:".format(status) + line + "\n"
    return understand_configs



def parse_command_line():
    """Parse the command line args"""
    parser = argparse.ArgumentParser(prog="check_conf")

    parser.add_argument("-o", "--old_rpm", required=True, help="The old version rpm.")
    parser.add_argument("-n", "--new_rpm", required=True, help="The new version rpm.")
    parser.add_argument("-p", "--work_path", default="/var/tmp", nargs="?",
                        help="The work path to put rpm2cpio files and results")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Show additional information")
    args = parser.parse_args()
    return args


def main():
    """
    Entry point for check_conf
    """
    args = parse_command_line()
    if args.verbose:
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
    work_path = os.path.abspath(args.work_path)
    check_conf = CheckConfig(args.old_rpm, args.new_rpm, work_path)
    check_conf.conf_check()

if __name__ == "__main__":
    main()
