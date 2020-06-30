#!/usr/bin/python3
"""
This is a script to check upgradable information against upstream
"""
from pyrpm.spec import Spec, replace_macros

import yaml
import json
import datetime
import sys
import os
import argparse

import urllib.error
import gitee
import check_upstream
import version_recommend

if __name__ == "__main__":
    parameters = argparse.ArgumentParser()
    parameters.add_argument("-p", "--push", action="store_true",
            help="Push the version bump as an issue to src-openeuler repository") 
    parameters.add_argument("-d", "--default", type=str, default=os.getcwd(),
            help="The fallback place to look for YAML information")
    parameters.add_argument("repo", type=str,
            help="Repository to be checked for upstream version info") 

    args = parameters.parse_args()

    gitee = gitee.Gitee()
    prj_name = args.repo
    spec_string = gitee.get_spec(prj_name)
    if not spec_string:
        print("{repo} seems to be an empty repository".format(repo=args.repo))
        sys.exit(1)

    s_spec = Spec.from_string(spec_string)

    current_version = replace_macros(s_spec.version, s_spec)

    print("Checking ", prj_name)
    print("current version is ", current_version)

    try:
        prj_info_string = gitee.get_yaml(prj_name)
    except urllib.error.HTTPError:
        prj_info_string = ""

    if not prj_info_string:
        print("Fallback to {dir}".format(dir=args.default))
        try:
            prj_info_string = open(os.path.join(args.default, prj_name + ".yaml")).read()
        except FileNotFoundError:
            print("Failed to get YAML info for {pkg}".format(pkg=prj_name))
            sys.exit(1)

    prj_info = yaml.load(prj_info_string, Loader=yaml.Loader)

    vc_type = prj_info["version_control"]
    if vc_type == "hg":
        tags = check_upstream.check_hg(prj_info)
    elif vc_type == "github":
        tags = check_upstream.check_github(prj_info)
    elif vc_type == "git":
        tags = check_upstream.check_git(prj_info)
    elif vc_type == "gitlab.gnome":
        tags = check_upstream.check_gnome(prj_info)
    elif vc_type == "svn":
        tags = check_upstream.check_svn(prj_info)
    elif vc_type == "metacpan":
        tags = check_upstream.check_metacpan(prj_info)
    elif vc_type == "pypi":
        tags = check_upstream.check_pypi(prj_info)
    else:
        print("Unsupport version control method {vc}".format(vc=vc_type))
        sys.exit(1)

    print("known release tags :", tags)
    v = version_recommend.VersionRecommend(tags, current_version, 0)
    print("Latest version is ", v.latest_version)
    print("Maintain version is", v.maintain_version)
