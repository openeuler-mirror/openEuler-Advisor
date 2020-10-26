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

from advisors import gitee
from advisors import oa_upgradable
from advisors import version_recommend
from advisors import match_patches


def get_spec_path(gt_api, pkg):
    """
    Get specfile path in repository
    """
    excpt = gt_api.get_spec_exception(pkg)
    if excpt:
        spec_path = os.path.join(excpt["dir"], excpt["file"])
    else:
        spec_path = "./{}.spec".format(pkg)
    return spec_path


def download_source_url(gt_api, pkg, spec, o_ver, n_ver):
    """
    Download source file from Source or Source0 URL
    """
    spec_path = get_spec_path(gt_api, pkg)
    source_str = subprocess.check_output(["spectool -S {}".format(spec_path)],
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
    fork_existed = False
    if not gt_api.fork_repo(repo):
        fork_existed = True
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
            if fork_existed:
                upstream_url = "https://gitee.com/src-openeuler/{}.git".format(repo)
                subprocess.call(["git", "remote", "add", "upstream", upstream_url])
                subprocess.call(["git", "fetch", "upstream"])
                subprocess.call(["git", "merge", "upstream/{}".format(branch)])
                subprocess.call(["git", "push", "origin", "{}".format(branch)])
            os.chdir(os.pardir)
            break


def download_src(gt_api, pkg, spec, o_ver, n_ver):
    """
    Download source code for upgraded package
    """
    os.chdir(pkg)
    source_file = download_source_url(gt_api, pkg, spec, o_ver, n_ver)
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


def modify_patch(repo, pkg_spec, patch_match):
    """
    delete the patch in spec that has been merged into the new version
    """
    os.chdir(repo)
    patch_nums = []
    with open(repo + ".spec", "r") as old_file:
        lines = old_file.readlines()

    with open(repo + ".spec", "w") as new_file:
        for pre_line in lines:
            temp_line = "".join(pre_line)
            if temp_line.startswith("Patch"):
                line = replace_macros(temp_line, pkg_spec)
                patch_name = "".join(line.split(":", 1)[1].split())
                patch_num_list = "".join(line.split(":", 1)[0].split())
                patch_num = "".join(re.findall(r"\d+\.?\d*", patch_num_list))
                if patch_name in patch_match:
                    patch_nums.append(patch_num)
                    continue
                new_file.write(temp_line)
            elif temp_line.startswith("%patch"):
                if patch_nums is not None:
                    current_line_num = "".join(line.split(" ", 1)[0].split())
                    current_patch_num = "".join(re.findall(r"\d+\.?\d*", current_line_num))
                    if current_patch_num in patch_nums:
                        continue
                    new_file.write(temp_line)
            else:
                new_file.write(temp_line)
    os.chdir(os.pardir)


def create_spec(gt_api, repo, spec_str, o_ver, n_ver):
    """
    Create new spec file for upgraded package
    """
    pkg_spec = Spec.from_string(spec_str)
    spec_path = get_spec_path(gt_api, repo)
    os.rename(spec_path, "{}.old".format(spec_path))
    file_spec = open(spec_path, "w")
    in_changelog = False
    for line in spec_str.splitlines():
        if line.startswith("Release:"):
            file_spec.write(re.sub(r"\d+", "1", line) + "\n")
            continue
        if line.startswith("Source:") or line.startswith("Source0:"):
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

    if len(pkg_spec.patches) >= 1:
        os.chdir(repo)
        patch_match = match_patches.patches_match(gt_api, repo, o_ver, n_ver)
        os.chdir(os.pardir)
        if patch_match is not None:
            modify_patch(repo, pkg_spec, patch_match)


def build_pkg(u_pkg, u_branch, obs_prj):
    """
    Auto build upgrade pkg on obs
    """
    subprocess.call(["osc", "branch", "{prj}".format(prj=obs_prj), "{pkg}".format(pkg=u_pkg)])

    user_info = subprocess.getoutput(["osc user"])
    user = user_info.split(':')[0]
    subprocess.call(["osc", "co", "home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=obs_prj,
                                                                           pkg=u_pkg)])

    if os.path.isdir("home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=obs_prj, pkg=u_pkg)):
        os.chdir("home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=obs_prj, pkg=u_pkg))
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
    spec_path = get_spec_path(gt_api, u_pkg)
    subprocess.call(["git rm *{old_ver}.* -rf".format(old_ver=o_ver)], shell=True)
    os.remove("{}.old".format(spec_path))
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

    branch_info = gt_api.get_branch_info(u_branch)

    if not u_ver:
        pkg_tags = oa_upgradable.get_ver_tags(gt_api, u_pkg)
        if pkg_tags is None:
            return
        ver_rec = version_recommend.VersionRecommend(pkg_tags, pkg_ver, 0)

        if branch_info["recommend_type"] == "master":
            u_ver = ver_rec.latest_version
        else:
            u_ver = ver_rec.maintain_version

    if update_ver_check(u_pkg, pkg_ver, u_ver):
        fork_clone_repo(gt_api, u_pkg, u_branch)

        if not download_src(gt_api, u_pkg, pkg_spec, pkg_ver, u_ver):
            return

        create_spec(gt_api, u_pkg, spec_str, pkg_ver, u_ver)

        if not build_pkg(u_pkg, u_branch, branch_info["obs_prj"]):
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


def __manual_operate(gt_api, op_args):
    """
    Manual operation of this module
    """
    spec_string = gt_api.get_spec(op_args.repo_pkg, op_args.branch)
    if not spec_string:
        print("WARNING: {pkg}.spec can't be found on the {br} branch.".format(
              pkg=op_args.repo_pkg, br=op_args.branch))
        sys.exit(1)
    spec_file = Spec.from_string(spec_string)
    cur_version = replace_macros(spec_file.version, spec_file)

    branch_info = gt_api.get_branch_info(op_args.branch)

    if op_args.fork_then_clone:
        fork_clone_repo(gt_api, op_args.repo_pkg, op_args.branch)

    if op_args.download or op_args.create_spec or op_args.push_create_pr_issue:
        if not op_args.new_version:
            print("Please specify the upgraded version of the {}".format(op_args.repo_pkg))
            sys.exit(1)
        elif not update_ver_check(op_args.repo_pkg, cur_version, op_args.new_version):
            sys.exit(1)

    if op_args.download:
        if not download_src(gt_api, op_args.repo_pkg, spec_file, cur_version,
                            op_args.new_version):
            sys.exit(1)

    if op_args.create_spec:
        create_spec(gt_api, op_args.repo_pkg, spec_string, cur_version, op_args.new_version)

    if op_args.build_pkg:
        if not build_pkg(op_args.repo_pkg, op_args.branch, branch_info["obs_prj"]):
            sys.exit(1)

    if op_args.push_create_pr_issue:
        push_create_pr_issue(gt_api, op_args.repo_pkg, cur_version, op_args.new_version,
                             op_args.branch)


def main():
    """
    Main entrance for command line
    """
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
        __manual_operate(user_gitee, args)


if __name__ == "__main__":
    main()
