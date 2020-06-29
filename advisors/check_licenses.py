#!/usr/bin/python3
"""
(1) This is a script that checks whether the licenses in the LICENSE file 
    in the tar package and the licenses in the SPEC file are the same. 
    If they are the same, output:
    "licenses from LICENSES are same as form SPEC:[xxx, yyy] <==> [xxx, zzz]"

    If they are not the same, output:
    "licenses from LICENSES are not same as form SPEC:[xxx, yyy] <==> [xxx, yyy]"

(2) This script depends on download.py and license_translations,
    you can add keywords for licenses in license_translations.

(3) Command parameters
    Required parameters:
    -t	Specify the path or url of the tar package
        (e.g. /home/test.tar.gz or  https://example.com/test.tar.gz)
    -s	Specify the path of the spec file
        (e.g. /home/test.spec)

    Optional parameters:		
    -w  With this parameter, if the licenses in the tar 
        and the licenses in the spec file are are not the same, 
        modify the spec file directly.
    -d  Specify the decompression path of the tar package, 
        default: /var/tmp/tmp_tarball
"""
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: wangchuangGG
# Create: 2020-06-27
# Description: provide a tool to check licenses in tar package and spec file
# ******************************************************************************/

import argparse
import configparser
import os
import re
import sys
import hashlib
import tarfile
import bz2
import shutil
import download
import chardet
import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)

licenses_for_license = []
licenses_for_spec = []
license_translations = {}
def main():
    """ Entry point for check_licenses."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tarball", default="", nargs="?",
                        help="tarball path or url (e.g."
                        "/home/test.tar.gz" 
                        " or http://example.com/test.tar.gz)")
    parser.add_argument("-s", "--specfile", default="", nargs="?",
                        help="SPEC file path (e.g. /home/mytar.spec)")
    parser.add_argument("-w", "--writespec", dest="writespec", action="store_true",
                        default=False,
                        help="Overwrite the licenses of SPEC file")
    parser.add_argument("-d", "--downloadpath", default="", nargs="?",
                        help="The dest download or extract path of tarball"
                        " (e.g. /home/tmp_tarball default: /var/tmp/tmp_tarball)")
    args = parser.parse_args()

    if not args.tarball:
        parser.error(argparse.ArgumentTypeError(
            "the tarball path or url argument['-t'] is required"))
    
    if not args.specfile:
        parser.error(argparse.ArgumentTypeError(
            "the spec file argument['-s'] is required"))
    
    if args.downloadpath:
        download_path = args.downloadpath
    else:
        download_path = "/var/tmp/tmp_tarball"
        if os.path.exists(download_path):
            shutil.rmtree(download_path)
    os.makedirs(download_path, exist_ok=True)
    process_licenses(args, download_path)


def get_contents(filename):
    """
    Get file contents and return values.
    If read failed return None.
    """
    with open(filename, "rb") as f:
        return f.read()
    return None


def get_tarball_from_url(upstream_url, download_path, tarpackage):
    """
    Get tar package from url.
    return: tar package path.
    """
    tarball_path = download_path + "/" + tarpackage
    if not os.path.isfile(tarball_path):
        download.do_curl(upstream_url, dest=tarball_path)
    return tarball_path


def extract_tar(tarball_path, extraction_path):
    """
    Extract tar package in extraction_path.
    If extract failed the program will exit.
    """
    if not os.path.isfile(tarball_path):
        logging.error("%s is not a tarball file", tarball_path)
        exit(1)
    with tarfile.open(tarball_path) as content:
        content.extractall(path=extraction_path)


def decode_license(license_string, charset):
    """ 
    Decode the license string.
    return the license string or nothing.
    """
    if not charset:
        return
    return license_string.decode(charset)


def add_license_from_spec_file(license_string):
    """
    Add license to licenses_for_spec.
    """
    if license_string in licenses_for_spec:
        logging.debug("the license was in licenses_for_spec: %s", license_string)
    else:
        licenses_for_spec.append(license_string)


def add_license_from_license_file(license_string):
    """
    Add license to licenses_for_license.
    """
    if license_string in licenses_for_license:
        logging.debug("the license was in licenses_for_license: %s\n", license_string)
    else:
        licenses_for_license.append(license_string)


def scan_licenses(copying):
    """
    Scan licenses from copying file and add to licenses_for_license.
    if get contents failed or decode data failed, return nothing.
    """
    try:
        data = get_contents(copying)
    except FileNotFoundError:
        return
    data = decode_license(data, chardet.detect(data)['encoding'])
    if not data:
        return 
    for word in license_translations:
        if word in data:
            real_word = license_translations.get(word, word)
            add_license_from_license_file(real_word)
    logging.debug("all licenses from license file is: %s", licenses_for_license)


def scan_licenses_in_LICENSE(srcdir):
    """
    Find LICENSE files and scan. 
    """
    targets = ["copyright",
                "copyright.txt",
                "apache-2.0",
                "artistic.txt",
                "libcurllicense",
                "gpl.txt",
                "gpl2.txt",
                "gplv2.txt",
                "notice",
                "copyrights",
                "licence",
                "about_bsd.txt"]
    target_pat = re.compile(r"^((copying)|(licen[cs]e))|(licen[cs]e)(\.(txt|xml))?$")
    files = os.listdir(srcdir)
    for filename in files:
        if not os.path.isdir(filename):
            if filename.lower() in targets or target_pat.search(filename.lower()):
                scan_licenses(os.path.join(srcdir, filename))


def clean_license_string(lic):
    """
    Clean up license string by replace substrings.
    """
    reps = [(" (", "("),
            (" v2", "-2"),
            (" v3", "-3"),
            (" 2", "-2"),
            (" 3", "-3"),
            (" <", "<"),
            (" >", ">"),
            ("= ", "="),
            ("GPL(>=-2)", "GPL-2.0+"),
            ("Modified", ""),
            ("OSI", ""),
            ("Approved", ""),
            ("Simplified", ""),
            ("file", ""),
            ("LICENSE", "")]

    for sub, rep in reps:
        lic = lic.replace(sub, rep)
    return lic


def scan_licenses_in_SPEC(specfile):
    """
    Find spec file and scan.
    If no spec file or open file failed,
    the program will exit with an error. 
    """
    if not specfile.endswith(".spec"):
        logging.error("%s is not a spec file", specfile)
        exit(1)
    try:
        with open(specfile, 'r') as specfd:
            lines = specfd.readlines()
    except FileNotFoundError:
        logging.error("no SPEC file found!")
        exit(1)
    for line in lines:
        if line.startswith("#"):
            continue
        excludes = ["and", "AND"]
        if line.startswith("License"):
            splits = line.split(":")[1:]
            words = ":".join(splits).strip()
            if words in license_translations:
                real_words = license_translations.get(words, words)
                add_license_from_spec_file(real_words)
            else:
                words = clean_license_string(words).split()
                for word in words:
                    if word not in excludes:
                        real_word = license_translations.get(word, word)
                        logging.debug("after translate license_string ==> "
                                    "real_license: %s ==> %s", word, real_word)
                        add_license_from_spec_file(real_word)
    logging.debug("\nall licenses from SPEC file is: %s", licenses_for_spec)                        


def check_licenses_is_same():
    """
    Check if the licenses from SPEC is the same as the licenses from LICENSE file.
    if same, return True.
    if not same return False.
    """
    for lic_from_licenses in licenses_for_license:
        if lic_from_licenses not in licenses_for_spec:
            return False 
    for lic_from_spec in licenses_for_spec:
        if lic_from_spec not in licenses_for_license:
            return False
    return True


def overwrite_spec(specfile):
    """
    Write License in SPEC file.
    If open file failed, return nothing.
    """
    licenses_for_wirte = "License:\t"
    for lic in licenses_for_license:
        if lic == licenses_for_license[0]:
            licenses_for_wirte += lic
        else:
            licenses_for_wirte += " and " + lic
    licenses_for_wirte += "\n"
    
    try:
        with open(specfile, 'r') as specfd:
            lines = specfd.readlines()
            specfd.close()
    except FileNotFoundError:
        return
    f = open(specfile, 'w')
    for line in lines:
        if line.startswith("License"):
            f.write(licenses_for_wirte)
        else:
            f.write(line)
    f.close()
    logging.info("licenses wirte to spec success")


def read_licenses_translate_conf(filename):
    """
    Read the licenses_translate file.
    """
    conf_dir = os.path.dirname(os.path.abspath(__file__))
    conf_path = os.path.join(conf_dir, filename)
    if not os.path.isfile(conf_path):
        logging.info("not found the config file: %s", conf_path)
        return
    with open(conf_path, "r") as conf_file:
        for line in conf_file:
            if line.startswith("#"):
                continue
            key_name, final_name = line.rsplit(", ", 1)
            license_translations[key_name] = final_name.rstrip()


def process_licenses(args, download_path):
    """
    Begin process licenses in tar package and spec file. 
    """
    read_licenses_translate_conf("license_translations")

    if os.path.exists(args.tarball):
        tarball_path = args.tarball
    else:
        tarball_path = get_tarball_from_url(args.tarball, download_path, os.path.basename(args.tarball))
    extract_tar(tarball_path, download_path)
    
    tarball_name = os.path.basename(tarball_path)
    extract_tar_name = os.path.splitext(tarball_name)[0]
    extract_file_name = os.path.splitext(extract_tar_name)[0]
    scan_licenses_in_LICENSE(os.path.join(download_path, extract_file_name))
    
    specfile = args.specfile
    scan_licenses_in_SPEC(specfile)

    if check_licenses_is_same():
        logging.info("licenses from LICENSES are same as form SPEC:"
                    "%s <==> %s", licenses_for_license, licenses_for_spec)
    else:
        logging.info("licenses from LICENSES are not same as form SPEC:"
                    "%s <==> %s", licenses_for_license, licenses_for_spec)
        if args.writespec:
            overwrite_spec(specfile)
            exit(0)
    exit(0)


if __name__ == '__main__':
    main()
