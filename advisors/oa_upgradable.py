#!/usr/bin/python3
"""
This is a script to check upgradable information against upstream
"""
import os
import sys
import argparse

from pyrpm.spec import Spec, replace_macros

import yaml

import gitee
import check_upstream
import version_recommend


def _filter_except(excpts, sources):
    """
    Filter except case in sources
    """
    for exp in excpts:
        sources = [s for s in sources if exp not in s]
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
        "hg":check_upstream.check_hg,
        "hg-raw":check_upstream.check_hg_raw,
        "github":check_upstream.check_github,
        "git":check_upstream.check_git,
        "gitlab.gnome":check_upstream.check_gnome,
        "svn":check_upstream.check_svn,
        "metacpan":check_upstream.check_metacpan,
        "pypi":check_upstream.check_pypi,
        "rubygem":check_upstream.check_rubygem,
        "gitee":check_upstream.check_gitee,
        "gnu-ftp":check_upstream.check_gnu_ftp,
        "ftp":check_upstream.check_ftp
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

    print("Checking", args.repo)

    user_gitee = gitee.Gitee()
    spec_string = user_gitee.get_spec(args.repo)
    if not spec_string:
        print("WARNING: {pkg}.spec can't be found on master".format(pkg=args.repo))
        sys.exit(1)

    spec_file = Spec.from_string(spec_string)
    cur_version = replace_macros(spec_file.version, spec_file)
    
    if cur_version.startswith('v') or cur_version.startswith('V'):
        cur_version = cur_version[1:]

    print("Current version is", cur_version)
    pkg_tags = get_ver_tags(user_gitee, args.repo, args.default)
    print("known release tags:", pkg_tags)

    if pkg_tags is None:
        sys.exit(1)

    if cur_version not in pkg_tags:
        print("WARNING: Current {ver} doesn't exist in upstream."\
              "Please double check.".format(ver=cur_version))

    ver_rec = version_recommend.VersionRecommend(pkg_tags, cur_version, 0)

    print("Latest version is", ver_rec.latest_version)
    print("Maintain version is", ver_rec.maintain_version)

    if cur_version != ver_rec.latest_version:
        if args.push:
            user_gitee.post_issue(args.repo, "Upgrade to latest release", """Dear {repo} maintainer:

We found the latest version of {repo} is {ver}, while the current version in openEuler mainline is {cur_ver}.

Please consider upgrading.

Yours openEuler Advisor.

If you think this is not proper issue, Please visit https://gitee.com/openeuler/openEuler-Advisor.
Issues and feedbacks are welcome.""".format(repo=args.repo,
                                            ver=ver_rec.latest_version,
                                            cur_ver=cur_version))


if __name__ == "__main__":
    main()
