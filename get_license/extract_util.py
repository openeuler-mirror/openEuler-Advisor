import os
import tarfile
import zipfile
import lzma
import filetype
import logging
import shutil

log_check = logging.getLogger()

def _extract_tar(tarball_path, extract_path):
    """
    Extract tar package in extract_path. If extract failed the program will exit.
    """
    res_flag = True
    if not os.path.isfile(tarball_path):
        log_check.error("%s is not a file", tarball_path)
        res_flag = False
        return res_flag

    try:
        with tarfile.open(tarball_path) as content:
            content.extractall(path=extract_path)
    except FileNotFoundError:
        res_flag = False
        log_check.error("%s can not be found", tarball_path)
    except tarfile.CompressionError:
        res_flag = False
        log_check.error("%s can not be decoded correctly", tarball_path)
    except tarfile.ReadError:
        res_flag = False
        log_check.error("%s is invalid tar file", tarball_path)
    finally:
        return res_flag


def _extract_bz2(bz2_path, extract_path):
    """
    Extract bz2 package in extract_path. If extract failed the program will exit.
    """
    res_flag = True
    if not os.path.isfile(bz2_path):
        log_check.error("%s is not a bz2 file", bz2_path)
        res_flag = False
        return res_flag

    try:
        archive = tarfile.open(bz2_path, 'r:bz2')
        for tarinfo in archive:
            archive.extract(tarinfo, extract_path)
        archive.close()
    except FileNotFoundError:
        res_flag = False
        log_check.error("%s can not be found", bz2_path)
    except tarfile.CompressionError:
        res_flag = False
        log_check.error("%s can not be decoded correctly", bz2_path)
    except tarfile.ReadError:
        res_flag = False
        log_check.error("%s is invalid tar file", bz2_path)
    finally:
        return res_flag


def _extract_zip(zip_path, extract_path):
    """
    Extract zip package in extract_path. If extract failed the program will exit.
    """
    res_flag = True
    if not os.path.isfile(zip_path):
        log_check.error("%s is not a zip file", zip_path)
        res_flag = False
        return res_flag

    try:
        zip_file = zipfile.ZipFile(zip_path)
        zip_file.extractall(extract_path)
        zip_file.close()
    except FileNotFoundError:
        res_flag = False
        log_check.error("%s can not be found", zip_path)
    except zipfile.BadZipfile:
        res_flag = False
        log_check.error("%s is bad zip file", zip_path)
    except zipfile.LargeZipFile:
        res_flag = False
        log_check.error("The zip file requires the zip64 feature but is not enabled")
    finally:
        return res_flag


def _extract_xz(xz_path, extract_path):
    """
    extract tar.xz to specific path
    """
    if not os.path.isfile(xz_path):
        log_check.error("%s is not a file", xz_path)
        return False
    tar_file = os.path.join(extract_path, os.path.basename(xz_path).split(".xz")[0])
    try:
        with lzma.open(xz_path, "rb") as file_input:
            with open(tar_file, "wb") as output:
                shutil.copyfileobj(file_input, output)
                res = _extract_tar(tar_file, extract_path)
                os.remove(tar_file)
                return res
    except FileNotFoundError:
        log_check.error("%s can not found", xz_path)
        return False
    except lzma.LZMAError:
        log_check.error("%s can not be decompressed", xz_path)
        return False


def extract_tarball(tb_file, extract_path):
    """
    Entrypoint for extract tarball
    """
    method_map = {
            "tar": _extract_tar,
            "gz": _extract_tar,
            "bz2": _extract_bz2,
            "zip": _extract_zip,
            "xz": _extract_xz
            }
    ft = filetype.guess(tb_file)
    method = None if not ft else method_map.get(ft.extension, None)
    if method:
        return method(tb_file, extract_path)
    log_check.error("filetype: %s not support to extract")
    return False


def extract_all_pkg(tarballs, extract_path):
    """
    Extract all tarballs
    """
    extr_res = True
    for tname in tarballs:
        if not extract_tarball(tname, extract_path):
            extr_res = False
    return extr_res