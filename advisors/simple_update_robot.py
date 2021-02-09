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
import platform
import json
import shutil
import os.path
import datetime
import argparse
import subprocess
import tarfile
import yaml
from pyrpm.spec import Spec, replace_macros

from advisors import gitee
from advisors import oa_upgradable
from advisors import version_recommend
from advisors import match_patches
from advisors import package_type
from advisors import check_command
#import some requires about abi_check
from advisors import build_rpm_package
from advisors import check_abi
from advisors import check_conf

__NUMBER = 0
__WORK_PATH = ''

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


def download_helper(src_url, file_name=None):
    """
    Source download helper
    """
    if not file_name:
        file_name = os.path.basename(src_url)
    down_cnt = 0
    while down_cnt < 2:
        down_cnt += 1
        if not subprocess.call(["timeout 15m wget -c {url} -O {name} -q".format(url=src_url,
                                                                                name=file_name)],
                               shell=True):
            break
    return src_url


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
        return download_helper(source)

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
        return download_helper(url, file_name)

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
            pkg=repo,
            c_ver=o_ver,
            u_ver=n_ver))
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
                subprocess.call(["git", "reset", "--hard", "HEAD^"])
                subprocess.call(["git", "remote", "add", "upstream", upstream_url])
                subprocess.call(["git", "fetch", "upstream"])
                subprocess.call(["git", "merge", "upstream/{}".format(branch)])
                subprocess.call(["git", "push", "origin", "-f", "{}".format(branch)])
            os.chdir(os.pardir)
            break


def cpan_source_helper(src_name, src_url):
    """
    Help cpan packages get right source
    """
    update_file = True
    file_name = r"/root/02packages.details.txt"
    if os.path.exists(file_name):
        file_time = os.path.getctime(file_name)
        today = datetime.date.today()
        today_time = time.mktime(today.timetuple())
        if file_time > today_time:
            update_file = False

    if update_file:
        url = "https://www.cpan.org/modules/02packages.details.txt.gz"
        subprocess.call(["wget -P /root {}".format(url)], shell=True)
        if subprocess.call(["gzip -f -d ~/{}".format(os.path.basename(url))], shell=True):
            print("WARNING: Please check validity of {}".format(url))
            return

    with open(file_name, "r") as details_file:
        for line in details_file.readlines():
            if re.search(r'/{}-\d+'.format(src_name), line):
                base_url = "https://cpan.metacpan.org/authors/id/"
                new_url = base_url + line.split(" ")[-1].rstrip("\n")
                src_file = os.path.basename(src_url)
                new_url.replace(os.path.basename(new_url), src_file)
                download_helper(new_url)
                old_path = src_url.strip(src_file)
                new_path = new_url.strip(src_file)
                subprocess.call(["grep -lr {old} | xargs sed -i \'s#{old}#{new}#g\'"
                                 .format(old=old_path, new=new_path)],
                                shell=True)
                break
    return


def download_src(gt_api, pkg, spec, o_ver, n_ver):
    """
    Download source code for upgraded package
    """
    os.chdir(pkg)
    source = download_source_url(gt_api, pkg, spec, o_ver, n_ver)
    if source:
        print(source)
        result = True
    else:
        source = download_upstream_url(gt_api, pkg, n_ver)
        if source:
            print(source)
            result = True
        else:
            print("WARNING: Failed to download the latest source code.")
            os.chdir(os.pardir)
            result = False

    repo_yaml = gt_api.get_yaml(pkg)
    pkg_info = yaml.load(repo_yaml, Loader=yaml.Loader)
    if result and pkg_info["version_control"] == "metacpan":
        if not tarfile.is_tarfile(os.path.basename(source)):
            cpan_source_helper(pkg_info["src_repo"], source)
    return result


def create_spec(gt_api, repo, o_ver, n_ver):
    """
    Create new spec file for upgraded package
    """
    spec_path = get_spec_path(gt_api, repo)
    with open(spec_path, "r") as spec_file:
        spec_str = spec_file.read()

    pkg_spec = Spec.from_string(spec_str)

    if len(pkg_spec.patches) >= 1:
        patch_match = match_patches.patches_match(gt_api, repo, o_ver, n_ver)

    os.rename(spec_path, "{}.old".format(spec_path))
    file_spec = open(spec_path, "w")

    in_changelog = False
    patch_num_list = []
    patch_dict = {}

    for line in spec_str.splitlines():
        if line.startswith("Release:"):
            file_spec.write(re.sub(r"\d+", "1", line) + "\n")
            continue

        if line.startswith("Source:") or line.startswith("Source0:"):
            file_spec.write(line.replace(o_ver, n_ver) + "\n")
            continue

        if line.startswith("Patch") and patch_match:
            patch_dict["line"] = replace_macros(line, pkg_spec)
            patch_dict["pre_name"] = patch_dict["line"].split(":", 1)[1].strip()
            if patch_dict["pre_name"] in patch_match:
                patch_dict["pre_tag"] = patch_dict["line"].split(":", 1)[0].strip()
                patch_dict["pre_num"] = re.findall(r"\d+\.?\d*", patch_dict["pre_tag"])
                patch_num_list.append(patch_dict["pre_num"])
                continue

        if line.startswith("%patch") and patch_match:
            if patch_num_list:
                patch_dict["ply_tag"] = line.split(" ", 1)[0].strip()
                patch_dict["ply_num"] = re.findall(r"\d+\.?\d*", patch_dict["ply_tag"])
                if patch_dict["ply_num"] in patch_num_list:
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

    subprocess.call(["osc", "rm", "_service"])
    subprocess.call(["osc", "up", "-S"])
    subprocess.call(["for file in `ls _service:*`;" + "do newfile=${file##*:};" +
                     "mv -v $file $newfile;done"], shell=True)

    #Build old version
    if 'aarch64' in platform.machine():
        standard = 'standard_aarch64'
        standard_path = 'standard_aarch64-aarch64'
    else:
        standard = 'standard_x86_64'
        standard_path = 'standard_x86_64-x86_64'

    if subprocess.call(["osc", "build", '--no-verify', standard, "--clean"]):
        result = False
    else:
        result = True

    rpmbuildpath = "/var/tmp/build-root/{path}/home/abuild/rpmbuild/RPMS".format(path=standard_path)
    oldrpmpath = "/root/oldrpms"
    #Copy rpms to oldrpmpath from rpmbuildpath
    copyrpms(rpmbuildpath, oldrpmpath)

    #Build update version
    subprocess.call(["cp ../../{pkg}/* .".format(pkg=u_pkg)], shell=True)

    if subprocess.call(["osc", "build", '--no-verify', standard]):
        result = False
    else:
        result = True

    newrpmpath = "/root/newrpms"
    #Copy rpms to newrpmpath from rpmbuildpath
    copyrpms(rpmbuildpath, newrpmpath)

    os.chdir("../../")
    return result


def copyrpms(source_path, target_path):
    """
    Copy rpms to the compares path from local osc build rpms path
    """
    subprocess.call(["rm", "-rf", "{}".format(target_path)])
    subprocess.call(["mkdir {}".format(target_path)], shell=True)
    subprocess.call(["cp -r {source_path} {target_path}".format(source_path=source_path,\
                     target_path=target_path)], shell=True)


def push_create_pr_issue(gt_api, values):
    """
    Auto push update repo, create upgrade PR and issue.
    """
    u_pkg = values['repo_pkg']
    o_ver = values['cur_version']
    u_ver = values['new_version']
    u_branch = values['branch']
    check_result = values['check_result']
    global __WORK_PATH
    os.chdir(__WORK_PATH)
    os.chdir(u_pkg)
    spec_path = get_spec_path(gt_api, u_pkg)
    subprocess.call(["git rm *{old_ver}.* -rf".format(old_ver=o_ver)], shell=True)
    os.remove("{}.old".format(spec_path))
    subprocess.call(["git add *"], shell=True)
    subprocess.call(["git commit -m \"upgrade {pkg} to {ver}\"".format(pkg=u_pkg, ver=u_ver)],
                    shell=True)
    subprocess.call(["git push origin"], shell=True)
    ret_pr = gt_api.create_pr(u_pkg, u_ver, u_branch)
    if not ret_pr:
        print("WARNING: create_pr failed, please check the pr already exist ?")
        return
    number = json.loads(ret_pr)['number']
    gt_api.create_pr_comment(u_pkg, number, check_result)
    gt_api.create_issue(u_pkg, u_ver, u_branch)
    os.chdir(os.pardir)


def auto_update_pkg(gt_api, u_pkg, u_branch, u_ver=None):
    """
    Auto upgrade based on given branch for single package
    """
    print("\n------------------------Updating {}------------------------".format(u_pkg))
    spec_str = gt_api.get_spec(u_pkg, u_branch)
    if not spec_str:
        print("WARNING: Spec of {pkg} can't be found on the {br} branch.".format(
            pkg=u_pkg, br=u_branch))
        return
    pkg_spec = Spec.from_string(spec_str)
    pkg_ver = replace_macros(pkg_spec.version, pkg_spec)

    branch_info = gt_api.get_branch_info(u_branch)
    if not branch_info:
        sys.exit(1)

    if not u_ver:
        pkg_tags = oa_upgradable.get_ver_tags(gt_api, u_pkg)
        if not pkg_tags:
            print("WARNING: Can't get {} version list, stop upgrade.".format(u_pkg))
            return

        ver_rec = version_recommend.VersionRecommend(pkg_tags, pkg_ver, 0)
        if not ver_rec:
            print("WARNING: Can't get {} recommend version, stop upgrade.".format(u_pkg))
            return

        pkg_type = package_type.PackageType(u_pkg)
        if pkg_type.pkg_type == "core":
            print("WARNING: {} is core package, if need upgrade, please specify "\
                  "upgarde version for it.".format(u_pkg))
            return
        if pkg_type.pkg_type == "app":
            u_ver = ver_rec.latest_version
        else:
            if branch_info["recommend_type"] == "master":
                u_ver = ver_rec.latest_version
            else:
                u_ver = ver_rec.maintain_version
        print("version_recommen u_ver is :{}".format(u_ver))

    if update_ver_check(u_pkg, pkg_ver, u_ver):
        fork_clone_repo(gt_api, u_pkg, u_branch)

        if not download_src(gt_api, u_pkg, pkg_spec, pkg_ver, u_ver):
            return

        create_spec(gt_api, u_pkg, pkg_ver, u_ver)

        if not build_pkg(u_pkg, u_branch, branch_info["obs_prj"]):
            return

        check_rest = check_rpm_abi(u_pkg)
        values = make_values(u_pkg, pkg_ver, u_ver, u_branch, check_rest)
        push_create_pr_issue(gt_api, values)


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


def check_rpm_abi(u_pkg):
    """
    rpm check abi
    """
    old_dir = "/root/oldrpms"
    new_dir = "/root/newrpms"
    old_rpm_path = get_rpm_debug_path(u_pkg, old_dir)
    new_rpm_path = get_rpm_debug_path(u_pkg, new_dir)

    rpms = [old_rpm_path[0], new_rpm_path[0]]
    debuginfos = [old_rpm_path[1], new_rpm_path[1]]

    # check conf in old_rpm and new_rpm
    check_conf_file = check_conf.CheckConfig(old_rpm_path[0], new_rpm_path[0])
    check_conf_file.conf_check()
    ret_conf = check_conf_file.output_file
    if os.path.getsize(ret_conf) == 0:
        with open(ret_conf, 'w', encoding='utf-8') as conf_file:
            conf_file.write("Configs are same")

    print("conf result is : {}".format(ret_conf))

    # check abi in old_rpm and new_rpm
    check_abi_file = check_abi.CheckAbi()
    check_abi_file.process_with_rpm(rpms, debuginfos)

    if not os.path.exists(check_abi_file.result_output_file):
        return ""

    ret_abi = os.path.join(check_abi_file.work_path, "{}_result.txt".format(u_pkg))
    joint_abi_rest(check_abi_file.result_output_file, ret_abi)
    # check command
    ret_command = check_command.process_check_command(rpms)
    print("ret_command is : {}".format(ret_command))
    review_body = make_check_review(ret_conf, ret_command, ret_abi)
    return review_body


def get_rpm_debug_path(u_pkg, target_path):
    """
    return the rpm package path and debug package path
    """
    rpm_packages = build_rpm_package.BuildRPMPackage(u_pkg, target_path)
    rpm_path = rpm_packages.main_package_local()
    debug_packages = rpm_packages.debuginfo_package_local()
    return [rpm_path, debug_packages]


def joint_abi_rest(old_file, new_file):
    """
    Joint the abi check result, and remove duplicate information
    """
    lines_seen = set()
    if os.path.getsize(old_file) > 0:
        with open(old_file, 'r', encoding='utf-8') as oldfile:
            abi_line = oldfile.readlines()

        with open(new_file, 'w') as newfile:
            for line in abi_line:
                if line not in lines_seen:
                    if line.startswith("# Functions changed info"):
                        newfile.write(line)
                    if line.startswith("------"):
                        newfile.write(line)
                    if line.startswith("Functions changes summary:"):
                        newfile.write(line)
                    if line.startswith("Variables changes summary:"):
                        newfile.write(line)
                    lines_seen.add(line)
            newfile.write("Detailed interface changes results in check_abi of openeuler-ci-bot")


def make_check_review(ret_conf, ret_commd, ret_abi):
    """
    Summary of interface change results
    """
    review_body = """**以下为openEuler-Advistor生成的接口变更清单**"""
    chk_table_header = """<table><tr><th>编号</th><th>检查项</th><th>变更内容</th></tr>"""
    review_body += chk_table_header
    print("ret_conf is : {}".format(ret_conf))
    review_body += check_item("配置文件差异", ret_conf)
    review_body += check_item("命令差异", ret_commd)
    review_body += check_item("abi 变更差异", ret_abi)
    review_body += "</table>"
    return review_body


def check_item(check_name, check_result):
    """
    join check item as a table row
    """
    item_template = "<tr><th>{}</th><th>{}</th><th>{}</th></tr>"
    ret_str = ""
    global __NUMBER
    with open(check_result, 'r', encoding='utf-8') as ch_file:
        for line in ch_file.readlines():
            ret_str += line
    res = item_template.format(__NUMBER, check_name, ret_str)
    __NUMBER += 1
    return res


def extract_rpm_name(rpm_fullname):
    """
    取出名字部分
    :param rpm_fullname:
    :return:
    """
    try:
        rpm_name = re.match("(.*)-[0-9.]+-.*rpm", rpm_fullname)
    except NameError:
        return rpm_fullname
    else:
        return rpm_name.group(1)


def __manual_operate(gt_api, op_args):
    """
    Manual operation of this module
    """
    spec_string = gt_api.get_spec(op_args.repo_pkg, op_args.branch)
    if not spec_string:
        print("WARNING: Spec of {pkg} can't be found on the {br} branch.".format(
            pkg=op_args.repo_pkg,
            br=op_args.branch))
        sys.exit(1)
    spec_file = Spec.from_string(spec_string)
    cur_version = replace_macros(spec_file.version, spec_file)

    branch_info = gt_api.get_branch_info(op_args.branch)
    if not branch_info:
        sys.exit(1)

    if op_args.fork_then_clone:
        fork_clone_repo(gt_api, op_args.repo_pkg, op_args.branch)

    if op_args.download or op_args.create_spec or op_args.push_create_pr_issue:
        if not op_args.new_version:
            print("Please specify the upgraded version of the {}".format(op_args.repo_pkg))
            sys.exit(1)
        if not update_ver_check(op_args.repo_pkg, cur_version, op_args.new_version):
            sys.exit(1)

    if op_args.download:
        if not download_src(gt_api, op_args.repo_pkg, spec_file, cur_version,
                            op_args.new_version):
            sys.exit(1)

    if op_args.create_spec:
        create_spec(gt_api, op_args.repo_pkg, cur_version, op_args.new_version)

    if op_args.build_pkg and not build_pkg(op_args.repo_pkg, op_args.branch,
                                           branch_info["obs_prj"]):
        sys.exit(1)

    if op_args.check_rpm_abi:
        check_result = check_rpm_abi(op_args.repo_pkg)

    if op_args.push_create_pr_issue:
        values = make_values(op_args.repo_pkg, cur_version, op_args.new_version,
                             op_args.branch, check_result)
        push_create_pr_issue(gt_api, values)


def make_values(repo_pkg, cur_ver, new_ver, branch, check_result):
    """
    Make values for push_create_pr_issue
    """
    values = {}
    values["repo_pkg"] = repo_pkg
    values["cur_version"] = cur_ver
    values["new_version"] = new_ver
    values["branch"] = branch
    values["check_result"] = check_result
    return values


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
    global __WORK_PATH
    __WORK_PATH = os.getcwd()
    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)

    if args.update:
        if args.update == "repo":
            auto_update_repo(user_gitee, args.repo_pkg, args.branch)
        else:
            auto_update_pkg(user_gitee, args.repo_pkg, args.branch, args.new_version)
    else:
        __manual_operate(user_gitee, args)


if __name__ == "__main__":
    main()
