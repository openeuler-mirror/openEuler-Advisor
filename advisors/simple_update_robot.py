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
This is a robot to do package upgrade automation
Expected process:
 1. get URL to download updated version
 2. Change Version to new one
 3. Change Source or Source0 if needed
 4. Update %changelog
 5. auto rpmbuild -ba
 6. fork on gitee and clone to local
 7. git add, git commit, git push
 8. PR on gitee
"""

import sys
import re
import time
import shutil
import os.path
import datetime
import argparse
import subprocess
import yaml
from pyrpm.spec import Spec, replace_macros

import gitee
import oa_upgradable
import version_recommend


def download_source_url(pkg, spec, o_ver, n_ver):
    """
    Download source file from Source or Source0 URL
    """
    source_str = subprocess.check_output(["spectool -S {}.spec".format(pkg)],
                                         shell=True).decode("utf-8")
    if source_str:
        source = source_str.split('\n')[0].split(' ')[1]
    else:
        if spec.sources_dict:
            source = replace_macros(spec.sources[0], spec)
        else:
            print("WARNING: No source url in specfile.")
            return None

    source = source.replace(o_ver, n_ver)

    if re.match(r"%{.*?}", source):
        print("WARNING: Extra macros in source url which failed to be expanded.")
        return None

    if source.startswith("http") or source.startswith("ftp"):
        file_name = os.path.basename(source)
        down_cnt = 0
        while down_cnt < 2:
            down_cnt += 1
            if not subprocess.call(["timeout 15m wget -c {url} -O {name}".format(url=source,
                               name=file_name)], shell=True):
                break
        return file_name

    print("WARNING: Source url is invalid in specfile.")
    return None


def download_upstream_url(gt_api, repo, n_ver):
    """
    Download source from upstream metadata URL
    """
    upstream_yaml = gt_api.get_yaml(repo)
    if not upstream_yaml:
        return None

    rp_yaml = yaml.load(upstream_yaml, Loader=yaml.Loader)
    if rp_yaml["version_control"] == "github":
        url = "https://github.com/{rp}/archive/{nv}.tar.gz".format(rp=rp_yaml["src_repo"], nv=n_ver)
        file_name = "{rp}.{nv}.tar.gz".format(rp=repo, nv=n_ver)
        down_cnt = 0
        while down_cnt < 2:
            down_cnt += 1
            if not subprocess.call(["timeout 15m wget -c {url} -O {name}".format(url=url,
                                   name=file_name)], shell=True):
                break
        return file_name

    print("Handling {vc} is still under developing".format(vc=rp_yaml["version_control"]))
    return None


def update_ver_check(repo, o_ver, n_ver):
    """
    Update version check for upgraded package
    """
    ver_type = version_recommend.VersionType()
    if ver_type.compare(n_ver, o_ver) == 1:
        result = True
    else:
        print("WARNING: Update failed >> [{pkg}: current_ver:{c_ver}, upgrade_ver:{u_ver}]".format(
              pkg=repo, c_ver=o_ver, u_ver=n_ver))
        result = False
    return result


def fork_clone_repo(gt_api, repo, branch):
    """
    Fork repo from src-openEuler to private repository, then clone it to local
    """
    if not gt_api.fork_repo(repo):
        print("WARNING: The repo of {pkg} seems to have been forked.".format(pkg=repo))

    name = gt_api.token["user"]
    while True:
        if os.path.exists(repo):
            shutil.rmtree(repo, ignore_errors=True)
        if subprocess.call(["git", "clone", "git@gitee.com:{user}/{pkg}".format(user=name,
                           pkg=repo)]):
            time.sleep(1)
            continue
        os.chdir(repo)
        if subprocess.call(["git", "checkout", "{br}".format(br=branch)]):
            os.chdir(os.pardir)
            time.sleep(1)
        else:
            os.chdir(os.pardir)
            break


def download_src(gt_api, pkg, spec, o_ver, n_ver):
    """
    Download source code for upgraded package
    """
    os.chdir(pkg)
    source_file = download_source_url(pkg, spec, o_ver, n_ver)
    if source_file:
        print(source_file)
        result = True
    else:
        source_file = download_upstream_url(gt_api, pkg, n_ver)
        if source_file:
            print(source_file)
            result = True
        else:
            print("WARNING: Failed to download the latest source code.")
            os.chdir(os.pardir)
            result = False
    return result


def create_spec(repo, spec_str, o_ver, n_ver, src_fn=None):
    """
    Create new spec file for upgraded package
    """
    os.rename("{}.spec".format(repo), "{}-old.spec".format(repo))
    file_spec = open(repo + ".spec", "w")
    in_changelog = False
    for line in spec_str.splitlines():
        if line.startswith("Release:"):
            file_spec.write(re.sub(r"\d+", "1", line) + "\n")
            continue
        if line.startswith("Source:") or line.startswith("Source0:"):
            if src_fn:
                file_spec.write("Source:	{src_fn}\n".format(src_fn=src_fn).replace(o_ver, n_ver))
            else:
                file_spec.write(line.replace(o_ver, n_ver) + "\n")
            continue
        if not in_changelog:
            line = line.replace(o_ver, n_ver)
        file_spec.write(line + "\n")

        if line.startswith("%changelog"):
            in_changelog = True
            cur_date = datetime.date.today()
            file_spec.write(cur_date.strftime("* %a %b %d %Y SimpleUpdate Robot <tc@openeuler.org>"\
                                              " - {ver}-1\n").format(ver=n_ver))
            file_spec.write("- Upgrade to version {ver}\n".format(ver=n_ver))
            file_spec.write("\n")
    file_spec.close()
    os.chdir(os.pardir)


def build_pkg(u_pkg, u_branch):
    """
    Auto build upgrade pkg on obs
    """
    if u_branch == "master":
        project = "openEuler:Mainline"
    elif u_branch == "openEuler-20.03-LTS":
        project = "openEuler:20.03:LTS"
    else:
        print("WARNING: Please check branch to be upgrade.")
        sys.exit(1)

    subprocess.call(["osc", "branch", "{prj}".format(prj=project), "{pkg}".format(pkg=u_pkg)])

    user_info = subprocess.getoutput(["osc user"])
    user = user_info.split(':')[0]
    subprocess.call(["osc", "co", "home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=project,
                                                                           pkg=u_pkg)])

    if os.path.isdir("home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=project, pkg=u_pkg)):
        os.chdir("home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=project, pkg=u_pkg))
    else:
        print("WARNING: {repo} of {br} may not exist on OBS.".format(repo=u_pkg, br=u_branch))
        return False

    for file_name in os.listdir("./"):
        if file_name.startswith("."):
            continue
        try:
            os.remove(file_name)
        except OSError:
            shutil.rmtree(file_name, ignore_errors=True)

    subprocess.call(["cp ../../{pkg}/* .".format(pkg=u_pkg)], shell=True)
    if subprocess.call(["osc", "build", "standard_aarch64"]):
        result = False
    else:
        result = True
    os.chdir("../../")
    return result


def push_create_pr_issue(gt_api, u_pkg, o_ver, u_ver, u_branch):
    """
    Auto push update repo, create upgrade PR and issue.
    """
    os.chdir(u_pkg)
    subprocess.call(["git rm *{old_ver}.* -rf".format(old_ver=o_ver)], shell=True)
    os.remove("{}-old.spec".format(u_pkg))
    subprocess.call(["git add *"], shell=True)
    subprocess.call(["git commit -m \"upgrade {pkg} to {ver}\"".format(pkg=u_pkg, ver=u_ver)],
                    shell=True)
    subprocess.call(["git push origin"], shell=True)
    gt_api.create_pr(u_pkg, u_ver, u_branch)
    gt_api.create_issue(u_pkg, u_ver, u_branch)
    os.chdir(os.pardir)


def auto_update_pkg(gt_api, u_pkg, u_branch, u_ver=None):
    """
    Auto upgrade based on given branch for single package
    """
    print("\n------------------------Updating {}------------------------".format(u_pkg))
    spec_str = gt_api.get_spec(u_pkg, u_branch)
    if not spec_str:
        print("WARNING: {pkg}.spec can't be found on the {br} branch.".format(
            pkg=u_pkg, br=u_branch))
        return
    pkg_spec = Spec.from_string(spec_str)
    pkg_ver = replace_macros(pkg_spec.version, pkg_spec)

    if not u_ver:
        pkg_tags = oa_upgradable.get_ver_tags(gt_api, u_pkg)
        if pkg_tags is None:
            return
        ver_rec = version_recommend.VersionRecommend(pkg_tags, pkg_ver, 0)

        if u_branch == "master":
            u_ver = ver_rec.latest_version
        elif re.search(r"LTS", u_branch):
            u_ver = ver_rec.maintain_version
        else:
            print("WARNING: Auto-upgrade current not support for {} branch.".format(u_branch))
            return

    if update_ver_check(u_pkg, pkg_ver, u_ver):
        fork_clone_repo(gt_api, u_pkg, u_branch)

        if not download_src(gt_api, u_pkg, pkg_spec, pkg_ver, u_ver):
            return

        create_spec(u_pkg, spec_str, pkg_ver, u_ver)

        if len(pkg_spec.patches) >= 1:
            print("WARNING: {repo} has multiple patches, please analyse it.".format(repo=u_pkg))
            return

        if not build_pkg(u_pkg, u_branch):
            return

        push_create_pr_issue(gt_api, u_pkg, pkg_ver, u_ver, u_branch)


def auto_update_repo(gt_api, u_repo, u_branch):
    """
    Auto upgrade based on given branch for packages in given repository
    """
    try:
        repo_yaml = open(os.path.join(os.getcwd(), "{repo}.yaml".format(repo=u_repo)))
    except FileNotFoundError:
        print("WARNING: {repo}.yaml can't be found in current working directory.".format(
              repo=u_repo))
        repo_yaml = gt_api.get_community(u_repo)
        if not repo_yaml:
            print("WARNING: {repo}.yaml in community is empty.".format(repo=u_repo))
            sys.exit(1)

    pkg_info = yaml.load(repo_yaml, Loader=yaml.Loader)
    pkg_list = pkg_info.get("repositories")
    for pkg in pkg_list:
        pkg_name = pkg.get("name")
        u_ver = pkg.get("u_ver")
        auto_update_pkg(gt_api, pkg_name, u_branch, u_ver)


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("repo_pkg", type=str, help="The repository or package to be upgraded")
    pars.add_argument("branch", type=str, help="The branch that upgrade based")
    pars.add_argument("-u", "--update", type=str, help="Auto upgrade for packages in repository "\
                      "or single package", choices=["repo", "pkg"])
    pars.add_argument("-n", "--new_version", type=str, help="The upgrade version of package.")
    pars.add_argument("-d", "--download", help="Download upstream source code", action="store_true")
    pars.add_argument("-s", "--create_spec", help="Create spec file", action="store_true")
    pars.add_argument("-fc", "--fork_then_clone", help="Fork src-openeuler repo, then "\
                      "clone to local", action="store_true")
    pars.add_argument("-b", "--build_pkg", help="Build package in local", action="store_true")
    pars.add_argument("-p", "--push_create_pr_issue", help="Push update repo, create "\
                      "PR and issue", action="store_true")
    args = pars.parse_args()

    user_gitee = gitee.Gitee()

    if args.update:
        if args.update == "repo":
            auto_update_repo(user_gitee, args.repo_pkg, args.branch)
        else:
            auto_update_pkg(user_gitee, args.repo_pkg, args.branch, args.new_version)
    else:
        spec_string = user_gitee.get_spec(args.repo_pkg, args.branch)
        if not spec_string:
            print("WARNING: {pkg}.spec can't be found on the {br} branch.".format(
                  pkg=args.repo_pkg, br=args.branch))
            sys.exit(1)
        spec_file = Spec.from_string(spec_string)
        cur_version = replace_macros(spec_file.version, spec_file)

        if args.fork_then_clone:
            fork_clone_repo(user_gitee, args.repo_pkg, args.branch)

        if args.download or args.create_spec or args.push_create_pr_issue:
            if not args.new_version:
                print("Please specify the upgraded version of the {}".format(args.repo_pkg))
                sys.exit(1)
            elif not update_ver_check(args.repo_pkg, cur_version, args.new_version):
                sys.exit(1)

        if args.download:
            if not download_src(user_gitee, args.repo_pkg, spec_file, cur_version,
                                args.new_version):
                sys.exit(1)

        if args.create_spec:
            create_spec(args.repo_pkg, spec_string, cur_version, args.new_version)

        if len(spec_file.patches) >= 1:
            print("WARNING: {} has multiple patches, please analyse it.".format(args.repo_pkg))
            sys.exit(1)

        if args.build_pkg:
            if not build_pkg(args.repo_pkg, args.branch):
                sys.exit(1)

        if args.push_create_pr_issue:
            push_create_pr_issue(user_gitee, args.repo_pkg, cur_version, args.new_version,
                                 args.branch)
