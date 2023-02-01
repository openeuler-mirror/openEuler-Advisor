#!/usr/bin/python3
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
This is a script to check upgradable information against upstream
"""
import os
import sys
import argparse
import re
from datetime import datetime
from pyrpm.spec import Spec, replace_macros
import yaml

from advisors import gitee
from advisors import check_upstream
from advisors import version_recommend

NEW_COMMENT = """Dear {repo} maintainer:

We found this issue has been open for {days} days.

If you have any problems during implementation, please let the community known.

We'll try our best to help.

This is a automatic recommendation from openEuler-Advisor. If you think the suggestion is incorrect,
 
please fill an issue at https://gitee.com/openeuler/openEuler-Advisor to help us improve.

Yours openEuler Advisor.
"""


def _filter_except(excpts, sources):
    """
    Filter except case in sources
    """
    for exp in excpts:
        for source in sources.keys():
            result = re.fullmatch(exp, source)
            if result:
                sources.pop(source)
    return sources


def get_ver_tags(my_gitee, repo, clean_tag=True, cwd_path=None):
    """
    Get version tags of given package
    """
    if cwd_path:
        try:
            repo_yaml = open(os.path.join(cwd_path, "{pkg}.yaml".format(pkg=repo)))
        except FileNotFoundError:
            print("WARNING: {pkg}.yaml can't be found in local path: {path}.".format(pkg=repo,
                                                                                     path=cwd_path))
            repo_yaml = my_gitee.get_yaml(repo)
    else:
        repo_yaml = my_gitee.get_yaml(repo)

    if repo_yaml:
        pkg_info = yaml.load(repo_yaml, Loader=yaml.Loader)
    else:
        return None

    vc_type = pkg_info.get("version_control", None)
    if vc_type is None:
        print("Missing version_control in YAML file")
        return None

    switcher = {
        "hg": check_upstream.check_hg,
        "hg-raw": check_upstream.check_hg_raw,
        "github": check_upstream.check_github,
        "git": check_upstream.check_git,
        "gitlab.gnome": check_upstream.check_gnome,
        "svn": check_upstream.check_svn,
        "metacpan": check_upstream.check_metacpan,
        "pypi": check_upstream.check_pypi,
        "rubygem": check_upstream.check_rubygem,
        "gitee": check_upstream.check_gitee,
        "gnu-ftp": check_upstream.check_gnu_ftp,
        "ftp": check_upstream.check_ftp,
        "sourceforge": check_upstream.check_sourceforge
    }

    check_method = switcher.get(vc_type, None)
    if check_method:
        tags = check_method(pkg_info, clean_tag)
    else:
        print("Unsupport version control method {vc}".format(vc=vc_type))
        return None

    excpt_list = my_gitee.get_version_exception()
    if repo in excpt_list:
        tags = _filter_except(excpt_list[repo], tags)
    return tags


def main():
    """
    Main entrance of the functionality
    """
    parameters = argparse.ArgumentParser()
    parameters.add_argument("-p", "--push", action="store_true",
                            help="Push the version bump as an issue to src-openeuler repository")
    parameters.add_argument("-d", "--default", type=str, default=os.getcwd(),
                            help="The fallback place to look for YAML information")
    parameters.add_argument("repo", type=str,
                            help="Repository to be checked for upstream version info")

    args = parameters.parse_args()
    main_process(args.push, args.default, args.repo)


def main_process(push, default, repo):
    """
    Main process of the functionality
    """
    print("Checking", repo)
    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)
    spec_string = user_gitee.get_spec(repo)
    if not spec_string:
        print("WARNING: Spec of {pkg} can't be found on master".format(pkg=repo))
        return None

    spec_file = Spec.from_string(spec_string)
    cur_version = replace_macros(spec_file.version, spec_file)
    if cur_version.startswith('v') or cur_version.startswith('V'):
        cur_version = cur_version[1:]

    print("Current version is", cur_version)
    pkg_tags = get_ver_tags(user_gitee, repo, cwd_path=default)
    print("known release tags:", list(pkg_tags.keys()))

    if not pkg_tags:
        return None

    if cur_version not in pkg_tags.keys():
        print("WARNING: Current {ver} doesn't exist in upstream." \
              "Please double check.".format(ver=cur_version))

    ver_rec = version_recommend.VersionRecommend(list(pkg_tags.keys()), cur_version, 0)

    if pkg_tags.get(cur_version):
        cur_ver_release_time = pkg_tags[cur_version].strftime("%Y/%m/%d")
    else:
        cur_ver_release_time = "-/-/-"
    if pkg_tags.get(ver_rec.latest_version):
        lasts_version_release_time = pkg_tags[ver_rec.latest_version].strftime("%Y/%m/%d")
    else:
        lasts_version_release_time = "-/-/-"

    if pkg_tags.get(ver_rec.maintain_version):
        maintain_version_release_time = pkg_tags[ver_rec.maintain_version].strftime("%Y/%m/%d")
    else:
        maintain_version_release_time = "-/-/-"

    print("current version is {}  {}".format(cur_version, cur_ver_release_time))
    print("Latest version is {}  {}".format(ver_rec.latest_version, lasts_version_release_time))
    print("Maintain version is {}  {}".format(ver_rec.maintain_version, maintain_version_release_time))

    need_push_issue = True
    version_type = version_recommend.VersionType()
    if version_type.compare(ver_rec.latest_version, cur_version) == 1:
        if push:
            issues = user_gitee.get_issues(repo)
            for issue in issues:
                if "Upgrade to latest release" in issue["title"]:
                    need_push_issue = False
                    ages = datetime.now() - user_gitee.get_gitee_datetime(issue["created_at"])
                    if ages.days <= 30:
                        print("Advise has been issues only %d days ago" % ages.days)
                        print("Give developers more time to handle it.")
                        break
                    user_gitee.post_issue_comment(repo, issue["number"], NEW_COMMENT.format(
                        repo=repo,
                        days=ages.days))
                    break
            if need_push_issue:
                tile = """Upgrade to latest release [{repo}: {cur_ver} {cur_ver_date} -> {ver} {date}]""".format(
                    repo=repo,
                    ver=ver_rec.latest_version,
                    date=lasts_version_release_time,
                    cur_ver=cur_version,
                    cur_ver_date=cur_ver_release_time,
                    )
                body = """Dear {repo} maintainer:

We found the latest version of {repo} is {ver} release at {date}, while the current version in openEuler mainline is {cur_ver} release at {cur_ver_date}.

Please consider upgrading.

Yours openEuler Advisor.

If you think this is not proper issue, Please visit https://gitee.com/openeuler/openEuler-Advisor.
Issues and feedbacks are welcome.""".format(repo=repo,
                                            ver=ver_rec.latest_version,
                                            date=lasts_version_release_time,
                                            cur_ver=cur_version,
                                            cur_ver_date=cur_ver_release_time)

                user_gitee.post_issue(repo, tile, body)
        return [repo, cur_version, ver_rec.latest_version]
    else:
        return None


if __name__ == "__main__":
    main()
