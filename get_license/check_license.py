#! /usr/bin/env python
# coding=utf-8
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
# Author:
# Create: 2020-10-13
# ******************************************************************************/
"""
check license for source package
"""
import os
import re
import chardet
import argparse
import yaml

from get_license.spec import Spec, replace_macros
import logging

log_check = logging.getLogger()


class PkgLicense(object):
    """
    解析获取软件包中源码、spec中的license
    进行白名单校验、一致性检查
    """

    LICENSE_FILE_TARGET = ["apache-2.0",
                           "artistic",
                           "artistic.txt",
                           "libcurllicense",
                           "gpl.txt",
                           "gpl2.txt",
                           "gplv2.txt",
                           "lgpl.txt",
                           "notice",
                           "about_bsd.txt",
                           "mit",
                           "pom.xml",
                           "meta.yml",
                           "pkg-info"]

    LICENSE_TARGET_PAT = re.compile(
            r"^(copying)|(copyright)|(copyrights)|(licenses)|(licen[cs]e)(\.(txt|xml))?$")

    def __init__(self):
        self.license_list = {}
        self.full_name_map = {}

    @staticmethod
    def load_licenses_config(filename):
        white_black_list = {}
        translations = {}
        if not os.path.exists(filename):
            log_check.warning("not found License config: %s", filename)
            return white_black_list, translations
        data = {}
        with open(filename, "r") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                log_check.exception("yaml load error: %s", str(e))
                return white_black_list, translations
        PkgLicense.parse_tag_license(data["Software Licenses"]["Bad Licenses"], 
                                    "black", 
                                    white_black_list, 
                                    translations)
        PkgLicense.parse_tag_license(data["Software Licenses"]["Good Licenses"], 
                                    "white", 
                                    white_black_list, 
                                    translations)
        PkgLicense.parse_tag_license(data["Software Licenses"]["Need Review Licenses"], 
                                    "need review", 
                                    white_black_list, 
                                    translations)
        return white_black_list, translations

    @staticmethod
    def parse_tag_license(licenses, tag, white_black_list, translations):
        for lic in licenses:
            if lic["identifier"] not in white_black_list:
                white_black_list[lic["identifier"]] = tag
            for oname in lic["alias"]:
                if oname not in translations:
                    translations[oname] = lic["identifier"]

    @staticmethod
    def check_license_safe(licenses, license_list):
        """  
        Check if the license is in the blacklist.
        """
        result = True
        for lic in licenses:
            res = license_list.get(lic, "need review")
            if res == "white":
                pass
            elif res == "black":
                log_check.error("This license: %s is not safe", lic)
                result = False
            else:
                log_check.warning("This license: %s need to be review", lic)
                result = False
        return result

    # 以下为从spec文件中获取license
    @staticmethod
    def scan_licenses_in_spec(specfile, license_translations):
        """
        Find spec file and scan. If no spec file
        or open file failed, the program will exit with an error.
        """
        if not specfile:
            return []
        s_spec = Spec.from_file(specfile)
        licenses = replace_macros(s_spec.license, s_spec)
        licenses_in_spec = set()

        words = PkgLicense.split_license(licenses)
        for word in words:
            licenses_in_spec.add(word)
        result = PkgLicense._translate_license(licenses_in_spec, license_translations)
        if not licenses_in_spec:
            log_check.warning("full license in spec is empty")
        else:
            log_check.info("full license in spec: %s", ", ".join(list(licenses_in_spec)))
        if not license_translations:
            log_check.warning("real license in spec is empty")
        else:
            log_check.info("real license in spec: %s", ", ".join(result))
        return result

    @staticmethod
    def split_license(licenses):
        """
        分割spec license字段的license
        """
        license_set = re.split(r'\(|\)|\,|\W+[Aa][Nn][Dd]\W+|\s+-or-\s+|\s+[oO][rR]\s+|\s+/\s+', licenses)
        for index in range(len(license_set)): # 去除字符串首尾空格
            license_set[index] = license_set[index].strip()
        return set(filter(None, license_set)) # 去除list中空字符串

    # 以下为从license文件中获取license
    @staticmethod
    def scan_licenses_in_source(srcdir, license_translations, head=True):
        """
        Find LICENSE files and scan.
        """
        full_license_in_file = set()
        if not os.path.exists(srcdir):
            log_check.error("%s not exist.", srcdir)
            return full_license_in_file
        with os.scandir(srcdir) as dir_iter:
            for entry in dir_iter:
                if not entry.name.startswith('.'):
                    file_name = entry.name
                    if os.path.islink(os.path.join(srcdir, file_name)):
                        continue
                    # print("now file: {}".format(file_name))
                    if entry.is_file():
                        if file_name.lower() in PkgLicense.LICENSE_FILE_TARGET \
                                or PkgLicense.LICENSE_TARGET_PAT.search(file_name.lower()):
                            # print("scan the license target file: {}".format(file_name))
                            log_check.info("scan the license target file: %s", file_name)
                            full_license_in_file.update(
                                PkgLicense.scan_licenses(
                                    os.path.join(srcdir, file_name),
                                    license_translations))
                    else:
                        full_license_in_file.update(
                                    PkgLicense.scan_licenses_in_source(
                                        os.path.join(srcdir, file_name),
                                        license_translations,
                                        False))
        result = full_license_in_file
        if head:
            log_check.info("full license in files: %s", ", ".join(list(full_license_in_file)))
            result = PkgLicense._translate_license(full_license_in_file, license_translations)
            log_check.info("real license in files: %s", ", ".join(result))
        return result

    @staticmethod
    def scan_licenses(copying, license_translations):
        """
        Scan licenses from copying file and add to licenses_for_source_files.
        if get contents failed or decode data failed, return nothing.
        """
        licenses_in_file = set()
        log_check.info("%d", len(license_translations))
        for word in license_translations:
            if word in copying:
                licenses_in_file.add(word)
                log_check.info("get license({}) from file({})".format(word, copying))
        try:
            with open(copying, "rb") as file_handler:
                data = file_handler.read()
        except FileNotFoundError:
            return licenses_in_file
        data = PkgLicense._auto_decode_data(data)
        if not data:
            return licenses_in_file
        content = ' '.join(str(data).split())
        for word in license_translations:
            try:
                if word in content:
                    pattern_str = r'(^{word}$)|(^{word}(\W+).*)|(.*(\W+){word}$)|(.*(\W+){word}(\W+).*)' \
                                  .format(word=word)
                    if re.match(r'' + pattern_str + '', content):
                        licenses_in_file.add(word)
                        print("get license({}) from file({})".format(word, copying))
                        log_check.info("get license({}) from file({})".format(word, copying))
            except UnicodeDecodeError as e:
                log_check.exception("decode error: %s", str(e))
        return licenses_in_file

    @staticmethod
    def _decode_data(data, charset):
        """
        Decode the license string. return the license string or nothing.
        """
        if not charset:
            return ""
        try:
            return data.decode(charset)
        except UnicodeDecodeError as ue:
            log_check.exception("auto decode data error %s", str(ue))
            return ""

    @staticmethod
    def _auto_decode_data(data):
        return PkgLicense._decode_data(data, chardet.detect(data)['encoding'])

    @staticmethod
    def _translate_license(data, license_translations):
        result = set()
        for e in data:
            print("origin:{} after:{}".format(e, license_translations.get(e, e)))
            result.add(license_translations.get(e, e))
        return list(result)

    @staticmethod
    def check_licenses_is_same(licenses_for_spec, licenses_for_source_files):
        """
        Check if the licenses from SPEC is the same as the licenses from LICENSE file.
        if license in spec contains license in srcs, return True. if not same return False.
        """
        return set(licenses_for_source_files) <= set(licenses_for_spec)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--cvelist", default="",
                        help="path of cve pkgs")
    # input of new repo name
    parser.add_argument("-o", "--old_repos", type=str, nargs='*', required=True,
                        help="repo list of old repo")
    parser.add_argument("-n", "--new_repos", type=str, nargs='*', required=True,
                        help="repo list of new repo")

    parser.add_argument("-s", "--savedir", default="/tmp/update-package/pkg_rpm",
                        help="dir of download dir")
    parser.add_argument("-d", "--downloaddir", default="/tmp/update-package/download",
                        help="dir of require download dir")
    parser.add_argument("--skip_cve_list", action="store_true", default=False,
                        help="skip download pkg in cve list")
    args = parser.parse_args()