#!/usr/bin/python3
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

from urllib import request
from pprint import pprint
from os import path
import json
import sys
import re
import datetime
import argparse
import subprocess

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

def get_source_url(j):
    v = j["info"]["version"]
    rs = j["releases"][v]
    for r in rs:
        if r["packagetype"] == "sdist":
            return r["url"]
    return ""

def transform_module_name(n):
    # remove ()
    ns = re.split("[()]", n)
    if ns[0].startswith("python-"):
        ns[0] = ns[0].replace("python-", "python3-")
        return " ".join(ns) 
    else:
        ns[0] = "python3-"+ns[0] 
        if ns[0].find("/") != -1 or ns[0].find(".") != -1:
            return ""
        else:
            return " ".join(ns)

def get_requires(j):
    rs = j["info"]["requires_dist"]
    if rs == None:
        return
    for r in rs:
        idx = r.find(";")
        mod = transform_module_name(r[:idx])
        if mod != "":
            print ("Requires:\t"+mod)

def get_buildarch(j):
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
    if res == []:
        return j["info"]["summary"]
    else:
        return "\n".join(res)

def store_json(resp, pkg):
    json_file = json_file_template.format(pkg_name=pkg)
    
    # if file exist, do nothing 
    if path.exists(json_file) and path.isfile(json_file):
        with open(json_file, 'r') as f:
            resp = json.load(f)
    else:
        with open(json_file, 'w') as f:
            json.dump(resp, f)


def get_pkg_json(pkg):
    url = url_template.format(pkg_name=pkg)

    u = request.urlopen(url)
    resp = json.loads(u.read().decode('utf-8'))

    return resp



def download_source(resp):
    subprocess.run(["wget", get_source_url(resp)])
    return

def prepare_rpm_build_env(rootdir):
    return True

def build_rpm(resp):
    if(prepare_rpm_build_env() == False):
        return

    return


def build_spec(resp, output):
    tmp = sys.stdout
    if (output == ""):
        print()
    else:
        sys.stdout = open(output,'w')

    
    print(name_tag_template.format(pkg_name=resp["info"]["name"]))
    print(version_tag_template.format(pkg_ver=resp["info"]["version"]))
    print(release_tag_template)
    print(summary_tag_template.format(pkg_sum=resp["info"]["summary"]))
    print(license_tag_template.format(pkg_lic=resp["info"]["license"]))
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
    print("Provides:\tpython-"+resp["info"]["name"])
    print(buildreq_tag_template.format(req='python3-devel'))
    print(buildreq_tag_template.format(req='python3-setuptools'))

    if build_noarch == False:
        print(buildreq_tag_template.format(req='python3-cffi'))
        print(buildreq_tag_template.format(req='gcc'))
        print(buildreq_tag_template.format(req='gdb'))

    print("%description -n python3-"+resp["info"]["name"])
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
    print("")
    print("%files -n python3-{name}".format(name=resp["info"]["name"]))
#    print("%{python3_sitelib}/*.egg-info/")
#    print("%{python3_sitelib}/"+resp["info"]["name"])

    if build_noarch:
        print("%{python3_sitelib}/*")
    else:
        print("%{python3_sitearch}/*")

    print("")
    print("%files help")
    print("%{_pkgdocdir}")
    print("")
    print("%changelog")
    date_str = datetime.date.today().strftime("%a %b %d %Y")
    print("* {today} Python_Bot <Python_Bot@openeuler.org>".format(today=date_str))
    print("- Package Spec generated")

    sys.stdout = tmp


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--spec", help="Create spec file", action="store_true")
    parser.add_argument("-b", "--build", help="Build rpm package", action="store_true")
    parser.add_argument("-d", "--download", help="Download source file", action="store_true")
    parser.add_argument("-j", "--json", help="Get Package JSON info", action="store_true")
    parser.add_argument("-o", "--output", help="Output to file", type=str, default="")
    parser.add_argument("pkg", type=str, help="The Python Module Name")
    args=parser.parse_args()

    print(args)

    resp=get_pkg_json(args.pkg)

    if (args.spec):
        build_spec(resp, args.output)

    if (args.build):
        build_rpm(resp)

    if (args.download):
        download_source(resp)

    if (args.json):
        store_json(resp, args.pkg)
