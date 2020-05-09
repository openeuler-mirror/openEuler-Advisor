#!/usr/bin/python3
"""
This is a packager bot for python modules from pypi.org
"""
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2018-2019. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: Shinwell_Hu Myeuler
# Create: 2020-05-07
# Description: provide a tool to package python module automatically
# ******************************************************************************/

import urllib
import urllib.request
from pprint import pprint
from os import path
import json
import sys
import re
import datetime
import argparse
import subprocess
import os
from pathlib import Path
# python3-wget is not default available on openEuler yet.
# import wget  

url_template = 'https://pypi.org/pypi/{pkg_name}/json'
json_file_template = '{pkg_name}.json'
name_tag_template    = 'Name:\t\tpython-{pkg_name}' 
summary_tag_template = 'Summary:\t{pkg_sum}' 
version_tag_template = 'Version:\t{pkg_ver}' 
release_tag_template = 'Release:\t1'
license_tag_template = 'License:\t{pkg_lic}' 
home_tag_template = 'URL:\t\t{pkg_home}' 
source_tag_template = 'Source0:\t{pkg_source}'

buildreq_tag_template = 'BuildRequires:\t{req}'

build_noarch = True # Usually python modules are arch independent

# TODO List
# 1. Need a reliable way to get description of module .. Partially done
# 2. requires_dist has some dependency restirction, need to present
# 3. dependency outside python (i.e. pycurl depends on libcurl) doesn't exist in pipy


def get_license(j):
    """
    By default, the license info can be achieved from json["info"]["license"]
    In rare cases it doesn't work.
    We fall back to json["info"]["classifiers"], it looks like License :: OSI Approved :: BSD Clause
    """
    if j["info"]["license"] != "":
        return j["info"]["license"]
    for k in j["info"]["classifiers"]:
        if k.startswith("License"):
            ks = k.split("::")
            return ks[2].strip()
    return ""


def get_source_url(j):
    """
    return URL for source file for the latest version
    return "" in errors
    """
    v = j["info"]["version"]
    rs = j["releases"][v]
    for r in rs:
        if r["packagetype"] == "sdist":
            return r["url"]
    return ""


def transform_module_name(n):
    """
    return module name with version restriction.
    Any string with '.' or '/' is considered file, and will be ignored
    Modules start with python- will be changed to python3- for consistency.
    """
    # remove ()
    ns = re.split("[()]", n)
    if len(ns) > 1:
        m = re.match("([<>=]+)( *)(\d.*)", ns[1])
        ns[1] = m[1] + " " + m[3]
    ns[0] = ns[0].strip()
    if ns[0].startswith("python-"):
        ns[0] = ns[0].replace("python-", "python3-")
        return " ".join(ns) 
    else:
        ns[0] = "python3-" + ns[0] 
        if ns[0].find("/") != -1 or ns[0].find(".") != -1:
            return ""
        else:
            return " ".join(ns)


def get_requires(j):
    """
    return all requires no matter if extra is required.
    """
    rs = j["info"]["requires_dist"]
    if rs is None:
        return
    for r in rs:
        idx = r.find(";")
        mod = transform_module_name(r[:idx])
        if mod != "":
            print ("Requires:\t" + mod)


def refine_requires(req):
    """
    return only requires without ';' (thus no extra)
    """
    ra = req.split(";", 1)
    #
    # Do not add requires which has ;, which is often has very complicated precondition
    #
    if (len(ra) >= 2):
        return ""
    return transform_module_name(ra[0])


def get_buildarch(j):
    """
    If this module has a prebuild package for amd64, then it is arch dependent.
    print BuildArch tag if needed.
    """
    v = j["info"]["version"]
    rs = j["releases"][v]
    for r in rs:
        if r["packagetype"] == "bdist_wheel":
            if r["url"].find("amd64") != -1:
                global build_noarch
                build_noarch = False
                return
    print("BuildArch:\tnoarch")


def get_description(j):
    """
    return description.
    Usually it's json["info"]["description"]
    If it's rst style, then only use the content for the first paragraph, and remove all tag line.
    For empty description, use summary instead.
    """
    desc = j["info"]["description"].splitlines()
    res = []
    paragraph = 0
    for d in desc:
        if len(d.strip()) == 0:
            continue
        first_char = d.strip()[0]
        ignore_line = False
        if d.strip().startswith("===") or d.strip().startswith("---"):
            paragraph = paragraph + 1
            ignore_line = True
        elif d.strip().startswith(":") or d.strip().startswith(".."):
            ignore_line = True
        if ignore_line != True and paragraph == 1:
            res.append(d)
        if paragraph >= 2:
            del res[-1]
            return "\n".join(res)
    if res != []:
        return "\n".join(res)
    elif paragraph == 0:
        return j["info"]["description"]
    else:
        return j["info"]["summary"]


def store_json(resp, pkg, spath):
    """
    save json file
    """
    fname = json_file_template.format(pkg_name=pkg)
    json_file = os.path.join(spath, fname)
    
    # if file exist, do nothing 
    if path.exists(json_file) and path.isfile(json_file):
        with open(json_file, 'r') as f:
            resp = json.load(f)
    else:
        with open(json_file, 'w') as f:
            json.dump(resp, f)


def get_pkg_json(pkg):
    """
    recieve json from pypi.org
    """
    url = url_template.format(pkg_name=pkg)

    u = urllib.request.urlopen(url)
    resp = json.loads(u.read().decode('utf-8'))

    return resp


def download_source(resp, tgtpath):
    """
    download source file from url, and save it to target path
    """
    if (os.path.exists(tgtpath) == False):
        print("download path %s does not exist\n", tgtpath)
        return False
    s_url = get_source_url(resp)
    return subprocess.call(["wget", s_url, "-P", tgtpath])


def prepare_rpm_build_env(buildroot):
    """
    prepare environment for rpmbuild
    """
    if (os.path.exists(buildroot) == False):
        print("Build Root path %s does not exist\n", buildroot)
        return False

    bpath=os.path.join(buildroot, "SPECS")
    if (os.path.exists(bpath) == False):
        os.mkdir(bpath)
    bpath=os.path.join(buildroot, "BUILD")
    if (os.path.exists(bpath) == False):
        os.mkdir(bpath)
    bpath=os.path.join(buildroot, "SOURCES")
    if (os.path.exists(bpath) == False):
        os.mkdir(bpath)
    bpath=os.path.join(buildroot, "SRPMS")
    if (os.path.exists(bpath) == False):
        os.mkdir(bpath)
    bpath=os.path.join(buildroot, "RPMS")
    if (os.path.exists(bpath) == False):
        os.mkdir(bpath)
    bpath=os.path.join(buildroot, "BUILDROOT")
    if (os.path.exists(bpath) == False):
        os.mkdir(bpath)

    return True


def installed_package(pkg):
    """
    install packages listed in build requires
    """
    print(pkg)
    ret = subprocess.call(["rpm", "-qi", pkg])
    if ret == 0:
        return True
    return False


def build_package(specfile):
    """
    build rpm package with rpmbuild
    """
    ret = subprocess.call(["rpmbuild", "-ba", specfile])
    return ret


def build_rpm(resp, buildroot):
    """
    full process to build rpm
    """
    if(prepare_rpm_build_env(buildroot) == False):
        return False

    specfile = os.path.join(buildroot, "SPECS", "python-" + resp["info"]["name"] + ".spec")
    req_list = build_spec(resp, specfile)
    for req in req_list:
        if (installed_package(req) == False):
            return req

    download_source(resp, os.path.join(buildroot, "SOURCES"))

    build_package(specfile)

    return ""


def build_spec(resp, output):
    """
    print out the spec file
    """
    tmp = sys.stdout
    if (output == ""):
        print()
    else:
        sys.stdout = open(output, 'w+')
    
    print(name_tag_template.format(pkg_name=resp["info"]["name"]))
    print(version_tag_template.format(pkg_ver=resp["info"]["version"]))
    print(release_tag_template)
    print(summary_tag_template.format(pkg_sum=resp["info"]["summary"]))
    print(license_tag_template.format(pkg_lic=get_license(resp)))
    print(home_tag_template.format(pkg_home=resp["info"]["project_urls"]["Homepage"]))
    print(source_tag_template.format(pkg_source=get_source_url(resp)))
    get_buildarch(resp)
    print("")
    get_requires(resp)
    print("")
    print("%description")
    print(get_description(resp))
    print("")
    print("%package -n python3-{name}".format(name=resp["info"]["name"]))
    print(summary_tag_template.format(pkg_sum=resp["info"]["summary"]))
    print("Provides:\tpython-" + resp["info"]["name"])
    print(buildreq_tag_template.format(req='python3-devel'))
    print(buildreq_tag_template.format(req='python3-setuptools'))

    if build_noarch == False:
        print(buildreq_tag_template.format(req='python3-cffi'))
        print(buildreq_tag_template.format(req='gcc'))
        print(buildreq_tag_template.format(req='gdb'))


    req_list=[]
    rds = resp["info"]["requires_dist"]
    if rds is not None:
        for rp in rds:
            br = refine_requires(rp)
            if (br == ""):
                continue
            print(buildreq_tag_template.format(req=br))
            name=str.lstrip(br).split(" ")
            req_list.append(name[0])

    print("%description -n python3-" + resp["info"]["name"])
    print(get_description(resp))
    print("")
    print("%package help")
    print("Summary:\tDevelopment documents and examples for {name}".format(name=resp["info"]["name"]))
    print("Provides:\tpython3-{name}-doc".format(name=resp["info"]["name"]))
    print("%description help")
    print(get_description(resp))
    print("")
    print("%prep")
    print("%autosetup -n {name}-{ver}".format(name=resp["info"]["name"], ver=resp["info"]["version"]))
    print("")
    print("%build")
    print("%py3_build")
    print("")
    print("%install")
    print("%py3_install")
    print("install -d -m755 %{buildroot}/%{_pkgdocdir}")
    print("if [ -d doc ]; then cp -arf doc %{buildroot}/%{_pkgdocdir}; fi")
    print("if [ -d docs ]; then cp -arf docs %{buildroot}/%{_pkgdocdir}; fi")
    print("if [ -d example ]; then cp -arf example %{buildroot}/%{_pkgdocdir}; fi")
    print("if [ -d examples ]; then cp -arf examples %{buildroot}/%{_pkgdocdir}; fi")
    print("pushd %{buildroot}")
    print("if [ -d usr/lib ]; then")
    print("\tfind usr/lib -type f -printf \"/%h/%f\\n\" >> filelist.lst")
    print("fi")
    print("if [ -d usr/lib64 ]; then")
    print("\tfind usr/lib64 -type f -printf \"/%h/%f\\n\" >> filelist.lst")
    print("fi")
    print("if [ -d usr/bin ]; then")
    print("\tfind usr/bin -type f -printf \"/%h/%f\\n\" >> filelist.lst")
    print("fi")
    print("if [ -d usr/sbin ]; then")
    print("\tfind usr/sbin -type f -printf \"/%h/%f\\n\" >> filelist.lst")
    print("fi")
    print("popd")
    print("mv %{buildroot}/filelist.lst .")
    print("")
    print("%files -n python3-{name} -f filelist.lst".format(name=resp["info"]["name"]))
#   print("%{python3_sitelib}/*.egg-info/")
#   print("%{python3_sitelib}/" + resp["info"]["name"])

    if build_noarch:
        print("%dir %{python3_sitelib}/*")
    else:
        print("%dir %{python3_sitearch}/*")

    print("")
    print("%files help")
    print("%{_pkgdocdir}")
    print("")
    print("%changelog")
    date_str = datetime.date.today().strftime("%a %b %d %Y")
    print("* {today} Python_Bot <Python_Bot@openeuler.org>".format(today=date_str))
    print("- Package Spec generated")

    sys.stdout = tmp

    return req_list


if __name__ == "__main__":

    dft_root_path=os.path.join(str(Path.home()), "rpmbuild")

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--spec", help="Create spec file", action="store_true")
    parser.add_argument("-b", "--build", help="Build rpm package", action="store_true")
    parser.add_argument("-r", "--rootpath", help="Build rpm package in root path", type=str, default=dft_root_path)
    parser.add_argument("-d", "--download", help="Download source file indicated path", action="store_true")
    parser.add_argument("-p", "--path", help="indicated path to store files", type=str, default=os.getcwd())
    parser.add_argument("-j", "--json", help="Get Package JSON info", action="store_true")
    parser.add_argument("-o", "--output", help="Output to file", type=str, default="")
    parser.add_argument("pkg", type=str, help="The Python Module Name")
    args=parser.parse_args()

    resp=get_pkg_json(args.pkg)

    if (args.spec):
        build_spec(resp, args.output)

    if (args.build):
        ret = build_rpm(resp, args.rootpath)
        if ret != "":
            print("BuildRequire : %s" % ret)

    if (args.download):
        download_source(resp, args.path)

    if (args.json):
        store_json(resp, args.pkg, args.path)

