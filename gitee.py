#!/usr/bin/python3
"""
This is a simple script to query that contact person for specific package
"""

import urllib
import urllib.request
import urllib.parse
import urllib.error
import argparse
import yaml
import re
import os.path
import json
import pprint


class Gitee:
    def __init__(self):
        self.secret = open(os.path.expanduser("~/.gitee_personal_token.json"), "r")
        self.token = json.load(self.secret)

        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) Gecko/20100101 Firefox/50.0'}
        self.specfile_url_template = "https://gitee.com/src-openeuler/{package}/raw/master/{specfile}"
        self.yamlfile_url_template = "https://gitee.com/src-openeuler/{package}/raw/master/{package}.yaml"
        self.advisor_url_template = "https://gitee.com/openeuler/openEuler-Advisor/raw/master/upstream-info/{package}.yaml"
        self.specfile_exception_url = "https://gitee.com/openeuler/openEuler-Advisor/raw/master/helper/specfile_exceptions.yaml"

    def post_gitee(self, url, values, headers = None):
        if headers == None:
            headers = self.headers.copy()
        data = urllib.parse.urlencode(values).encode('utf-8')
        req = urllib.request.Request(url = url, data = data, headers=headers, method="POST")
        try:
            u = urllib.request.urlopen(req)
        except urllib.error.HTTPError as err:
            print("WARNING:"+str(err.code))
            print("WARNING:"+str(err.headers))
        return u.read().decode("utf-8")

    def fork_repo(self, repo):
        url = "https://gitee.com/api/v5/repos/src-openeuler/{repo}/forks".format(repo=repo)
        values = {}
        values["access_token"] = self.token["access_token"]
       # headers["User-Agent"] = "curl/7.66.0"
        #headers["Content-Type"] = "application/json;charset=UTF-8"
        #headers["HOST"] = "gitee.com"
        #headers["Accept"] = "*/*"
        return self.post_gitee(url, values)

    def create_pr(self, head, repo):
        url = "https://gitee.com/api/v5/repos/src-openeuler/{repo}/pulls".format(repo=repo)
        values = {}
        values["access_token"] = self.token["access_token"]
        values["title"] = "Upgrade to latest version of {repo}".format(repo=repo)
        values["head"] = "{head}:master".format(head=head)
        values["base"] = "master"
        values["body"] = "This is a (mostly) automatically created PR by openEuler-Advisor.\nPlease be noted that it's not throughly tested.\nReview carefully before accept this PR.\nThanks.\nYours openEuler-Advisor.\n"
        return self.post_gitee(url, values)

    def get_gitee(self, url, headers=None):
        if headers == None:
            req = urllib.request.Request(url=url, headers=self.headers)
        else:
            req = urllib.request.Request(url=url, headers=headers)
        u = urllib.request.urlopen(req)
        return u.read().decode("utf-8")

    def get_gitee_json(self, url):
        #headers = self.headers.copy()
        headers = {}
        headers["Content-Type"] = "application/json;charset=UTF-8"
        resp = self.get_gitee(url, headers)
        return json.loads(resp)

    def get_spec_exception(self):
        resp = self.get_gitee(self.specfile_exception_url)
        exps = yaml.load(resp, Loader=yaml.Loader)
        return exps

    def get_spec(self, pkg):
        exp = self.get_spec_exception()
        if pkg in exp:
            dir_name = exp[pkg]["dir"]
            file_name = exp[pkg]["file"]
            specurl = self.specfile_url_template.format(package=pkg, specfile=dir_name + "/" + file_name)
        else:
            specurl = self.specfile_url_template.format(package=pkg, specfile=pkg+".spec")

        return self.get_gitee(specurl)

    def get_yaml(self, pkg):
        yamlurl = self.advisor_url_template.format(package=pkg)
        resp = self.get_gitee(yamlurl)
        if re.match("Not found", resp):
            yamlurl = self.yamlfile_url_template.format(package=pkg)
            resp = self.get_gitee(yamlurl)
            if re.match("Not found", resp):
                print("Cannot find upstream metadata")
                return False
            else:
                return resp
        else:
            return False

class Advisor:
    def __init__(self):
        self.gitee = Gitee()

    """
    def new_issue(owner, repo, title, body):
        @param["access_token"] = @token["access_token"]
        @param["repo"] = repo
        @param["title"] = title
        @param["body"] = body
        @cmd += " 'https://gitee.com/api/v5/repos/#{owner}/issues'"
        @cmd += " -d '" + @param.to_json + "'"
        #puts @cmd
        resp = %x[#{@cmd}]
        #puts resp
    """

class openEuler_TC:
    def __init__(self):
        self.gitee = Gitee()
        self.list_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls?access_token={token}&state=open&sort=created&direction=desc&page=1&per_page=100"
        self.desc_url = "https://gitee.com/api/v5/repos/openeuler/community/pulls/{number}/comments?access_token={token}&page=1&per_page=100"
        self.tc_members = ["myeuler", "cynthia_xh", "shinwell_hu", "dream0819", "hanjun-guo", "xiexiuqi", "zhanghai_lucky"]


    def get_prs(self):
        url = self.list_url.format(token=self.token["access_token"])
        return self.gitee.get_gitee(url)

    def get_pr_comments(self, number):
        url = self.desc_url.format(number=number, token=self.token["access_token"])
        return self.gitee.get_gitee(url)

    def filter_out_tc(self, users):
        return [x for x in self.tc_members if x in users]
        
if __name__ == "__main__":
    pass

