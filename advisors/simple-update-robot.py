#!/usr/bin/python3
"""
This is a robot to do package upgrade automation
Expected process:
 1. get URL to download updated version
 2. Change Version to new one
 3. Change Source or Source0 if needed
 4. Update %changelog
 5. try rpmbuild -bb (not yet)
 6. fork on gitee and clone to local
 7. git add, git commit, git push (manually now)
 8. PR on gitee
"""

from pyrpm.spec import Spec, replace_macros
import yaml
import argparse
import gitee
import sys
import subprocess
import os.path
import re
import time
import datetime

import oa_upgradable
import version_recommend


def download_source_url(spec, o_ver, n_ver):
    """
    Download source file from Source or Source0 URL
    """
    source = replace_macros(spec.sources[0], spec).replace(o_ver, n_ver) 
    if re.match(r"%{.*?}", source):
        print("WARNING: Extra macros in URL which failed to be expanded")
        return False
    elif source.startswith("http") or source.startswith("ftp"):
        fn = os.path.basename(source)
        for time in range(2):
            if subprocess.call(["curl", "-m", "600", "-L", source, "-o", fn]):
                continue
            else:
                break
        return fn
    else:
        print("WARNING: Not valid URL for Source code")
        return False


def download_upstream_url(gt, repo, n_ver):
    """
    Download source from upstream metadata URL
    """
    upstream_yaml = gt.get_yaml(repo)
    if not upstream_yaml:
        return False

    rp_yaml = yaml.load(upstream_yaml, Loader=yaml.Loader)
    if rp_yaml["version_control"] == "github":
        url = "https://github.com/{rp}/archive/{nv}.tar.gz".format(rp=rp_yaml["src_repo"], nv=n_ver)     
        fn = "{rp}.{nv}.tar.gz".format(rp=repo, nv=n_ver)
        for time in range(2):
            if subprocess.call(["curl", "-m", "600", "-L", url, "-o", fn]):
                continue
            else:
                break
        return fn
    else:
        print("Handling {vc} is still under developing".format(vc=rp_yaml["version_control"]))
        return False


def update_ver_check(repo, o_ver, n_ver):
    """
    Update version check for upgraded package
    """
    ver_type = version_recommend.VersionType()
    if(ver_type.compare(n_ver, o_ver) == 1):
        return True
    else:
        print("WARNING: Update failed >> [{pkg}: current_ver:{cur_ver}, upgraded_ver:{upd_ver}]".format(
            pkg=repo, cur_ver=o_ver, upd_ver=n_ver))
        return False


def fork_clone_repo(gt, repo, br):
    """
    Fork repo from src-openEuler to private repository, then clone it to local
    """
    if not gt.fork_repo(repo):
        print("WARNING: The repo of {pkg} seems to have been forked.".format(pkg=repo))
    
    name = gt.token["user"]
    while True:
        subprocess.call(["rm", "-rf", "{pkg}".format(pkg=repo)])
        subprocess.call(["git", "clone", "git@gitee.com:{user}/{pkg}".format(user=name, pkg=repo)])
        os.chdir(repo)
        if subprocess.call(["git", "checkout", "{branch}".format(branch=br)]):
            os.chdir(os.pardir)
            time.sleep(1)
        else:
            os.chdir(os.pardir)
            break


def download_src(gt, spec, o_ver, n_ver):
    """
    Download source code for upgraded package
    """
    os.chdir(replace_macros(spec.name, spec))
    source_file = download_source_url(spec, o_ver, n_ver)
    if source_file:
        print(source_file)
        return True
    else:
        source_file = download_upstream_url(gt, spec.name, n_ver)
        if source_file:
            print(source_file)
            return True
        else:
            print("WARNING: Failed to download the latest source code.")
            os.chdir(os.pardir)
            return False


def create_spec(repo, spec_str, o_ver, n_ver, src_fn=None):
    """
    Create new spec file for upgraded package
    """
    fn = open(repo + "_old.spec", "w")
    fn.write(spec_str)
    fn.close()
    fn = open(repo + ".spec", "w")
    in_changelog = False
    for l in spec_str.splitlines():
        if l.startswith("Release:"):
            fn.write(re.sub(r"\d+", "1", l) + "\n")
            continue
        if l.startswith("Source:") or l.startswith("Source0:"):
            if src_fn:
                fn.write("Source:	{src_fn}\n".format(src_fn=src_fn).replace(o_ver, n_ver))
            else:
                fn.write(l.replace(o_ver, n_ver) + "\n")
            continue
        if not in_changelog:
            nl = l.replace(o_ver, n_ver)
        else:
            nl = l
        fn.write(nl + "\n")

        if nl.startswith("%changelog"):
            in_changelog = True
            d = datetime.date.today()
            fn.write(d.strftime("* %a %b %d %Y SimpleUpdate Robot <tc@openeuler.org> - {ver}-1\n").format(ver=n_ver))
            fn.write("- Upgrade to version {ver}\n".format(ver=n_ver))
            fn.write("\n")
    fn.close()
    os.chdir(os.pardir)


def build_pkg(u_pkg, u_branch):
    """
    Auto build upgrade pkg on obs
    """
    build_result = True
    if (u_branch == "master"):
        project = "openEuler:Mainline"
    elif (u_branch == "openEuler-20.03-LTS"):
        project = "openEuler:20.03:LTS"
    else:
        print("WARNING: Please check branch to be upgrade.")
        sys.exit(1)

    subprocess.call(["osc", "branch", "{prj}".format(prj=project), "{pkg}".format(pkg=u_pkg)])
    user_info = subprocess.getoutput(["osc user"])
    user = user_info.split(':')[0]
    subprocess.call(["osc", "co", "home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=project, pkg=u_pkg)])
    os.chdir("home:{usr}:branches:{prj}/{pkg}".format(usr=user, prj=project, pkg=u_pkg))
    subprocess.call(["rm * -rf"], shell=True)
    subprocess.call(["cp ../../{pkg}/* .".format(pkg=u_pkg)], shell=True)
    if subprocess.call(["osc", "build", "standard_aarch64"]):
        build_result = False
    os.chdir("../../")
    return build_result


def push_create_pr_issue(gt, u_pkg, o_ver, u_ver, u_branch):
    """
    Auto push update repo, create upgrade PR and issue.
    """
    os.chdir(u_pkg)
    subprocess.call(["git rm *{old_ver}.* -rf".format(old_ver=o_ver)], shell=True)
    subprocess.call(["rm *_old.spec -f"], shell=True)
    subprocess.call(["git add *"], shell=True)
    subprocess.call(["git commit -m \"upgrade {pkg} to {ver}\"".format(pkg=u_pkg, ver=u_ver)], shell=True)
    subprocess.call(["git push origin"], shell=True)
    gt.create_pr(gt.token["user"], u_pkg, u_ver, u_branch)
    gt.create_issue(u_pkg, u_ver, u_branch)
    os.chdir(os.pardir)


def auto_update_pkg(gt, u_pkg, u_branch, u_ver=None):
    """
    Auto upgrade based on given branch for single package
    """
    spec_str = gt.get_spec(u_pkg, u_branch)
    if not spec_str:
        print("WARNING: {pkg}.spec can't be found on the {br} branch.".format(
            pkg=u_pkg, br=u_branch))
        sys.exit(1)
    pkg_spec = Spec.from_string(spec_str)
    pkg_ver = replace_macros(pkg_spec.version, pkg_spec)
    
    if (u_branch == "master"):
        pkg_tags = oa_upgradable.get_ver_tags(gt, u_pkg)
        if pkg_tags is None:
            sys.exit(1)
        ver_rec = version_recommend.VersionRecommend(pkg_tags, pkg_ver, 0)
        u_ver = ver_rec.latest_version
    elif re.search(r"LTS", u_branch):
        if not u_ver:
            print("WARNING: Please specify upgrade version in LTS upgrade.")
            sys.exit(1)
    else:
        print("WARNING: Please check branch to upgrade.")
        sys.exit(1)
    
    fork_clone_repo(gt, u_pkg, u_branch)

    if not update_ver_check(u_pkg, pkg_ver, u_ver):
        sys.exit(1)

    if not download_src(gt, pkg_spec, pkg_ver, u_ver):
        sys.exit(1)

    create_spec(u_pkg, spec_str, pkg_ver, u_ver)
    
    if len(pkg_spec.patches) >= 1:
        print("WARNING: {repo} has multiple patches, please analyse it.".format(repo=u_pkg))
        sys.exit(1)
    
    if not build_pkg(u_pkg, u_branch):
        sys.exit(1)

    push_create_pr_issue(gt, u_pkg, pkg_ver, u_ver, u_branch)


def auto_update_repo(gt, u_repo, u_branch):
    """
    Auto upgrade based on given branch for packages in given repository
    """
    if (u_branch == "master"):
        repo_yaml = gt.get_community(u_repo)
        if not repo_yaml:
            print("WARNING: {repo}.yaml in community is empty.".format(repo=u_repo))
            sys.exit(1)
    elif re.search(r"LTS", u_branch):
        try:
            repo_yaml = open(os.path.join(os.getcwd(), "{repo}.yaml".format(repo=u_repo)))
        except FileNotFoundError:
            print("WARNING: {repo}.yaml can't be found in current working directory.".format(repo=u_repo))
            sys.exit(1)
    else:
        print("WARNING: Please check branch to upgrade.")
        sys.exit(1)

    pkg_info = yaml.load(repo_yaml, Loader=yaml.Loader)
    pkg_list = pkg_info.get("repositories")
    for pkg in pkg_list:
        pkg_name = pkg.get("name")
        print("\n------------------------Updating " + pkg_name + "------------------------")
        spec_str = gt.get_spec(pkg_name, u_branch)
        if not spec_str:
            print("WARNING: {pkg}.spec can't be found on the {br} branch. ".format(
                pkg=pkg_name, br=u_branch))
            continue
        pkg_spec = Spec.from_string(spec_str)
        pkg_ver = replace_macros(pkg_spec.version, pkg_spec)
        
        if (u_branch == "master"):
            pkg_tags = oa_upgradable.get_ver_tags(gt, pkg_name)
            if pkg_tags is None:
                continue
            ver_rec = version_recommend.VersionRecommend(pkg_tags, pkg_ver, 0)
            u_ver = ver_rec.latest_version
        else:
            u_ver = pkg.get("u_ver")

        fork_clone_repo(gt, pkg_name, u_branch)

        if not update_ver_check(pkg_name, pkg_ver, u_ver):
            continue

        if not download_src(gt, pkg_spec, pkg_ver, u_ver):
            continue

        create_spec(pkg_name, spec_str, pkg_ver, u_ver)
        
        if len(pkg_spec.patches) >= 1:
            print("WARNING: {repo} has multiple patches, please analyse it.".format(repo=pkg_name))
            continue
        
        if not build_pkg(pkg_name, u_branch):
            continue
        
        push_create_pr_issue(gt, pkg_name, pkg_ver, u_ver, u_branch)


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("repo_pkg", type=str, help="The repository or package to be upgraded")
    pars.add_argument("branch", type=str, help="The branch that upgrade based")
    pars.add_argument("-u", "--update", type=str, help="Auto upgrade for packages in repository or single package",
            choices=["repo", "pkg"])
    pars.add_argument("-n", "--new_version", type=str, help="New upstream version of package will be upgrade to")
    pars.add_argument("-d", "--download", help="Download upstream source code", action="store_true")
    pars.add_argument("-s", "--create_spec", help="Create spec file", action="store_true")
    pars.add_argument("-fc", "--fork_then_clone", help="Fork src-openeuler repo into users, then clone to local",
            action="store_true")
    pars.add_argument("-b", "--build_pkg", help="Build package in local", action="store_true")
    pars.add_argument("-pcpi", "--push_create_pr_issue", help="Push update repo, create PR and issue", action="store_true")
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
            print("WARNING: {pkg}.spec can't be found on the {br} branch. ".format(pkg=args.repo_pkg, br=args.branch))
            sys.exit(1)
        spec_file = Spec.from_string(spec_string)
        cur_version = replace_macros(spec_file.version, spec_file)

        if args.fork_then_clone:
            fork_clone_repo(user_gitee, args.repo_pkg, args.branch)

        if args.download or args.create_spec or args.push_create_pr_issue:
            if not args.new_version:
                print("Please specify the upgraded version of the {repo}".format(repo=args.repo_pkg))
                sys.exit(1)
            elif not update_ver_check(args.repo_pkg, cur_version, args.new_version):
                sys.exit(1)

        if args.download:
            if not download_src(user_gitee, spec_file, cur_version, args.new_version):
                sys.exit(1)

        if args.create_spec:
            create_spec(args.repo_pkg, spec_string, cur_version, args.new_version)
        
        if len(spec_file.patches) >= 1:
            print("WARNING: {repo} has multiple patches, please analyse it.".format(repo=args.repo_pkg))
            sys.exit(1)
        
        if args.build_pkg:
            if not build_pkg(args.repo_pkg, args.branch):
                sys.exit(1)

        if args.push_create_pr_issue:
            push_create_pr_issue(user_gitee, args.repo_pkg, cur_version, args.new_version, args.branch)
