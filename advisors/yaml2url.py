# !/usr/bin/python3
# ******************************************************************************
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
This is an script for get url from repo name
"""

from urllib.parse import urljoin


def __get_hg_url(pkg_info):
    """
    Get hg repo url of package
    """
    url = urljoin(pkg_info["src_repo"] + "/", "json-tags")
    return url


def __get_hg_raw_url(pkg_info):
    """
    Get hg raw repo url of package
    """
    url = urljoin(pkg_info["src_repo"] + "/", "raw-tags")
    return url


def __get_github_url(pkg_info):
    """
    Get github repo url of package
    """
    url = "https://github.com/" + pkg_info["src_repo"] + ".git"
    return url


def __get_gnome_url(pkg_info):
    """
    Get gnome repo url of package
    """
    src_repos = pkg_info["src_repo"].split("/")
    if len(src_repos) == 1:
        url = "https://gitlab.gnome.org/GNOME/" + pkg_info["src_repo"] + ".git"
    else:
        url = "https://gitlab.gnome.org/" + pkg_info["src_repo"] + ".git"
    return url


def __get_git_url(pkg_info):
    """
    Get git repo url of package
    """
    url = pkg_info["src_repo"]
    return url


def __get_svn_url(pkg_info):
    """
    Get svn repo url of package
    """
    tag_dir = pkg_info.get("tag_dir", "tags")
    url = pkg_info["src_repo"] + "/" + tag_dir
    return url


def __get_metacpan_url(pkg_info):
    """
    Get metacpan repo url of package
    """
    url = urljoin("https://metacpan.org/release/", pkg_info["src_repo"])
    return url


def __get_gitee_url(pkg_info):
    """
    Get gitee repo url of package
    """
    url = "https://gitee.com/" + pkg_info["src_repo"] + ".git"
    return url


def __get_gnu_ftp_url(pkg_info):
    """
    Get gnu ftp repo url of package
    """
    url = urljoin("https://ftp.gnu.org/gnu/", pkg_info["src_repo"] + "/")
    return url


def __get_ftp_url(pkg_info):
    """
    Get ftp repo url of package
    """
    url = urljoin('ftp', pkg_info["src_repo"] + "/")
    return url


def __get_pypi_url(pkg_info):
    """
    Get pypi repo url of package
    """
    url = urljoin("https://pypi.org/pypi/", pkg_info["src_repo"] + "/json")
    return url


def __get_rubygem_url(pkg_info):
    """
    Get rubygem repo url of package
    """
    url = urljoin("https://rubygems.org/api/v1/versions/", pkg_info["src_repo"] + ".json")
    return url


def __get_sourceforge_url(pkg_info):
    """
    Get git repo url of package
    """
    url = pkg_info["src_repo"]
    return url


def yaml2url(pkg_info):
    """
    Get url from yaml
    """
    if not isinstance(pkg_info, dict):
        print("ERROR: parameter pkg_info type error")
        return None
    vc_type = pkg_info.get("version_control", None)
    if vc_type is None:
        print("Missing version_control in YAML file")
        return None

    switcher = {
        "hg": __get_hg_url,
        "hg-raw": __get_hg_raw_url,
        "github": __get_github_url,
        "git": __get_git_url,
        "gitlab.gnome": __get_gnome_url,
        "svn": __get_svn_url,
        "metacpan": __get_metacpan_url,
        "pypi": __get_pypi_url,
        "rubygem": __get_rubygem_url,
        "gitee": __get_gitee_url,
        "gnu-ftp": __get_gnu_ftp_url,
        "ftp": __get_ftp_url,
        "sourceforge": __get_sourceforge_url
    }

    get_url_method = switcher.get(vc_type, None)
    if get_url_method:
        url = get_url_method(pkg_info)
    else:
        print("Unsupport version control method {vc}".format(vc=vc_type))
        return None

    return url
