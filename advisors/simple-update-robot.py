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
        subprocess.call(["curl", "-L", source, "-o", fn])
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
        subprocess.call(["curl", "-L", url, "-o", fn])
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
            fn.write(re.sub(r"\d", "1", l) + "\n")
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


def auto_update_pkg(gt, u_branch, u_pkg):
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

    pkg_tags = oa_upgradable.get_ver_tags(gt, u_pkg)
    if pkg_tags is None:
        sys.exit(1)
    ver_rec = version_recommend.VersionRecommend(pkg_tags, pkg_ver, 0)
    rec_up_ver = ver_rec.latest_version

    fork_clone_repo(gt, u_pkg, u_branch)

    if not update_ver_check(u_pkg, pkg_ver, rec_up_ver):
        sys.exit(1)

    if not download_src(gt, pkg_spec, pkg_ver, rec_up_ver):
        sys.exit(1)

    create_spec(u_pkg, spec_str, pkg_ver, rec_up_ver)
    
    if len(pkg_spec.patches) >= 1:
        print("WARNING: {repo} has multiple patches, please analyse it.".format(repo=u_pkg))
        sys.exit(1)


def auto_update_repo(gt, u_branch, u_repo):
    """
    Auto upgrade based on given branch for packages in given repository
    """
    repo_yaml = gt.get_community(u_repo)
    if not repo_yaml:
        print("WARNING: {repo}.yaml in community is empty.".format(repo=u_repo))
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

        pkg_tags = oa_upgradable.get_ver_tags(gt, pkg_name)
        if pkg_tags is None:
            continue
        ver_rec = version_recommend.VersionRecommend(pkg_tags, pkg_ver, 0)
        rec_up_ver = ver_rec.latest_version

        fork_clone_repo(gt, pkg_name, u_branch)

        if not update_ver_check(pkg_name, pkg_ver, rec_up_ver):
            continue

        if not download_src(gt, pkg_spec, pkg_ver, rec_up_ver):
            continue

        create_spec(pkg_name, spec_str, pkg_ver, rec_up_ver)
        
        if len(pkg_spec.patches) >= 1:
            print("WARNING: {repo} has multiple patches, please analyse it.".format(repo=pkg_name))
            continue


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("repo_pkg", type=str, help="The repository or package to be upgraded")
    pars.add_argument("branch", type=str, help="The branch that upgrade based")
    pars.add_argument("-u", "--update", type=str, help="Auto upgrade for packages in repository or single package",
            choices=["repo", "pkg"])
    pars.add_argument("-n", "--new_version", type=str, help="New upstream version of package will be upgrade to")
    pars.add_argument("-s", "--create_spec", help="Create spec file", action="store_true")
    pars.add_argument("-d", "--download", help="Download upstream source code", action="store_true")
    pars.add_argument("-fc", "--fork_then_clone", help="Fork src-openeuler repo into users, then clone to local",
            action="store_true")
    pars.add_argument("-p", "--PR", help="Create upgrade PR", action="store_true")
    args = pars.parse_args()
    
    user_gitee = gitee.Gitee()

    if args.update:
        if not args.branch == "master":
            print("WARNING: Now only support master version auto-upgrade.")
            print("WARNING: You can try manually upgrade with specified version, command as follow:")
            print("python3 simple-update-robot.py {pkg} {br} -fc -d -s -n upgrade_ver".format(
                pkg=args.repo_pkg, br=args.branch))
            sys.exit(1)
        if args.update == "repo":
            auto_update_repo(user_gitee, args.branch, args.repo_pkg)
        else:
            auto_update_pkg(user_gitee, args.branch, args.repo_pkg)
    else:
        spec_string = user_gitee.get_spec(args.repo_pkg, args.branch)
        if not spec_string:
            print("WARNING: {pkg}.spec can't be found on the {br} branch. ".format(pkg=args.repo_pkg, br=args.branch))
            sys.exit(1)
        spec_file = Spec.from_string(spec_string)
        cur_version = replace_macros(spec_file.version, spec_file)

        if args.fork_then_clone:
            fork_clone_repo(user_gitee, args.repo_pkg, args.branch)

        if args.download or args.create_spec:
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

        if args.PR:
            user_gitee.create_pr(user_gitee.token["user"], args.repo_pkg)
