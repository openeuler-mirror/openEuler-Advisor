#!/usr/bin/python3
"""
This is a simple script to query that contact person for specific package
"""

import urllib
import urllib.request
import argparse
import yaml
import re

# Useful default setting
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW 64; rv:23.0) Gecko/20100101 Firefox/23.0'}
# known important information
sigs_url = "https://gitee.com/openeuler/community/raw/master/sig/sigs.yaml"
sigs_owner_url_template = "https://gitee.com/openeuler/community/raw/master/sig/{signame}/OWNERS"
specfile_url_template = "https://gitee.com/src-openeuler/{package}/raw/master/{specfile}"
specfile_exception_url = "https://gitee.com/openeuler/openEuler-Advisor/raw/master/advisors/helper/specfile_exceptions.yaml"


def get_gitee(url):
    req = urllib.request.Request(url=url, headers=headers)
    u = urllib.request.urlopen(req)
    return u.read().decode("utf-8")


def get_sigs():
    req = urllib.request.Request(url=sigs_url, headers=headers)
    u = urllib.request.urlopen(req)
    sigs = yaml.load(u.read().decode("utf-8"), Loader=yaml.Loader)
    return sigs


def get_spec(pkg, specfile):
    url = specfile_url_template.format(package=pkg, specfile=specfile)
    req = urllib.request.Request(url=url, headers=headers)
    u = urllib.request.urlopen(req)
    return u.read().decode("utf-8")


def get_spec_exception():
    req = urllib.request.Request(url=specfile_exception_url, headers=headers)
    u = urllib.request.urlopen(req)
    exps = yaml.load(u.read().decode("utf-8"), Loader=yaml.Loader)
    return exps


def get_manager_sig(pkg):
    sis_load = get_sigs()
    for sig in sis_load["sigs"]:
        for repo in sig["repositories"]:
            if repo == "src-openeuler/"+pkg:
                return sig["name"]
 

def get_sig_owners(sig_name):
    url = sigs_owner_url_template.format(signame=sig_name)
    r = get_gitee(url)
    owners = yaml.load(r, Loader=yaml.Loader)
    return owners["maintainers"]


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("pkg", type=str, help="The Package to be Queried")
    args = parser.parse_args()

    s = get_manager_sig(args.pkg)
    o = get_sig_owners(s)
    print("SIG Owner:")
    for owner in o:
        print("\t"+owner)

    exp = get_spec_exception()
    if args.pkg in exp:
        dir_name = exp[args.pkg]["dir"]
        file_name = exp[args.pkg]["file"]
        specurl = specfile_url_template.format(package=args.pkg, specfile=dir_name + "/" + file_name)
    else:
        specurl = specfile_url_template.format(package=args.pkg, specfile=args.pkg+".spec")

    spec = get_gitee(specurl)

    in_changelog = False
    emails = set()
    for line in spec.splitlines():
        if line.startswith("%changelog"):
            in_changelog = True
        if line.startswith("*") and in_changelog:
            m = re.match(r".*\d\d\d\d (.*) .*", line)
            if m is None:
                emails.add(line)
            else:
                n = m[1].split("<")
                if len(n) == 1: 
                    emails.add(n[0])
                else:
                    emails.add(n[0].strip() + " <" + n[1].strip())

    print("Package Contributor:")
    for email in emails:
        print("\t"+email)
