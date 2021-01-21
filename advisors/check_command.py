#!/usr/bin/python3
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: orange-snn
# Create: 2020-11-13
# ******************************************************************************/

"""
This script is used to check the command changes between the old
and new versions of rpm packages.
The merged result on difference is saved in the comd_diff_file.txt file in the working
directory.
default path: /var/tmp/tmpxxxxxx/comd_diff_file.txt
"""

import argparse
import subprocess
import sys
import os
import logging
import shutil
import tempfile


def process_check_command(rpms, work_path="/var/tmp/"):
    """
    Process rpms to check the command with two paths
    """
    temp_path = os.path.abspath(tempfile.mkdtemp(dir=work_path))
    abi_paths = [make_abi_path(temp_path, name) for name \
                 in ["previous_package", "current_package"]]
    rpm_path = [get_rpm_path(x[0], x[1]) for x in zip(rpms, abi_paths)]
    rpmfile_list = [do_rpm2cpio(x[0], x[1]) for x in zip(abi_paths, rpm_path)]

    pre_bin_file = has_command(rpmfile_list[0])
    cur_bin_file = has_command(rpmfile_list[1])
    comd_diff_file = os.path.join(temp_path, "comd_diff_file.txt")
    with open(comd_diff_file, "w") as diff_file:
        if os.path.getsize(pre_bin_file) == 0:
            if os.path.getsize(cur_bin_file) == 0:
                diff_file.write("There is no command in two rpms.")
            else:
                diff_file.write("The old packages don't have command, command only "\
                                "available in the new package.\n")
                diff_file.write("So, there are new command have been added.\n")
                for line in open(cur_bin_file):
                    diff_file.write(line)
        else:
            if os.path.getsize(cur_bin_file) == 0:
                diff_file.write("The new packages don't have command, command only "\
                                "available in the old package.\n")
                diff_file.write("So, these commands have been deleted.\n")

                for line in open(pre_bin_file):
                    diff_file.write(line)

            else:
                command_file = os.path.join(temp_path, "command_file.txt")
                subprocess.call("diff {} {} > {}".format(pre_bin_file, cur_bin_file, command_file),
                                shell=True)
                if os.path.getsize(command_file) == 0:
                    diff_file.write("The command files are the same in two rpmfiles.\n")
                else:
                    diff_file.write("The command files has some differents, changes as follow:\n")
                    for line in open(command_file):
                        diff_file.write(line)
                for pre_command in open(pre_bin_file):
                    pre_command = pre_command.strip('\n')
                    make_check_command(pre_command, comd_diff_file, abi_paths)

    logging.info("-------------all result write at:%s", comd_diff_file)
    return comd_diff_file


def make_check_command(temp_line, comd_diff_file, abi_paths):
    """
    Return the diff file about command in two rpms
    """
    with open(comd_diff_file, "w") as diff_file:
        diff_file.write("\n###############")
        diff_file.write("This is a diff about the command: {} ".format(temp_line))
        diff_file.write("###############\n")
    pre_cmd_path = two_abs_join(abi_paths[0], temp_line)
    cur_cmd_path = two_abs_join(abi_paths[1], temp_line)
    temp_pre_help = os.path.join(abi_paths[0], "temp_help.txt")
    subprocess.call(["{} --help > {}".format(pre_cmd_path, temp_pre_help)],
                    shell=True)
    temp_cur_help = os.path.join(abi_paths[1], "temp_help.txt")
    subprocess.call("{} --help > {}".format(cur_cmd_path, temp_cur_help),
                    shell=True)
    subprocess.call("diff {} {} >> {}".format(temp_pre_help, temp_cur_help,
                    comd_diff_file), shell=True)


def two_abs_join(abs1, abs2):
    """
    Join two path
    """
    abs2 = os.path.splitdrive(abs2)[1]
    abs2 = abs2.strip('\\/') or abs2
    return os.path.join(abs1, abs2)


def has_command(rpmfilelist):
    """
    Determine whether the current rpm file contains /usr/bin and /usr/sbin directories
    """
    with open(rpmfilelist, "r") as old_file:
        lines = old_file.readlines()
    with open(rpmfilelist, "w") as new_file:
        for line in lines:
            temp_line = line.split('/')[2]
            if temp_line in ("bin", "sbin"):
                new_file.write(line)
    return rpmfilelist


def do_rpm2cpio(rpm_path, rpm_file):
    """
    Exec the rpm command at rpm_path
    """
    cur_dir = os.getcwd()
    os.chdir(rpm_path)
    rpmfile_list = os.path.join(rpm_path, "rpmfile_list.txt")
    subprocess.call("rpm -qpl {} > {}".format(rpm_file, rpmfile_list), shell=True)
    subprocess.call("rpm2cpio {} | cpio -div".format(rpm_file), shell=True)
    os.chdir(cur_dir)
    return rpmfile_list


def make_abi_path(work_path, abipath):
    """
    Get the path to put so file from rpm and return the path.
    """
    filepath = os.path.join(work_path, abipath)
    if os.path.isdir(filepath):
        shutil.rmtree(filepath)
    os.makedirs(filepath)
    return filepath


def get_rpm_path(rpm_url, dest):
    """Get the path of rpm package"""
    rpm_path = ""
    if os.path.isfile(rpm_url):
        rpm_path = os.path.abspath(rpm_url)
        logging.debug("rpm exists:%s", rpm_path)
    else:
        rpm_name = os.path.basename(rpm_url)
        rpm_path = os.path.join(dest, rpm_name)
        logging.debug("downloading %s......", rpm_name)
        subprocess.call(["curl", rpm_url, "-L",
                         "--connect-timeout", "10",
                         "--max-time", "600",
                         "-sS", "-o", rpm_path])
    return rpm_path


def parse_command_line():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(prog="check_abi")

    parser.add_argument("-d", "--work_path", default="/var/tmp", nargs="?",
                        help="The work path to put rpm2cpio files and results"
                        " (e.g. /home/tmp_abidiff default: /var/tmp/)")
    parser.add_argument("-r", "--rpms", required=True, nargs=2,
                        metavar=('old_rpm', 'new_rpm'),
                        help="Path or URL of both the old and new RPMs")
    config = parser.parse_args()

    return config


def main():
    """Entry point for check_command"""
    config = parse_command_line()
    config.work_path = os.path.abspath(config.work_path)
    process_check_command(config.rpms, work_path=config.work_path)
    sys.exit(1)


if __name__ == "__main__":
    main()
