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
    pars.add_argument("-o", "--old_version", type=str, help="Current upstream version of package")
    pars.add_argument("-n", "--new_version", type=str, help="New upstream version of package will be upgrade to")
    pars.add_argument("-s", "--create_spec", help="Create spec file", action="store_true")
    pars.add_argument("-d", "--download", help="Download upstream source code", action="store_true")
    pars.add_argument("-f", "--fork", help="fork src-openeuler repo into users", action="store_true")
    pars.add_argument("-c", "--clone", help="clone privatge repo to local", action="store_true")
    pars.add_argument("-p", "--PR", help="Create upgrade PR", action="store_true")
    args = pars.parse_args()

    my_gitee = gitee.Gitee()
    spec_string= my_gitee.get_spec(args.pkg)

    s_spec = Spec.from_string(spec_string)

    if args.fork:
        my_gitee.fork_repo(args.pkg)

    if args.clone:
        user=my_gitee.token["user"]
        subprocess.call(["git", "clone", "git@gitee.com:{user}/{pkg}".format(user=user, pkg=args.pkg)])
        os.chdir(args.pkg)

    if args.download:
        source_file = download_source_url(s_spec, args.old_version, args.new_version)
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
        create_spec(args.pkg, spec_string, args.old_version, args.new_version)

    if args.PR:
        my_gitee.create_pr(my_gitee.token["user"], args.pkg)
