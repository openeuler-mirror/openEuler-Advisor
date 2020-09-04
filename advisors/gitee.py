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
import sys
import os.path
import json
import base64
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
        self.src_openeuler_url = self.gitee_url + "src-openeuler/{package}/raw/{branch}/"
        self.advisor_url = self.gitee_url + "openeuler/openEuler-Advisor/raw/master/"
        self.specfile_url_template = self.src_openeuler_url + "{specfile}"
        self.yamlfile_url_template = self.src_openeuler_url + "{package}.yaml"
        #self.advisor_url_template = "https://gitee.com/openeuler/openEuler-Advisor/raw/master/upstream-info/{package}.yaml"
        self.advisor_url_template = self.advisor_url + "upstream-info/{package}.yaml"
        #self.specfile_exception_url = "https://gitee.com/openeuler/openEuler-Advisor/raw/master/helper/specfile_exceptions.yaml"
        self.specfile_exception_url = self.advisor_url + "advisors/helper/specfile_exceptions.yaml"
        self.version_exception_url = self.advisor_url + "advisors/helper/version_exceptions.yaml"
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
        #headers["User-Agent"] = "curl/7.66.0"
        #headers["Content-Type"] = "application/json;charset=UTF-8"
        #headers["HOST"] = "gitee.com"
        #headers["Accept"] = "*/*"
        return self.post_gitee(url, values)

    def create_issue(self, repo, version, branch):
        """
        Create issue in gitee
        """
        title = "Upgrade {pkg} to {ver} in {br}".format(pkg=repo, ver=version, br=branch)
        body = """This issue is automatically created by openEuler-Advisor.
               Please check the correspond PR is accepted before close it.
               Thanks.
               Yours openEuler-Advisor."""
        self.post_issue(repo, title, body)

    def get_reviewers(self, repo):
        """
        Get reviewers of pkg
        """
        url = "https://gitee.com/api/v5/repos/src-openeuler/{pkg}/collaborators".format(pkg=repo)
        return self.get_gitee(url)

    def create_pr(self, head, repo, version, branch):
        """
        Create PR in gitee
        """
        assignees = ""
        reviewer_info = self.get_reviewers(repo)
        if reviewer_info:
            reviewer_list = json.loads(reviewer_info)
            assignees = ",".join(reviewer["login"] for reviewer in reviewer_list)
        url = "https://gitee.com/api/v5/repos/src-openeuler/{pkg}/pulls".format(pkg=repo)
        values = {}
        values["access_token"] = self.token["access_token"]
        values["title"] = "Upgrade {pkg} to {ver}".format(pkg=repo, ver=version)
        values["head"] = "{hd}:{br}".format(hd=head, br=branch)
        values["base"] = branch
        values["assignees"] = assignees
        values["body"] = """This is a automatically created PR by openEuler-Advisor.
                         Please be noted that it's not throughly tested.
                         Review carefully before accept this PR.
                         Thanks.
                         Yours openEuler-Advisor."""
        return self.post_gitee(url, values)

    def get_gitee(self, url, headers=None):
        """
        GET from gitee api
        """
        if headers is None:
            req = urllib.request.Request(url=url, headers=self.headers)
        else:
            req = urllib.request.Request(url=url, headers=headers)
        try:
            u = urllib.request.urlopen(req)
            return u.read().decode("utf-8")
        except urllib.error.HTTPError:
            return None

    def get_gitee_json(self, url):
        """
        Get and load gitee json response
        """
        json_resp = []
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json;charset=UTF-8"
        resp = self.get_gitee(url, headers)
        if resp:
            json_resp = json.loads(resp)
        return json_resp

    def get_spec_exception(self):
        """
        Get well known spec file exceptions
        """
        resp = self.get_gitee(self.specfile_exception_url)
        if not resp:
            print("ERROR: specfile_exceptions.yaml may not exist.")
            sys.exit(1)
        excpt = yaml.load(resp, Loader=yaml.Loader)
        return excpt

    def get_version_exception(self):
        """
        Get vertion recommend exceptions
        """
        resp = self.get_gitee(self.version_exception_url)
        if not resp:
            print("ERROR: version_exceptions.yaml may not exist.")
            sys.exit(1)
        excpt = yaml.load(resp, Loader=yaml.Loader)
        return excpt

    def get_spec(self, pkg, br="master"):
        """
        Get openeuler spec file for specific package
        """
        specurl = self.specfile_url_template.format(branch=br, package=pkg, specfile=pkg + ".spec")
        excpt_list = self.get_spec_exception()
        if pkg in excpt_list:
            dir_name = excpt_list[pkg]["dir"]
            file_name = excpt_list[pkg]["file"]
            specurl = urllib.parse.urljoin(specurl, os.path.join(dir_name, file_name))
        resp = self.get_gitee(specurl)
        return resp

    def get_yaml(self, pkg):
        """
        Get upstream yaml metadata for specific package
        """
        yamlurl = self.advisor_url_template.format(package=pkg)
        resp = self.get_gitee(yamlurl)
        if not resp:
            yamlurl = self.yamlfile_url_template.format(branch="master", package=pkg)
            resp = self.get_gitee(yamlurl)
            if not resp:
                print("WARNING: {repo}.yaml can't be found in upstream-info and repo.".format(repo=pkg))
        return resp

    def get_community(self, repo):
        """
        Get yaml data from community repo
        """
        yamlurl = "https://gitee.com/api/v5/repos/openeuler/community/contents/"\
				  "repository/{repo}.yaml".format(repo=repo)
        resp = self.get_gitee_json(yamlurl)
        resp_str = base64.b64decode(resp["content"])
        return resp_str

    def get_issues(self, pkg, prj="src-openeuler"):
        """
        List all open issues of pkg
        """
        issues_url = "https://gitee.com/api/v5/repos/{prj}/{pkg}/issues?".format(prj=prj, pkg=pkg)
        #parameters = "access_token={token}&state=open&sort=created&derection=desc&creator=" + self.token["user"]
        parameters = "state=open&sort=created&direction=desc&page=1&per_page=20"
        return self.get_gitee_json(issues_url + parameters)

    def get_issue_comments(self, pkg, prj="src-openeuler"):
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

