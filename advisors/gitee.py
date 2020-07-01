#!/usr/bin/python3
"""
This is a helper script for working with gitee.com
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
from datetime import datetime


class Gitee(object):
    """
    Gitee is a helper class to abstract gitee.com api 
    """
    def __init__(self):
        self.secret = open(os.path.expanduser("~/.gitee_personal_token.json"), "r")
        self.token = json.load(self.secret)

        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) Gecko/20100101 Firefox/50.0'}
        self.gitee_url = "https://gitee.com/"
        self.src_openeuler_url = self.gitee_url + "src-openeuler/{package}/raw/master/"
        self.advisor_url = self.gitee_url + "openeuler/openEuler-Advisor/raw/master/"
        self.specfile_url_template = self.src_openeuler_url + "{specfile}"
        self.yamlfile_url_template = self.src_openeuler_url + "{package}.yaml"
        #self.advisor_url_template = "https://gitee.com/openeuler/openEuler-Advisor/raw/master/upstream-info/{package}.yaml"
        self.advisor_url_template = self.advisor_url + "upstream-info/{package}.yaml"
        #self.specfile_exception_url = "https://gitee.com/openeuler/openEuler-Advisor/raw/master/helper/specfile_exceptions.yaml"
        self.specfile_exception_url = self.advisor_url + "advisors/helper/specfile_exceptions.yaml"
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def post_gitee(self, url, values, headers=None):
        """
        POST into gitee API
        """
        if headers is None:
            headers = self.headers.copy()
        data = urllib.parse.urlencode(values).encode('utf-8')
        req = urllib.request.Request(url=url, data=data, headers=headers, method="POST")
        try:
            u = urllib.request.urlopen(req)
            return u.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            print("WARNING:" + str(err.code))
            print("WARNING:" + str(err.headers))
            return False

    def fork_repo(self, repo):
        """
        Fork repository in gitee
        """
        url = "https://gitee.com/api/v5/repos/src-openeuler/{repo}/forks".format(repo=repo)
        values = {}
        values["access_token"] = self.token["access_token"]
       # headers["User-Agent"] = "curl/7.66.0"
        #headers["Content-Type"] = "application/json;charset=UTF-8"
        #headers["HOST"] = "gitee.com"
        #headers["Accept"] = "*/*"
        return self.post_gitee(url, values)

    def create_pr(self, head, repo):
        """
        Create PR in gitee
        """
        url = "https://gitee.com/api/v5/repos/src-openeuler/{repo}/pulls".format(repo=repo)
        values = {}
        values["access_token"] = self.token["access_token"]
        values["title"] = "Upgrade to latest version of {repo}".format(repo=repo)
        values["head"] = "{head}:master".format(head=head)
        values["base"] = "master"
        values["body"] = """This is a (mostly) automatically created PR by openEuler-Advisor.
Please be noted that it's not throughly tested.
Review carefully before accept this PR.
Thanks.
Yours openEuler-Advisor.
"""
        return self.post_gitee(url, values)

    def get_gitee(self, url, headers=None):
        """
        GET from gitee api
        """
        if headers is None:
            req = urllib.request.Request(url=url, headers=self.headers)
        else:
            req = urllib.request.Request(url=url, headers=headers)
        u = urllib.request.urlopen(req)
        return u.read().decode("utf-8")

    def get_gitee_json(self, url):
        """
        get and load gitee json response
        """
        headers = self.headers.copy()
        #headers = {}
        headers["Content-Type"] = "application/json;charset=UTF-8"
        resp = self.get_gitee(url, headers)
        return json.loads(resp)

    def get_spec_exception(self):
        """
        get well known spec file exceptions
        """
        resp = self.get_gitee(self.specfile_exception_url)
        exps = yaml.load(resp, Loader=yaml.Loader)
        return exps

    def get_spec(self, pkg):
        """
        get openeuler spec file for specific package
        """
        specurl = self.specfile_url_template.format(package=pkg, specfile=pkg + ".spec")
        exp = self.get_spec_exception()
        if pkg in exp:
            dir_name = exp[pkg]["dir"]
            file_name = exp[pkg]["file"]
            specurl = urllib.parse.urljoin(specurl, os.path.join(dir_name, file_name))

        try:
            resp = self.get_gitee(specurl)
        except urllib.error.HTTPError:
            resp = ""

        return resp

    def get_yaml(self, pkg):
        """
        get upstream yaml metadata for specific package
        """
        yamlurl = self.advisor_url_template.format(package=pkg)
        try:
            resp = self.get_gitee(yamlurl)
        except urllib.error.HTTPError:
            resp = "Not found"
        if re.match("Not found", resp):
            yamlurl = self.yamlfile_url_template.format(package=pkg)
            try:
                resp = self.get_gitee(yamlurl)
            except urllib.error.HTTPError:
                resp = "Not found"
            if re.match("Not found", resp):
                print("Cannot find upstream metadata")
                return False
            else:
                return resp
        else:
            return resp

    def get_issues(self, pkg, prj="src-openeuler"):
        """
        List all open issues of pkg
        """
        issues_url = "https://gitee.com/api/v5/repos/{prj}/{pkg}/issues?".format(prj=prj, pkg=pkg)
        #parameters = "access_token={token}&state=open&sort=created&derection=desc&creator=" + self.token["user"]
        parameters = "state=open&sort=created&direction=desc&page=1&per_page=20"
        return self.get_gitee_json(issues_url + parameters)

    def get_issue_comments(self, pkg, number, prj="src-openeuler"):
        """
        Get comments of specific issue
        """
        issues_url = "https://gitee.com/api/v5/repos/{prj}/{pkg}/issues?".format(prj=prj, pkg=pkg)
        parameters = "number={num}&page=1&per_page=20&order=asc"
        return self.get_gitee_json(issues_url + parameters)

    def post_issue(self, pkg, title, body, prj="src-openeuler"):
        """
        Post new issue
        """
        issues_url = "https://gitee.com/api/v5/repos/{prj}/issues".format(prj=prj)
        parameters = {}
        parameters["access_token"] = self.token["access_token"]
        parameters["repo"] = pkg
        parameters["title"] = title
        parameters["body"] = body
        self.post_gitee(issues_url, parameters)

    def post_issue_comment(self, pkg, number, comment, prj="src-openeuler"):
        issues_url = "https://gitee.com/api/v5/repos/{prj}/{pkg}/issues/{number}/comments".format(
                prj=prj, pkg=pkg, number=number)
        parameters = {}
        parameters["access_token"] = self.token["access_token"]
        parameters["body"] = comment
        self.post_gitee(issues_url, parameters)

    def get_gitee_datetime(self, time_string):
        result = datetime.strptime(time_string, self.time_format)
        return result.replace(tzinfo=None)

        
if __name__ == "__main__":
    pass

