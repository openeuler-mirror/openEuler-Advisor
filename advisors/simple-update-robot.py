#!/usr/bin/python3
"""
This is a robot to do package upgrade automation
Expected process:
 1. get URL to download updated version
 2. Change Version to new one
 3. Change Source or Source0 if needed
 4. Update %changelog
 5. try rpmbuild -bb (not yet)
 6. fork on gitee
 7. git clone, git add, git commit, git push (manually now)
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
import datetime
import version_recommend

def download_source_url(spec, o_ver, n_ver):
    """
    Download source file from Source or Source0 URL
    """
    source = replace_macros(spec.sources[0], spec).replace(o_ver, n_ver) 
    if re.match(r"%{.*?}", source):
        print("Extra macros in URL which failed to be expanded")
        return False
    elif source.startswith("http") or source.startswith("ftp"):
        fn = os.path.basename(source)
        subprocess.call(["curl", "-L", source, "-o", fn])
        return fn
    else:
        print("Not valid URL for Source code")
        return False


def download_upstream_url(gt, repo, n_ver):
    """
    Download source from upstream metadata URL
    """
    upstream_yaml = gt.get_yaml(repo)
    if not upstream_yaml:
        return False

    rp_yaml = yaml.loads(upstream_yaml, Loader=yaml.Loader)
    if rp_yaml["version_control"] == "github":
        url = "https://github.com/{rp}/archive/{nv}.tar.gz".format(rp=rp_yaml["src_repo"], nv=n_ver)     
        fn = "{rp}.{nv}.tar.gz".format(rp=repo, nv=n_ver)
        subprocess.call(["curl", "-L", url, "-o", fn])
        return fn
    else:
        print("Handling {vc} is still under developing".format(vc=rp_yaml["version_control"]))
        return False


def create_spec(repo, spec_str, o_ver, n_ver, src_fn=None):
    """
    Create new spec file for upgraded package
    """
    fn = open(repo + ".spec", "w")
    in_changelog = False
    for l in spec_str.splitlines():
        if l.startswith("Release:"):
            fn.write("Release:\t0\n")
            continue
        if l.startswith("Source:") or l.startswith("Source0:"):
            if src_fn:
                fn.write("Source:	{src_fn}\n".format(src_fn=src_fn).replace(o_ver, n_ver))
            else:
                fn.write(l.replace(o_ver, n_ver)+"\n")
            continue
        if not in_changelog:
            nl = l.replace(o_ver, n_ver)
        else:
            nl = l
        fn.write(nl + "\n")

        if nl.startswith("%changelog"):
            in_changelog = True
            d = datetime.date.today()
            fn.write(d.strftime("* %a %b %d %Y SimpleUpdate Robot <tc@openeuler.org> - {ver}-0\n").format(ver=n_ver))
            fn.write("- Update to version {ver}\n".format(ver=n_ver))
            fn.write("\n")
    fn.close()

if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("pkg", type=str, help="The package to be upgraded")
    pars.add_argument("-n", "--new_version", type=str, help="New upstream version of package will be upgrade to")
    pars.add_argument("-s", "--create_spec", help="Create spec file", action="store_true")
    pars.add_argument("-d", "--download", help="Download upstream source code", action="store_true")
    pars.add_argument("-f", "--fork", help="fork src-openeuler repo into users", action="store_true")
    pars.add_argument("-c", "--clone", help="clone privatge repo to local", action="store_true")
    pars.add_argument("-p", "--PR", help="Create upgrade PR", action="store_true")
    args = pars.parse_args()

    my_gitee = gitee.Gitee()
    my_version = version_recommend.VersionType()
    spec_string= my_gitee.get_spec(args.pkg)

    s_spec = Spec.from_string(spec_string)
    cur_ver = replace_macros(s_spec.version, s_spec)

    if args.fork:
        if not my_gitee.fork_repo(args.pkg):
            print("The repo of {pkg} seems to have been forked.".format(pkg=args.pkg))

    if args.clone:
        user=my_gitee.token["user"]
        subprocess.call(["git", "clone", "git@gitee.com:{user}/{pkg}".format(user=user, pkg=args.pkg)])
        os.chdir(args.pkg)

    if args.download:
        source_file = download_source_url(s_spec, cur_ver, args.new_version)
        if source_file:
            print(source_file)
        else:
            source_file = download_upstream_url(my_gitee, args.pkg, args.new_version)
            if source_file:
                print(source_file)
            else:
                print("Failed to download the latest source code.")
                sys.exit(1)

    if args.create_spec:
        if len(s_spec.patches) >= 1:
            print("I'm too naive to handle complicated package.")
            print("This package has multiple in-house patches.")
            sys.exit(1)
        if(my_version.compare(args.new_version, cur_ver) ==1):
            create_spec(args.pkg, spec_string, cur_ver, args.new_version)
        else:
            print("Please check version of {pkg} will upgrade to, it's current version is {version}.".format(
				pkg=args.pkg, version=cur_ver))

    if args.PR:
        my_gitee.create_pr(my_gitee.token["user"], args.pkg)
