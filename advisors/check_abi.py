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
# Author: wangchuangGG
# Create: 2020-07-20
# ******************************************************************************/

"""
(1) This script is used to check the ABI changes between the old
    and new versions of dynamic libraries.
    The merged result on difference is saved in the xxx_all_abidiff.out file in the working
    directory.
    default path: /var/tmp/xxx_all_abidiff.out

(2) This script depends on abidiff from libabigail package.

(3) Command parameters
    This script accept two kind of command: compare_rpm or compare_so
    Run it without any paramter prints out help message.
"""

import argparse
import subprocess
import sys
import os
import logging
import shutil
import tempfile

def parse_command_line():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(prog="check_abi")

    parser.add_argument("-d", "--work_path", default="/var/tmp", nargs="?",
                        help="The work path to put rpm2cpio files and results"
                        " (e.g. /home/tmp_abidiff default: /var/tmp/)")
    parser.add_argument("-a", "--show_all_info", action="store_true", default=False,
                        help="show all infos includ changes in member name")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Show additional information")

    subparser = parser.add_subparsers(dest='command_name',
                                      help="Compare between two RPMs or two .so files")

    rpm_parser = subparser.add_parser('compare_rpm', help="Compare between two RPMs")
    rpm_parser.add_argument("-r", "--rpms", required=True, nargs=2,
                            metavar=('old_rpm', 'new_rpm'),
                            help="Path or URL of both the old and new RPMs")
    rpm_parser.add_argument("-d", "--debuginfo_rpm", nargs=2,
                            metavar=('old_debuginfo_rpm', 'new_debuginfo_rpm'),
                            required=False,
                            help="Path or URL of both the old and new debuginfo RPMs,"
                            "corresponding to compared RPMs.")
    rpm_parser.set_defaults(func=process_with_rpm)

    so_parser = subparser.add_parser('compare_so', help="Compare between two .so files")
    so_parser.add_argument("-s", "--sos", required=True, nargs=2,
                           metavar=('old_so', 'new_so'),
                           help="Path or URL of both the old and new .so files")
    so_parser.add_argument("-f", "--debuginfo_path", nargs=2, required=False,
                           metavar=('old_debuginfo_path', 'new_debuginfo_path'),
                           help="Path or URL of both the old and new debuginfo files,"
                           "corresponding to compared .so files.")
    so_parser.set_defaults(func=process_with_so)

    config = parser.parse_args()

    if config.command_name is None:
        parser.print_help()
        sys.exit(0)
    else:
        return config


def list_so_files(path):
    """
    Generate a list of all .so files in the directory.
    """
    # known suffix of exception
    # we cannot rely on number suffix for some .so files use complex version scheme.
    exception_list = ["hmac"]
    so_files = set()
    for dirpath, _, files in os.walk(path):
        for filename in files:
            fp = os.path.join(dirpath, filename)
            if os.path.islink(fp):
                continue
            if filename.split(".")[-1] in exception_list:
                continue
            if ".so" in filename:
                logging.debug(".so file found:%s", fp)
                so_files.add(fp)
    logging.debug("")
    return so_files

def find_all_so_file(path1, path2):
    """
    Generate a map between previous and current so files
    """
    all_so_pair = {}
    previous_sos = list_so_files(path1)
    current_sos = list_so_files(path2)
    logging.debug("previous_so:%s", previous_sos)
    logging.debug("current_so:%s", current_sos)
    prev_matched = set()
    curr_matched = set()
    if previous_sos and current_sos:
        for so_file1 in previous_sos:
            for so_file2 in current_sos:
                base_name1 = (os.path.basename(so_file1)).split('.')[0]
                base_name2 = (os.path.basename(so_file2)).split('.')[0]
                if base_name1 == base_name2:
                    all_so_pair[so_file1] = so_file2
                    prev_matched.add(so_file1)
                    curr_matched.add(so_file2)
    else:
        logging.info("Not found so files")
        sys.exit(0)
    prev_left = previous_sos - prev_matched
    curr_left = current_sos - curr_matched

    if prev_left:
        logging.info("Unmatched .so file in previous version")
        logging.info("Usually means deleted .so in current version")
        logging.info("%s\n", prev_left)
    if curr_left:
        logging.info("Unmatched .so file in current version")
        logging.info("Usually means newly added .so in current version")
        logging.info("%s\n", curr_left)

    logging.debug("mapping of .so files:%s\n", all_so_pair)
    return all_so_pair


def make_abi_path(work_path, abipath):
    """
    Get the path to put so file from rpm
    return the path.
    """
    fp = os.path.join(work_path, abipath)
    if os.path.isdir(fp):
        shutil.rmtree(fp)
    os.makedirs(fp)
    return fp


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

def do_rpm2cpio(rpm2cpio_path, rpm_file):
    """
    Exec the rpm2cpio at rpm2cpio_path.
    """
    cur_dir = os.getcwd()
    os.chdir(rpm2cpio_path)
    logging.debug("\n----working in path:%s----", os.getcwd())
    logging.debug("rpm2cpio %s", rpm_file)
    subprocess.run("rpm2cpio {} | cpio -id > /dev/null 2>&1".format(rpm_file), shell=True)
    os.chdir(cur_dir)

def merge_all_abidiff_files(all_abidiff_files, work_path, rpm_base_name):
    """
    Merge the all diff files to merged_file.
    return the merged_file.
    """
    merged_file = os.path.join(work_path, "{}_all_abidiff.out".format(rpm_base_name))
    if os.path.exists(merged_file):
        subprocess.run("rm -rf {}".format(merged_file), shell=True)

    ofile = open(merged_file, "a+")
    for diff_file in all_abidiff_files:
        diff_file_name = os.path.basename(diff_file)
        ofile.write("---------------diffs in {}:----------------\n".format(diff_file_name))
        for txt in open(diff_file, "r"):
            ofile.write(txt)
    ofile.close()
    return merged_file

def do_abidiff(config, all_so_pair, work_path, base_name, debuginfo_path):
    """
    Exec the abidiff and write result to files.
    return the abidiff returncode.
    """
    if not all_so_pair:
        logging.info("There are no .so files to compare")
        sys.exit(0)

    if debuginfo_path:
        logging.debug("old_debuginfo_path:%s\nnew_debuginfo_path:%s",
                      debuginfo_path[0], debuginfo_path[1])
        with_debuginfo = True
    else:
        with_debuginfo = False

    return_code = 0
    all_abidiff_files = []
    for old_so_file in all_so_pair:
        new_so_file = all_so_pair[old_so_file]
        logging.debug("begin abidiff between %s and %s", old_so_file, new_so_file)

        abidiff_file = os.path.join(work_path,
                                    "{}_{}_abidiff.out".format(base_name,
                                                               os.path.basename(new_so_file)))

        so_options = "{} {}".format(old_so_file, new_so_file)

        if config.show_all_info:
            additional_options = "--harmless"
        else:
            additional_options = "--changed-fns --deleted-fns --added-fns"

        if with_debuginfo:
            debug_options = "--d1 {} --d2 {}".format(debuginfo_path[0], debuginfo_path[1])
        else:
            debug_options = ""

        abidiff_template = "abidiff {so_options} {debug_options} {additional_options} > {difffile}"
        abidiff_cmd = abidiff_template.format(so_options=so_options,
                                              debug_options=debug_options,
                                              additional_options=additional_options,
                                              difffile=abidiff_file)

        ret = subprocess.run(abidiff_cmd, shell=True)

        all_abidiff_files.append(abidiff_file)
        logging.info("result write in: %s", abidiff_file)
        return_code |= ret.returncode

    merged_file = merge_all_abidiff_files(all_abidiff_files, work_path, base_name)
    logging.info("all results writed in: %s", merged_file)
    return return_code


def validate_sos(config):
    """
    Validate the command arguments
    """
    for so in config.sos:
        if not os.path.isfile(so) or ".so" not in so:
            logging.error(f"{so} not exists or not a .so file")
            sys.exit(0)

    if config.debuginfo_path:
        for d in config.debuginfo_path:
            if not os.path.exists(d):
                logging.error(f"{d} not exists")
                sys.exit(0)


def check_result(returncode):
    """
    Check the result of abidiff
    """
    ABIDIFF_ERROR_BIT = 1
    if returncode == 0:
        logging.info("No ABI differences found.")
    elif returncode & ABIDIFF_ERROR_BIT:
        logging.info("An unexpected error happened to abidiff")
    else:
        logging.info("ABI differences found.")


def process_with_rpm(config):
    """
    Process the file with type of rpm.
    """
    work_path = config.work_path
    temp_path = os.path.abspath(tempfile.mkdtemp(dir=work_path))

    abi_paths = [make_abi_path(temp_path, name) for name in ["previous_package", "current_package"]]
    logging.debug("abi_paths:%s\n", abi_paths)

    rpm_path = [get_rpm_path(x[0], x[1]) for x in zip(config.rpms, abi_paths)]
    logging.debug("rpm_path:%s\n", rpm_path)

    _ = [do_rpm2cpio(x[0], x[1]) for x in zip(abi_paths, rpm_path)]

    if config.debuginfo_rpm:
        debuginfo_rpm_path = [get_rpm_path(x[0], x[1])
                              for x in zip(config.debuginfo_rpm, abi_paths)]

        logging.debug("debuginfo_rpm_path:%s\n", debuginfo_rpm_path)

        _ = [do_rpm2cpio(x[0], x[1]) for x in zip(abi_paths, debuginfo_rpm_path)]

    os.chdir(temp_path)
    logging.debug("\n----begin abidiff working in path:%s----", os.getcwd())

    so_paths = [os.path.join(x, "usr/lib64") for x in abi_paths]

    all_so_pairs = find_all_so_file(so_paths[0], so_paths[1])

    debuginfo_paths = [os.path.join(x, "usr/lib/debug") for x in abi_paths]

    rpm_base_name = os.path.basename(rpm_path[0]).split('.')[0]

    returncode = do_abidiff(config, all_so_pairs, work_path, rpm_base_name, debuginfo_paths)
    logging.debug("\n--- delete temp directory:%s ---", temp_path)
    shutil.rmtree(temp_path)
    check_result(returncode)
    return returncode


def process_with_so(config):
    """
    Process the file with type of .so.
    """
    validate_sos(config)
    work_path = config.work_path
    all_so_pair = {}
    so_path = list(map(os.path.abspath, config.sos))
    all_so_pair[so_path[0]] = so_path[1]
    os.chdir(work_path)
    logging.debug("\n----begin abidiff with .so working in path:%s----", os.getcwd())

    so_base_name = os.path.basename(so_path[0]).split('.')[0]
    if config.debuginfo_path:
        debuginfo_path = list(map(os.path.abspath, config.debuginfo_path))
    else:
        debuginfo_path = None

    returncode = do_abidiff(config, all_so_pair, work_path, so_base_name, debuginfo_path)
    check_result(returncode)
    return returncode


def main():
    """Entry point for check_abi"""
    config = parse_command_line()
    if config.verbose:
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
    ret = config.func(config)
    sys.exit(ret)


if __name__ == "__main__":
    main()
