#!/usr/bin/python3
"""
Description: Database entity model mapping
"""
from sqlalchemy import Column, Integer, String
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper


class src_package(DBHelper.BASE):  # pylint: disable=C0103,R0903
    """
    Description: Temporary source package model
    """

    __tablename__ = 'src_package'

    pkgKey = Column(Integer, primary_key=True)

    name = Column(String(500), nullable=True)

    version = Column(String(200), nullable=True)

    rpm_license = Column(String(500), nullable=True)

    url = Column(String(200), nullable=True)

    maintaniner = Column(String(100), nullable=True)


class bin_package(DBHelper.BASE):  # pylint: disable=C0103,R0903
    """
    Description: Temporary binary package model
    """
    __tablename__ = 'bin_package'

    pkgKey = Column(Integer, primary_key=True)

    name = Column(String(500), nullable=True)

    version = Column(String(200), nullable=True)

    rpm_license = Column(String(500), nullable=True)

    url = Column(String(500), nullable=True)

    rpm_sourcerpm = Column(String(500), nullable=True)

    src_pack_name = Column(String(200), nullable=True)


class src_requires(DBHelper.BASE):  # pylint: disable=C0103,R0903
    """
    Description: Temporary source package depends on package model
    """
    __tablename__ = 'src_requires'

    id = Column(Integer, primary_key=True)

    pkgKey = Column(Integer)

    name = Column(String(500), nullable=True)


class bin_requiresment(DBHelper.BASE):  # pylint: disable=C0103,R0903
    """
    Description: Dependency package model for temporary binary packages
    """
    __tablename__ = 'bin_requiresment'

    id = Column(Integer, primary_key=True)

    pkgKey = Column(Integer)

    name = Column(String(500), nullable=True)


class bin_provides(DBHelper.BASE):  # pylint: disable=C0103,R0903
    """
    Description: Provided package model for temporary binary packages
    """
    __tablename__ = 'bin_provides'

    id = Column(Integer, primary_key=True)

    pkgKey = Column(Integer)

    name = Column(String(500), nullable=True)
