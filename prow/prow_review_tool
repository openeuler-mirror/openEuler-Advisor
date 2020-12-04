#!/usr/bin/env python3
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
This module provides interface for prow framework.
Three Scenario support:
    1: PR open event occurred at repository, then create review list in the PR
    2: PR update event occured at repository, then create review list in the PR
    3: PR's comment event occurred at reposity, then check comment and update status
Input:
    @event, event type that gitee send. review_tool only care for
     event 'Merge Request Hook' and 'Note Hook'
    @payload, json string that gitee post
Output:
    result. 0: success, other: fail
"""
import sys
import os
import json
import argparse
import subprocess


def get_cmd():
    """
    get review_tool real path
    """
    cmd_path = os.path.dirname(os.path.realpath(__file__))
    if cmd_path == "/usr/bin":
        review_cmd="/usr/bin/review_tool"
    else:
        review_cmd = os.path.join(os.path.dirname(cmd_path), "command/review_tool")
    return review_cmd

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--event", type=str,
            choices=['Merge Request Hook', 'Note Hook'], help="event type")
    parser.add_argument("-p", "--payload", type=str,
            help="json string that PROW framework send")
    args = parser.parse_args()
    return_code = 0
    if args.payload:
        data = json.loads(args.payload)
        if args.event == 'Merge Request Hook' and data['action'] == 'open' \
                or data['action'] == 'update':
            subp = subprocess.run(["python3", get_cmd(),
                    "-u", data['pull_request']['html_url'], "-w", "/tmp/review_dir", "-c"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    encoding="utf-8",
                    check=False)
            return_code = subp.returncode
        elif args.event == 'Note Hook' and data['action'] == 'comment' \
                and data['noteable_type'] == 'PullRequest':
            if not data['comment']['body'].startswith("/review"):
                sys.exit(2)
            for line in data['comment']['body'].splitlines():
                if line.strip().startswith("/review"):
                    args = line.strip().split(' ', 1)
                    content = args[1]
                    subp = subprocess.run(["python3", get_cmd(),
                        "-u", data['pull_request']['html_url'], "-e", content],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        encoding="utf-8",
                        check=False)
                    return_code = subp.returncode
        else:
            print("Event type: %s not support." % args.event)
    if return_code != 0:
        print(subp.stdout)
    sys.exit(return_code)
