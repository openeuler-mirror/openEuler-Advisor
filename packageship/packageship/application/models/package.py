#!/usr/bin/python3
"""
Description: Database entity model mapping
"""
import uuid
from sqlalchemy import Column, Integer, String, Text
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper


class SrcPack(DBHelper.BASE):
    """
        Source package model
    """

    __tablename__ = 'src_pack'

    pkgKey = Column(Integer, primary_key=True)
    pkgId = Column(String(500), nullable=True)
    name = Column(String(200), nullable=True)
    arch = Column(String(200), nullable=True)
    version = Column(String(500), nullable=True)
    epoch = Column(String(200), nullable=True)
    release = Column(String(500), nullable=True)
    summary = Column(String(500), nullable=True)
    description = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    time_file = Column(Integer, nullable=True)
    time_build = Column(Integer, nullable=True)
    rpm_license = Column(String(500), nullable=True)
    rpm_vendor = Column(String(500), nullable=True)
    rpm_group = Column(String(500), nullable=True)
    rpm_buildhost = Column(String(500), nullable=True)
    rpm_sourcerpm = Column(String(500), nullable=True)
    rpm_header_start = Column(Integer, nullable=True)
    rpm_header_end = Column(Integer, nullable=True)
    rpm_packager = Column(String(500), nullable=True)
    size_package = Column(Integer, nullable=True)
    size_installed = Column(Integer, nullable=True)
    size_archive = Column(Integer, nullable=True)
    location_href = Column(String(500), nullable=True)
    location_base = Column(String(500), nullable=True)
    checksum_type = Column(String(500), nullable=True)
    maintaniner = Column(String(100), nullable=True)
    maintainlevel = Column(String(100), nullable=True)


class BinPack(DBHelper.BASE):
    """
    Description: functional description:Binary package data
    """
    __tablename__ = 'bin_pack'

    pkgKey = Column(Integer, primary_key=True)
    pkgId = Column(String(500), nullable=True)
    name = Column(String(500), nullable=True)
    arch = Column(String(500), nullable=True)
    version = Column(String(500), nullable=True)
    epoch = Column(String(500), nullable=True)
    release = Column(String(500), nullable=True)
    summary = Column(String(500), nullable=True)
    description = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    time_file = Column(Integer, nullable=True)
    time_build = Column(Integer, nullable=True)
    rpm_license = Column(String(500), nullable=True)
    rpm_vendor = Column(String(500), nullable=True)
    rpm_group = Column(String(500), nullable=True)
    rpm_buildhost = Column(String(500), nullable=True)
    rpm_sourcerpm = Column(String(500), nullable=True)
    rpm_header_start = Column(Integer, nullable=True)
    rpm_header_end = Column(Integer, nullable=True)
    rpm_packager = Column(String(500), nullable=True)
    size_package = Column(Integer, nullable=True)
    size_installed = Column(Integer, nullable=True)
    size_archive = Column(Integer, nullable=True)
    location_href = Column(String(500), nullable=True)
    location_base = Column(String(500), nullable=True)
    checksum_type = Column(String(500), nullable=True)
    src_name = Column(String(500), nullable=True)


class BinRequires(DBHelper.BASE):
    """
        Binary package dependent package entity model
    """

    __tablename__ = 'bin_requires'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=True)
    flags = Column(String(200), nullable=True)
    epoch = Column(String(200), nullable=True)
    version = Column(String(500), nullable=True)
    release = Column(String(200), nullable=True)
    pkgKey = Column(Integer, nullable=True)
    pre = Column(String(20), nullable=True)


class SrcRequires(DBHelper.BASE):
    """
        Source entity package dependent package entity model
    """
    __tablename__ = 'src_requires'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=True)
    flags = Column(String(200), nullable=True)
    epoch = Column(String(200), nullable=True)
    version = Column(String(500), nullable=True)
    release = Column(String(200), nullable=True)
    pkgKey = Column(Integer, nullable=True)
    pre = Column(String(20), nullable=True)


class BinProvides(DBHelper.BASE):
    """
        Component entity model provided by binary package
    """
    __tablename__ = 'bin_provides'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=True)
    flags = Column(String(200), nullable=True)
    epoch = Column(String(200), nullable=True)
    version = Column(String(500), nullable=True)
    release = Column(String(200), nullable=True)
    pkgKey = Column(Integer, nullable=True)


class BinFiles(DBHelper.BASE):
    """
        Installation path of the binary package
    """
    __tablename__ = 'bin_files'
    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=True)
    type = Column(String(50), nullable=True)
    pkgKey = Column(Integer)


class Packages():
    """
    Source code package version, issuer and other information
    """
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    rpm_license = Column(String(500), nullable=True)
    version = Column(String(200), nullable=True)
    release = Column(String(200), nullable=True)
    release_time = Column(String(50), nullable=True)
    used_time = Column(Integer, default=0)
    latest_version = Column(String(200), nullable=True)
    latest_version_time = Column(String(50), nullable=True)
    feature = Column(Integer, default=0)
    cve = Column(Integer, default=0)
    defect = Column(Integer, default=0)
    maintainer = Column(String(200), nullable=True)
    maintainlevel = Column(Integer, nullable=True)
    version_control = Column(String(50), nullable=True)
    src_repo = Column(String(500), nullable=True)
    tag_prefix = Column(String(20), nullable=True)
    summary = Column(String(500), nullable=True)
    description = Column(String(500), nullable=True)

    @classmethod
    def package_meta(cls, table_name):
        """
            Dynamically generate different classes through metaclasses
        """
        _uuid = str(uuid.uuid1())
        model = type(_uuid, (cls, DBHelper.BASE), {
            '__tablename__': table_name})
        return model


class PackagesIssue(DBHelper.BASE):
    """
        Source package issue
    """
    __tablename__ = "packages_issue"
    id = Column(Integer, primary_key=True)
    issue_id = Column(String(50), nullable=True)
    issue_url = Column(String(500), nullable=True)
    issue_content = Column(Text, nullable=True)
    issue_title = Column(String(1000), nullable=True)
    issue_status = Column(String(20), nullable=True)
    pkg_name = Column(String(500), nullable=False)
    issue_download = Column(String(500), nullable=False)
    issue_type = Column(String(50), nullable=True)
    related_release = Column(String(500), nullable=True)


class PackagesMaintainer(DBHelper.BASE):
    """
        Correspondence between source code package and maintainer
    """
    __tablename__ = 'packages_maintainer'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=True)
    maintainer = Column(String(200), nullable=True)
    maintainlevel = Column(Integer, nullable=True)
