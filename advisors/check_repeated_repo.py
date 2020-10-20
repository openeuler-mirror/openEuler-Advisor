#!/usr/bin/python3
# ******************************************************************************
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
This is an automatic script for checking repo is repeated or not
"""
import argparse
import os
import sys
import yaml

from advisors import yaml2url


def get_url(repo_file):
    """
    Get url of given package
    """
    try:
        repo_yaml = open(repo_file)
    except FileNotFoundError:
        print("WARNING: {} can't be found in local path.".format(repo_file))
        return None

    if repo_yaml:
        pkg_info = yaml.load(repo_yaml, Loader=yaml.Loader)
    else:
        return None

    if not pkg_info:
        print("WARNING: load {} yaml fail".format(repo_file))
        return None

    return yaml2url.yaml2url(pkg_info)


def check_repo(directory):
    """
    Check repeate repo
    """
    url_dict = {}
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            url = get_url(file_path)
            if url:
                if url in url_dict.keys():
                    print("WARNING: {file1} is repeat with {file2}, url is {url}" \
                          .format(file1=url_dict[url], file2=file, url=url))
                else:
                    url_dict[url] = file
            else:
                continue


def main():
    """
    Main entrance of the functionality
    """
    pars = argparse.ArgumentParser()
    pars.add_argument("-d", "--default", type=str, default=None,
                      help="The fallback place to look for YAML information")
    args = pars.parse_args()

    if args.default:
        check_repo(args.default)
    else:
        print("WARNING: Please specify the direction (-d ../upstream-info/) to be checkd.")
        sys.exit(1)


if __name__ == "__main__":
    main()
