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
This is an test script for get url from repo name
"""
import yaml

from advisors import yaml2url


YAML_DOC = """
    version_control: {version_control}
    src_repo: {src_repo}
"""


def test_get_hg_url():
    """
    Test hg repo url
    """
    doc = YAML_DOC.format(version_control="hg",
                          src_repo="https://hg.mozilla.org/projects/python-nss")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://hg.mozilla.org/projects/python-nss/json-tags"


def test_get_hg_raw_url():
    """
    Test hg raw repo url
    """
    doc = YAML_DOC.format(version_control="hg-raw",
                          src_repo="http://hg.libsdl.org/SDL")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "http://hg.libsdl.org/SDL/raw-tags"


def test_get_github_url():
    """
    Test github repo url
    """
    doc = YAML_DOC.format(version_control="github",
                          src_repo="pixel/hexedit")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://github.com/pixel/hexedit.git"


def test_get_gnome_url():
    """
    Test gnome repo url
    """
    doc = YAML_DOC.format(version_control="gitlab.gnome",
                          src_repo="gdm")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://gitlab.gnome.org/GNOME/gdm.git"


def test_get_git_url():
    """
    Test git repo url
    """
    doc = YAML_DOC.format(version_control="git",
                          src_repo="git://sourceware.org/git/glibc.git")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "git://sourceware.org/git/glibc.git"


def test_get_svn_url():
    """
    Test svn repo url
    """
    doc = YAML_DOC.format(version_control="svn",
                          src_repo="https://svn.apache.org/repos/asf/apr/apr")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://svn.apache.org/repos/asf/apr/apr/tags"


def test_get_metacpan_url():
    """
    Test metacpan repo url
    """
    doc = YAML_DOC.format(version_control="metacpan",
                          src_repo="File-Which")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://metacpan.org/release/File-Which"


def test_get_rubygem_url():
    """
    Test rubygem repo url
    """
    doc = YAML_DOC.format(version_control="rubygem",
                          src_repo="path")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://rubygems.org/api/v1/versions/path.json"


def test_get_gitee_url():
    """
    Test gitee repo url
    """
    doc = YAML_DOC.format(version_control="gitee",
                          src_repo="openEuler/lcr")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://gitee.com/openEuler/lcr.git"


def test_get_gnu_ftp_url():
    """
    Test gnu ftp repo url
    """
    doc = YAML_DOC.format(version_control="gnu-ftp",
                          src_repo="bc")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://ftp.gnu.org/gnu/bc/"

def test_get_ftp_url():
    """
    Test ftp repo url
    """
    doc = YAML_DOC.format(version_control="ftp",
                          src_repo="https://ftp.gnu.org/pub/gnu/mailman")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://ftp.gnu.org/pub/gnu/mailman/"


def test_get_pypi_url():
    """
    Test pypi repo url
    """
    doc = YAML_DOC.format(version_control="pypi",
                          src_repo="pygments")

    pkg_info = yaml.load(doc, Loader=yaml.Loader)
    url = yaml2url.yaml2url(pkg_info)
    assert url == "https://pypi.org/pypi/pygments/json"
