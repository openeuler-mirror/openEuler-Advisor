#!/usr/bin/python3
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
This is a helper script for working with gitee.com
"""

import os
import json
import base64
import urllib
import urllib.request
import urllib.parse
import urllib.error
import threading
from datetime import datetime
import yaml


class Gitee():
    """
    Gitee is a helper class to abstract gitee.com api
    """
    _instance_lock = threading.Lock()
    _first_init = True

    def __new__(cls):
        if not hasattr(Gitee, "_instance"):
            with Gitee._instance_lock:
                if not hasattr(Gitee, "_instance"):
                    Gitee._instance = object.__new__(cls)
        return Gitee._instance

    def __init__(self):
        if not self._first_init:
            return
        self._first_init = False
        with open(os.path.expanduser("~/.gitee_personal_token.json"), "r") as secret:
            self.token = json.load(secret)

        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) '\
                        'Gecko/20100101 Firefox/50.0'}
        self.community_url = "https://gitee.com/api/v5/repos/openeuler/community/contents/"
        self.src_openeuler_url = "https://gitee.com/api/v5/repos/src-openeuler/{repo}/contents/"
        self.advisor_url = "https://gitee.com/api/v5/repos/openeuler/openEuler-Advisor/contents/"

        self.helper_info = {}
        specfile_exception_url = self.advisor_url + "advisors/helper/specfile_exceptions.yaml"
        resp = self.__get_gitee_json(specfile_exception_url)
        if not resp:
            print("ERROR: specfile_exceptions.yaml may not exist.")
            raise NameError
        resp_str = base64.b64decode(resp["content"]).decode("utf-8")
        self.helper_info["specfile_excepts"] = yaml.load(resp_str, Loader=yaml.Loader)

        version_exception_url = self.advisor_url + "advisors/helper/version_exceptions.yaml"
        resp = self.__get_gitee_json(version_exception_url)
        if not resp:
            print("ERROR: version_exceptions.yaml may not exist.")
            raise NameError
        resp_str = base64.b64decode(resp["content"]).decode("utf-8")
        self.helper_info["version_excepts"] = yaml.load(resp_str, Loader=yaml.Loader)

        upgrade_branches_url = self.advisor_url + "advisors/helper/upgrade_branches.yaml"
        resp = self.__get_gitee_json(upgrade_branches_url)
        if not resp:
            print("ERROR: upgrade_branches.yaml may not exist.")
            raise NameError
        resp_str = base64.b64decode(resp["content"]).decode("utf-8")
        self.helper_info["upgrade_branches"] = yaml.load(resp_str, Loader=yaml.Loader)


        reviewer_checklist_url = self.advisor_url + "advisors/helper/reviewer_checklist.yaml"
        resp = self.__get_gitee_json(reviewer_checklist_url)
        if not resp:
            print("ERROR: reviewer_checklist.yaml may not exist.")
            raise NameError
        resp_str = base64.b64decode(resp["content"]).decode("utf-8")
        self.helper_info["reviewer_checklist"] = yaml.load(resp_str, Loader=yaml.Loader)

    def __post_gitee(self, url, values, headers=None):
        """
        POST into gitee API
        """
        if headers is None:
            headers = self.headers.copy()
        data = urllib.parse.urlencode(values).encode('utf-8')
        req = urllib.request.Request(url=url, data=data, headers=headers, method="POST")
        try:
            result = urllib.request.urlopen(req)
            return result.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            print("ERROR: error occurred.\nerrcode: %d\nreason: %s\nheaders:\n%s"
                    % (err.code, err.reason, str(err.headers)))
            return False

    def __patch_gitee(self, url, values, headers=None):
        """
        PATCH method to gitee API
        """
        if headers is None:
            headers = self.headers.copy()
        data = urllib.parse.urlencode(values).encode('utf-8')
        req = urllib.request.Request(url=url, data=data, headers=headers, method="PATCH")
        try:
            result = urllib.request.urlopen(req)
            return result.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            print("ERROR: error occurred.\nerrcode: %d\nreason: %s\nheaders:\n%s"
                    % (err.code, err.reason, str(err.headers)))
            return False

    def fork_repo(self, repo, owner="src-openeuler"):
        """
        Fork repository in gitee
        """
        url_template = "https://gitee.com/api/v5/repos/{owner}/{repo}/forks"
        url = url_template.format(owner=owner, repo=repo)
        values = {}
        values["access_token"] = self.token["access_token"]
        #headers["User-Agent"] = "curl/7.66.0"
        #headers["Content-Type"] = "application/json;charset=UTF-8"
        #headers["HOST"] = "gitee.com"
        #headers["Accept"] = "*/*"
        return self.__post_gitee(url, values)

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

    def get_reviewers(self, repo, owner="src-openeuler"):
        """
        Get reviewers of pkg
        """
        url_template = "https://gitee.com/api/v5/repos/{owner}/{pkg}/collaborators"
        url = url_template.format(owner=owner, pkg=repo)
        return self.__get_gitee(url)

    def create_pr(self, repo, version, branch, owner="src-openeuler"):
        """
        Create PR in gitee
        """
        assignees = ""
        reviewer_info = self.get_reviewers(repo)
        if reviewer_info:
            reviewer_list = json.loads(reviewer_info)
            assignees = ",".join(reviewer["login"] for reviewer in reviewer_list)
        url_template = "https://gitee.com/api/v5/repos/{owner}/{pkg}/pulls"
        url = url_template.format(owner=owner, pkg=repo)
        values = {}
        values["access_token"] = self.token["access_token"]
        values["title"] = "Upgrade {pkg} to {ver}".format(pkg=repo, ver=version)
        values["head"] = "{hd}:{br}".format(hd=self.token["user"], br=branch)
        values["base"] = branch
        values["assignees"] = assignees
        values["body"] = """This is a automatically created PR by openEuler-Advisor.
                         Please be noted that it's not throughly tested.
                         Review carefully before accept this PR.
                         Thanks.
                         Yours openEuler-Advisor."""
        return self.__post_gitee(url, values)

    def create_pr_comment(self, repo, number, body, owner="src-openeuler"):
        """
        Post comment to the given specific PR
        """
        url_template = "https://gitee.com/api/v5/repos/{owner}/{repo}/pulls/{number}/comments"
        url = url_template.format(owner=owner, repo=repo, number=number)
        values = {}
        values["access_token"] = self.token["access_token"]
        values["body"] = body
        return self.__post_gitee(url, values)

    def get_pr_comments_all(self, owner, repo, number):
        """
        Get all comments of PR
        """
        url_template = "https://gitee.com/api/v5/repos/{owner}/{repo}/pulls/{number}/comments"\
                       "?page={page}&per_page={per_page}"
        res = []
        for i in range(1, 101):
            url = url_template.format(owner=owner, repo=repo, number=number, page=i, per_page=100)
            comments = self.__get_gitee_json(url)
            if not comments:
                break
            res.extend(comments)
        return res

    def edit_pr_comment(self, owner, repo, comment_id, body):
        """
        edit a comment
        """
        url_template = "https://gitee.com/api/v5/repos/{owner}/{repo}/pulls/comments/{comment_id}"
        url = url_template.format(owner=owner, repo=repo, comment_id=comment_id)
        values = {}
        values["access_token"] = self.token["access_token"]
        values["body"] = body
        return self.__patch_gitee(url, values)

    def __get_gitee(self, url, headers=None):
        """
        GET from gitee api
        """
        if '?' in url:
            new_url = url + "&"
        else:
            new_url = url + "?"
        new_url = new_url + "access_token=" + self.token["access_token"]
        if headers is None:
            req = urllib.request.Request(url=new_url, headers=self.headers)
        else:
            req = urllib.request.Request(url=new_url, headers=headers)
        try:
            result = urllib.request.urlopen(req)
            return result.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            print("get_gitee failed to access: %s" % (url))
            print("get_gitee failed: %d, %s" % (error.code, error.reason))
            return None

    def get_pr(self, repo, num, owner="src-openeuler"):
        """
        Get detailed information of the given specific PR
        """
        url_template = "https://gitee.com/api/v5/repos/{owner}/{repo}/pulls/{number}"
        url = url_template.format(owner=owner, repo=repo, number=num)
        return self.__get_gitee_json(url)

    def __get_gitee_json(self, url):
        """
        Get and load gitee json response
        """
        json_resp = []
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json;charset=UTF-8"
        resp = self.__get_gitee(url, headers)
        if resp:
            json_resp = json.loads(resp)
        return json_resp

    def get_branch_info(self, branch):
        """
        Get upgrade branch info
        """
        branches_info = self.helper_info["upgrade_branches"]
        for br_info in branches_info["branches"]:
            if branch == br_info["name"]:
                return br_info
        print("WARNING: Don't support branch: {} in auto-upgrade.".format(branch))
        return ""

    def get_spec_exception(self, repo):
        """
        Get well known spec file exception
        """
        excpt_list = self.helper_info["specfile_excepts"]
        if repo in excpt_list:
            return excpt_list[repo]
        return ""

    def get_version_exception(self):
        """
        Get version recommend exceptions
        """
        return self.helper_info["version_excepts"]

    def get_reviewer_checklist(self):
        """
        Get reviewer checklist
        """
        return self.helper_info["reviewer_checklist"]

    def get_spec(self, pkg, branch="master"):
        """
        Get openeuler spec file for specific package
        """
        specurl = self.src_openeuler_url + "{repo}.spec"
        specurl = specurl.format(repo=pkg)
        excpt = self.get_spec_exception(pkg)
        if excpt:
            specurl = urllib.parse.urljoin(specurl, os.path.join(excpt["dir"], excpt["file"]))
        specurl = specurl + "?ref={}".format(branch)
        resp = self.__get_gitee_json(specurl)
        resp_str = ""
        if resp:
            resp_str = base64.b64decode(resp["content"]).decode("utf-8")
        return resp_str

    def get_yaml(self, pkg):
        """
        Get upstream yaml metadata for specific package
        """
        yamlurl = self.advisor_url + "upstream-info/{}.yaml".format(pkg)
        resp = self.__get_gitee_json(yamlurl)
        if not resp:
            yamlurl = self.src_openeuler_url + "{repo}.yaml"
            yamlurl = yamlurl.format(repo=pkg)
            resp = self.__get_gitee_json(yamlurl)
            if not resp:
                print("WARNING: {}.yaml can't be found in upstream-info and repo.".format(pkg))
                return ''
        return base64.b64decode(resp["content"]).decode("utf-8")

    def get_sigs(self):
        """
        Get upstream sigs
        """
        sigs_url = "https://gitee.com/openeuler/community/raw/master/sig/sigs.yaml"
        req = urllib.request.Request(url=sigs_url, headers=self.headers)
        data = urllib.request.urlopen(req)
        sigs = yaml.load(data.read().decode("utf-8"), Loader=yaml.Loader)
        return sigs

    def get_community(self, repo):
        """
        Get yaml data from community repo
        """
        yamlurl = self.community_url + "repository/{repo}.yaml".format(repo=repo)
        resp = self.__get_gitee_json(yamlurl)
        resp_str = ""
        if resp:
            resp_str = base64.b64decode(resp["content"]).decode("utf-8")
        return resp_str

    def get_issues(self, pkg, group="src-openeuler"):
        """
        List all open issues of pkg
        """
        issues_url = "https://gitee.com/api/v5/repos/{owner}/{repo}/issues?"\
                .format(owner=group, repo=pkg)
        param_template = "state=open&sort=created&direction=desc&page={}&per_page=100"
        result = []
        for i in range(1, 101):
            parameters = param_template.format(i)
            issues = self.__get_gitee_json(issues_url + parameters)
            if not issues:
                break
            result.extend(issues)
        return result

    def get_issue_comments(self, pkg, number, group="src-openeuler"):
        """
        Get comments of specific issue
        """
        issues_url = "https://gitee.com/api/v5/repos/{owner}/{repo}/issues/{number}/comments?"\
                .format(owner=group, repo=pkg, number=number)
        param_template = "page={}&per_page=100&order=asc"
        result = []
        for i in range(1, 101):
            parameters = param_template.format(i)
            comments = self.__get_gitee_json(issues_url + parameters)
            if not comments:
                break
            result.extend(comments)
        return result

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
        self.__post_gitee(issues_url, parameters)

    def post_issue_comment(self, pkg, number, comment, prj="src-openeuler"):
        """
        Post comment of issue
        """
        issues_url = "https://gitee.com/api/v5/repos/{prj}/{pkg}/issues/{number}/"\
                     "comments".format(prj=prj, pkg=pkg, number=number)
        parameters = {}
        parameters["access_token"] = self.token["access_token"]
        parameters["body"] = comment
        self.__post_gitee(issues_url, parameters)

    @staticmethod
    def get_gitee_datetime(time_string):
        """
        Get datetime of gitee
        """
        time_format = "%Y-%m-%dT%H:%M:%S%z"
        result = datetime.strptime(time_string, time_format)
        return result.replace(tzinfo=None)


if __name__ == "__main__":
    pass
