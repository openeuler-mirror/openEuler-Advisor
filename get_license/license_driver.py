from get_license.spec import Spec 
from get_license.check_license import PkgLicense
from get_license.extract_util import extract_all_pkg

import os
import logging
import subprocess
import shutil

log_check = logging.getLogger()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LICENSE_LIST_PATH = os.path.join(CURRENT_DIR, "config", "LicenseList.txt")
FULLNAME_LICENSE_PATH = os.path.join(CURRENT_DIR, "config", "license_translations")
LICENSE_YAML_PATH = os.path.join(CURRENT_DIR, "config", "Licenses.yaml")
UNUSED_FILE_SUFFIX = (".spec~", ".specfc", ".spec.old", ".osc")
COMPRESSED_TYPE = ("tar", "tar.xz", ".tar.gz", ".tgz", ".gz", ".zip", ".bz2")

def get_parsed_spec(filename, parse_name="temp.spec"):
    """
    split license str in spec file

    :return:{
        license's short name: friendlyness(white, black, unknow),
        ...
    }
    """
    if not os.path.isfile(filename):
        log_check.error("spec file %s not exist", os.path.basename(filename))
        return ""
    parse_file = os.path.join(os.path.dirname(filename), parse_name)
    cmd_list = ["rpmspec", "--parse", filename, ">", parse_file]
    try:
        sub_proc = subprocess.run(" ".join(cmd_list), 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  check=True, shell=True)
    except subprocess.CalledProcessError as e:
        log_check.error("parse spec failed: %s", e)
        return ""
    return parse_file

def load_config(list_file, full_name_file):
    if not os.path.isfile(list_file) or not os.path.isfile(full_name_file):
        log_check.error("cannot find file")
        return None
    pl = PkgLicense()
    PkgLicense.load_licenses_dict(pl.license_list, list_file)
    PkgLicense.load_licenses_dict(pl.full_name_map, full_name_file)
    return pl


def load_config_new(license_config):
    if not os.path.isfile(license_config):
        log_check.error("cannot find file")
        return None
    pl = PkgLicense()
    pl.license_list, pl.full_name_map = PkgLicense.load_licenses_new(license_config)
    return pl


def parse_spec_license(spec_file, pl):
    parse_spec = get_parsed_spec(spec_file)
    if not parse_spec:
        parse_spec = spec_file
    spec_licenses =  pl.scan_licenses_in_spec(parse_spec, pl.full_name_map)
    spec_lic_dict = {}
    for lic in spec_licenses:
        spec_lic_dict[lic] = pl.license_list.get(lic, "unknow")
    os.remove(parse_spec)
    return spec_lic_dict


def parse_compressed_file_license(files, extract_path, pl):
    src_lic_dict = {}
    _ = not os.path.exists(extract_path) and os.makedirs(extract_path)
    extract_all_pkg(files, extract_path)
    src_licenses = PkgLicense.scan_licenses_in_source(extract_path, pl.full_name_map)
    for lic in src_licenses:
        src_lic_dict[lic] = pl.license_list.get(lic, "unknow")
    shutil.rmtree(extract_path)
    return src_lic_dict


def get_all_license(work_dir, extract_path, pl):
    compressed_files = []
    spec_file = None
    license_in_spec = {}
    license_in_src = {}

    for file_name in os.listdir(work_dir):
        file_path = os.path.join(work_dir, file_name)
        log_check.debug('Scanning file: %s', file_path)
        if is_compressed_file(file_path):  # save all file need to check license
            compressed_files.append(file_path)
            continue
        if file_name.endswith(".spec"):
            license_in_spec = parse_spec_license(file_path, pl)

    license_in_src = parse_compressed_file_license(compressed_files, extract_path, pl)

    return license_in_spec, license_in_src

def is_compressed_file(src_file):
    """
    Determine whether it is a compressed file.
    """
    if os.path.isfile(src_file):
        if src_file.endswith(COMPRESSED_TYPE):
            return True
    return False