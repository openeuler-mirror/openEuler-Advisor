#!/usr/bin/env python3
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
This is a command line tool to create reminder list for TC member
"""

import os
import json
import urllib
import urllib.request
import urllib.parse
from datetime import datetime
import yaml


class Advisor():
    """
    This is a object abstract TC robot
    """

    def __init__(self):
        self.secret = open(os.path.expanduser("~/.gitee_personal_token.json"), "r")
        self.token = json.load(self.secret)
        self.header = {"User-Agent": '''Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0)
        Gecko/20100101 Firefox/50.0'''}
        self.tc_members = None
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def get_json(self, url):
        """
        Return object parsed from remote json
        """
        headers = self.header.copy()
        headers["Content-Type"] = "application/json;charset=UTF-8"
        req = urllib.request.Request(url=url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as result:
            resp = json.loads(result.read().decode("utf-8"))
        return resp

    def get_file(self, repo, path):
        """
        Get remote raw file
        """
        url = "https://gitee.com/{repo}/raw/master/{path}".format(repo=repo, path=path)
        req = urllib.request.Request(url=url, headers=self.header, method="GET")
        with urllib.request.urlopen(req) as result:
            resp = result.read()
        return resp

    def get_prs(self):
        """
        Get list of PRs
        """
        pulls_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls"
        list_url = pulls_url + "?access_token={token}&state=open&sort=created&" \
                               "direction=desc&page=1&per_page=100"
        url = list_url.format(token=self.token["access_token"])
        return self.get_json(url)

    def get_pr_comments(self, number):
        """
        Get Comments for a specific PR
        """
        pulls_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls"
        desc_url = pulls_url + "/{number}/comments?access_token={token}&page=1&per_page=100"
        url = desc_url.format(number=number, token=self.token["access_token"])
        return self.get_json(url)

    def get_tc_members(self):
        """
        Get list of current TC members
        """
        owners = yaml.load(self.get_file("openeuler/community", "sig/TC/OWNERS"),
                           Loader=yaml.Loader)
        self.tc_members = owners["maintainers"]
        return owners["maintainers"]

    def filter_out_tc(self, users):
        """
        Pick TC members from users
        """
        if not self.tc_members:
            self.get_tc_members()
        return [x for x in self.tc_members if x in users]


def main():
    """
    Main entrance of the functionality
    """
    advisor = Advisor()
    pr_list = advisor.get_prs()
    pr_list.reverse()
    for preq in pr_list:
        commenters = []
        commenters.append(preq["user"]["login"])
        last_update = preq["updated_at"]
        print("URL: https://gitee.com/openeuler/community/pulls/{}".format(preq["number"]))
        print("Title: " + preq["title"])
        comments = advisor.get_pr_comments(preq["number"])
        last_update = datetime.strptime(comments[0]["updated_at"], advisor.time_format)
        comments.reverse()
        current_lgtm = 0
        current_approve = False
        for comment in comments:
            commenters.append(comment["user"]["login"])
            if comment["body"].startswith("new changes are detected"):
                last_update = datetime.strptime(comment["updated_at"], advisor.time_format)
                break  # older comments are ignored
            if comment["body"].startswith("***lgtm*** is added in this pull request"):
                current_lgtm = current_lgtm + 1
            elif comment["body"].startswith("***approved*** is added in this pull request"):
                current_approve = True

        tc_member = advisor.filter_out_tc(commenters)
        age = datetime.now() - last_update.replace(tzinfo=None)
        age_days = max(age.days, 0)
        print("Currently {num} days old".format(num=age_days))
        print("Currently involved TC members: " + ", ".join(tc_member))
        print("Currently has {num} /lgtm".format(num=current_lgtm))
        if current_approve:
            print("Currently /approve")
        print("")


if __name__ == "__main__":
    main()
