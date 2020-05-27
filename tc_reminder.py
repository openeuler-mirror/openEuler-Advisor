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
from pprint import pprint

class Advisor:
    def __init__(self):
        self.secret = open(os.path.expanduser("~/.gitee_token.json"), "r")
        self.token = json.load(self.secret)
#        self.req = urllib.request.Request('https://gitee.com/api/v5/repos/#{owner}/issues')
        self.header = {"Content-Type": "application/json;charset=UTF-8", "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"}
        self.list_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls?access_token={token}&state=open&sort=created&direction=desc&page=1&per_page=100"
        self.desc_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls/{number}/comments?access_token={token}&page=1&per_page=100"
        self.tc_members = ["myeuler", "cynthia_xh", "shinwell_hu", "dream0819", "hanjun-guo", "xiexiuqi", "zhanghai_lucky"]

    def get_gitee(self, url):
        req = urllib.request.Request(url = url, 
                headers = self.header,
                method = "GET")
       
        with urllib.request.urlopen(req) as u:
            resp = json.loads(u.read().decode("utf-8"))
        return resp


    def get_prs(self):
        url = self.list_url.format(token=self.token["access_token"])
        return self.get_gitee(url)

    def get_pr_comments(self, number):
        url = self.desc_url.format(number=number, token=self.token["access_token"])
        return self.get_gitee(url)

    def filter_out_tc(self, users):
        return [x for x in self.tc_members if x in users]
        
if __name__ == "__main__":
    par = argparse.ArgumentParser()

    args = par.parse_args()

    adv = Advisor()
    PRs = adv.get_prs()
    for pr in PRs:
        print("URL: https://gitee.com/openeuler/community/pulls/{number}".format(number=pr["number"]))
        print("Title: "+pr["title"])
        comm = adv.get_pr_comments(pr["number"])
        users = []
        for c in comm:
           users.append(c["user"]["login"]) 
        tc = adv.filter_out_tc(users)
        print("Currently involved TC members: " + ", ".join(tc))
        print("\n")


