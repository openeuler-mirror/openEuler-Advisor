#!/usr/bin/python3

from urllib import request
from pprint import pprint
from os import path
import json
import sys
import datetime

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

pkg = sys.argv[1]

url = url_template.format(pkg_name=pkg)
json_file = json_file_template.format(pkg_name=pkg)
name_tag = name_tag_template.format(pkg_name=pkg)

# if file exist? 
if path.exists(json_file) and path.isfile(json_file):
    with open(json_file, 'r') as f:
        resp = json.load(f)
else:
    u = request.urlopen(url)
    resp = json.loads(u.read().decode('utf-8'))
    with open(json_file, 'w') as f:
        json.dump(resp, f)

def get_source_url(j):
    v = j["info"]["version"]
    rs = j["releases"][v]
    for r in rs:
        if r["packagetype"] == "sdist":
            return r["url"]
    return ""

def get_description(j):
    n = j["info"]["name"]
    return "blahblah\nblahblah\n"

if __name__ == "__main__":
    print(name_tag_template.format(pkg_name=resp["info"]["name"]))
    print(version_tag_template.format(pkg_ver=resp["info"]["version"]))
    print(release_tag_template)
    print(summary_tag_template.format(pkg_sum=resp["info"]["summary"]))
    print(license_tag_template.format(pkg_lic=resp["info"]["license"]))
    print(home_tag_template.format(pkg_home=resp["info"]["project_urls"]["Homepage"]))
    print(source_tag_template.format(pkg_source=get_source_url(resp)))
    print("BuildArch:   noarch")
    print("")
    print("%description")
    print(get_description(resp))
    print("")
    print("%package -n python3-{name}".format(name=resp["info"]["name"]))
    print(summary_tag_template.format(pkg_sum=resp["info"]["summary"]))
    print(buildreq_tag_template.format(req='python3-devel'))
    print(buildreq_tag_template.format(req='python3-setuptools'))
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
    print("%{python3_sitelib}/*")
    print("")
    print("%files help")
    print("%{_pkgdocdir}")
    print("")
    print("%changelog")
    date_str = datetime.date.today().strftime("%a %b %d %Y")
    print("* {today} Python_Bot <Python_Bot@openeuler.org>".format(today=date_str))
    print("- Package Spec generated")
