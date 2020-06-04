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
        self.secret = open(os.path.expanduser("~/.gitee_personal_token.json"), "r")
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
        pulls_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls"
        list_url = pulls_url + "?access_token={token}&state=open&sort=created&direction=desc&page=1&per_page=100"
        url = list_url.format(token=self.token["access_token"])
        return self.get_json(url)

    def get_pr_comments(self, number):
        pulls_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls"
        desc_url = pulls_url + "/{number}/comments?access_token={token}&page=1&per_page=100"
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
        comments = adv.get_pr_comments(pr["number"])
        last_update = datetime.strptime(comments[0]["updated_at"], adv.time_format)
        comments.reverse()
        current_lgtm = 0
        current_approve = False
        for comment in comments:
            commenters.append(comment["user"]["login"]) 
            if comment["body"].startswith("new changes are detected"):
                last_update = datetime.strptime(comment["updated_at"], adv.time_format)
                break # older comments are ignored
            elif comment["body"].startswith("***lgtm*** is added in this pull request"):
                current_lgtm = current_lgtm + 1
            elif comment["body"].startswith("***approved*** is added in this pull request"):
                current_approve = True

        tc = adv.filter_out_tc(commenters)
        old = datetime.now() - last_update.replace(tzinfo=None)
        print("Currently {num} days old".format(num=old.days))
        print("Currently involved TC members: " + ", ".join(tc))
        print("Currently has {num} /lgtm".format(num=current_lgtm))
        if current_approve:
            print("Currently /approve")
        print("")


