#!/usr/bin/python3
"""
This is a command line tool to create reminder list for TC member
"""

import urllib
import urllib.request
import urllib.parse
import argparse
import json
import sys
import os
import yaml
from pprint import pprint
from datetime import datetime

class Advisor(object):
    """
    This is a object abstract TC robot
    """
    def __init__(self):
        self.secret = open(os.path.expanduser("~/.gitee_personal_token.json"), "r")
        self.token = json.load(self.secret)
        self.header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"}
        self.tc_members = None
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def get_json(self, url):
        """
        Return object parsed from remote json
        """
        headers = self.header.copy()
        headers["Content-Type"] = "application/json;charset=UTF-8"
        req = urllib.request.Request(url = url, 
                headers = headers,
                method = "GET")
       
        with urllib.request.urlopen(req) as u:
            resp = json.loads(u.read().decode("utf-8"))
        return resp

    def get_file(self, repo, path):
        """
        Get remote raw file
        """
        url = "https://gitee.com/{repo}/raw/master/{path}".format(repo=repo, path=path)
        req = urllib.request.Request(url = url, 
                headers = self.header,
                method = "GET")
       
        with urllib.request.urlopen(req) as u:
            resp = u.read()

        return resp

    def get_prs(self):
        """
        Get list of PRs
        """
        pulls_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls"
        list_url = pulls_url + "?access_token={token}&state=open&sort=created&direction=desc&page=1&per_page=100"
        url = list_url.format(token=self.token["access_token"])
        return self.get_json(url)

    def get_recent_prs(self, num):
        """
        Get list of _recent_ PRs
        """
        pulls_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls"
        list_all_url = pulls_url + "?access_token={token}&state=all&sort=created&direction=desc&"
        #list_all_url = pulls_url + "?access_token={token}&state=all&sort=created&direction=desc&per_page=100&page="
        list_all_url = list_all_url.format(token=self.token["access_token"])

        result = []
        page = 1

        if num <= 100:
            list_all_url = list_all_url + "per_page={num}&page=1".format(num=num)
            return self.get_json(list_all_url)
        

        list_all_url = list_all_url + "per_page=100&page="
        while num > 100:
            url = list_all_url + str(page)
            num -= 100
            page += 1
            result += self.get_json(url)
        url = list_all_url + str(page)
        result += self.get_json(url)
        return result

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
        m = yaml.load(adv.get_file("openeuler/community", "sig/TC/OWNERS"), Loader=yaml.Loader)
        self.tc_members = m["maintainers"]
        return m["maintainers"]

    def filter_out_tc(self, users):
        """
        Pick TC members from users
        """
        if not self.tc_members:
            self.get_tc_members()
        return [x for x in self.tc_members if x in users]
        
        
if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-n", "--number", help="Number of recent PRs to be processed", default="100")

    args = par.parse_args()

    adv = Advisor()
    tc_members = adv.get_tc_members()
    print("Current TC members :", tc_members)
    tc_statistic = {}
    for t in tc_members:
        tc_statistic[t] = 0
    PRs = adv.get_recent_prs(int(args.number))
    print("Statistic of recent {num} PRs".format(num=len(PRs)))

    for pr in PRs:
        commenter = pr["user"]["login"]
        if commenter in tc_members:
            tc_statistic[commenter] += 1
        comments = adv.get_pr_comments(pr["number"])
        for comment in comments:
            commenter = comment["user"]["login"]
            if commenter in tc_members:
                tc_statistic[commenter] += 1
            
    for tc in tc_statistic.keys():
        print("{tc} made {num} comments".format(tc=tc, num=tc_statistic[tc]))

