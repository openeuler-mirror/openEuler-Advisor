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
#
# ******************************************************************************/
"""
This is a helper script provides a way to query or list packages in specific SIG.
This script was inspired by previous work from @love_hangzhou
"""

import re
import sys
import argparse
import yaml


def list_packages(sigs, sig_name):
    """
    List all packages managed by specific SIG
    """
    for sig in sigs:
        if sig['name'].lower() == sig_name.lower():
            return sig['repositories']
    return []


def list_sigs(sigs):
    """
    List all current SIGs
    """
    result = []
    for sig in sigs:
        result.append(sig['name'])
    return result


def package_to_sigs(sigs, pkg_names):
    """
    Query which SIG manages the packages.
    """
    result = {}
    for pkg in pkg_names:
        for sig in sigs:
            repos = sig['repositories']
            for repo in repos:
                search_obj = re.search(pkg.lower(), repo.lower(), 0)
                if search_obj:
                    result[repo] = sig['name']
    return result


def print_list(lista):
    """
    Helper for print list
    """
    for i in lista:
        print(i)


def print_dict(dicta):
    """
    Helper for print dictionary
    """
    for k in dicta.keys():
        print(k + ": " + dicta[k])


def main():
    """
    Main entrance of functionality
    """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--list", default=False, nargs='?',
                       help="List packages managed by the specific SIG, or list all SIGs instead")
    group.add_argument("-q", "--query_packages", default=False, nargs='+',
                       help="Query which SIG manage the specific package")
    parser.add_argument("-f", "--yaml", default="sig/sigs.yaml",
                        help="Local path of sigs.yaml file")

    args = parser.parse_args()

    try:
        with open(args.yaml, 'r') as yaml_file:
            sigs = yaml.load(yaml_file, Loader=yaml.Loader)['sigs']
    except IOError:
        print("Failed to load information from %s" % args.yaml)
        parser.print_help()
        sys.exit(1)

    if args.list:
        print_list(list_packages(sigs, args.list))
    elif args.list is None:
        print_list(list_sigs(sigs))
    elif args.query_packages:
        print_dict(package_to_sigs(sigs, args.query_packages))
    else:
        pass


if __name__ == "__main__":
    main()
