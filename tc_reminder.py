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

class Advisor:
    def __init__(self):
        self.secret = open(os.path.expanduser("~/.gitee_token.json"), "r")
        self.token = json.load(self.secret)
#        self.req = urllib.request.Request('https://gitee.com/api/v5/repos/#{owner}/issues')
        self.header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"}
        self.tc_members = None
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"


    def get_json(self, url):
        headers = self.header.copy()
        headers["Content-Type"] = "application/json;charset=UTF-8"
        req = urllib.request.Request(url = url, 
                headers = headers,
                method = "GET")
       
        with urllib.request.urlopen(req) as u:
            resp = json.loads(u.read().decode("utf-8"))
        return resp


    def get_file(self, repo, path):
        url = "https://gitee.com/{repo}/raw/master/{path}".format(repo=repo, path=path)
        req = urllib.request.Request(url = url, 
                headers = self.header,
                method = "GET")
       
        with urllib.request.urlopen(req) as u:
            resp = u.read()

        return resp

    def get_prs(self):
        list_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls?access_token={token}&state=open&sort=created&direction=desc&page=1&per_page=100"
        url = list_url.format(token=self.token["access_token"])
        return self.get_json(url)

    def get_pr_comments(self, number):
        desc_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls/{number}/comments?access_token={token}&page=1&per_page=100"
        url = desc_url.format(number=number, token=self.token["access_token"])
        return self.get_json(url)

    def get_tc_members(self):
        m = yaml.load(adv.get_file("openeuler/community", "sig/TC/OWNERS"), Loader=yaml.Loader)
        self.tc_members = m["maintainers"]
        return m["maintainers"]

    def filter_out_tc(self, users):
        if not self.tc_members:
            self.get_tc_members()
        return [x for x in self.tc_members if x in users]
        
        
if __name__ == "__main__":
    par = argparse.ArgumentParser()

    args = par.parse_args()

    adv = Advisor()
    PRs = adv.get_prs()
    for pr in PRs:
        commenters = []
        commenters.append(pr["user"]["login"])
        last_update = pr["updated_at"]
        print("URL: https://gitee.com/openeuler/community/pulls/{number}".format(number=pr["number"]))
        print("Title: "+pr["title"])
        comm = adv.get_pr_comments(pr["number"])
        for c in comm:
            #print("comment updated at:")
            #pprint(datetime.strptime(c["updated_at"], adv.time_format)) 
            commenters.append(c["user"]["login"]) 
        tc = adv.filter_out_tc(commenters)
        print("Currently involved TC members: " + ", ".join(tc) + "\n")


