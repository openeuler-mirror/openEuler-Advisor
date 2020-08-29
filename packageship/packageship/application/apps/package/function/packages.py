#!/usr/bin/python3
"""
Description: Get package information and modify package information
functions: get_packages, buildep_packages, sub_packages, get_single_package,
 update_single_package, update_maintaniner_info
"""
import math


from flask import current_app, jsonify
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError


from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.serialize import AllPackInfoSchema
from packageship.application.apps.package.serialize import SinglePackInfoSchema
from packageship.libs.dbutils import DBHelper
from packageship.application.models.package import SrcPack
from packageship.application.models.package import PackagesMaintainer
from packageship.application.models.package import PackagesIssue
from packageship.application.models.package import SrcRequires
from packageship.application.models.package import BinPack
from packageship.application.models.package import BinRequires
from packageship.application.models.package import BinProvides
from packageship.libs.exception import Error
from packageship.application.models.package import Packages


def get_all_package_info(tablename, pagenum, pagesize,
                         srcname, maintainner, maintainlevel):
    """
    Args:
        tablename: Table Name
        pagenum: Page number
        pagesize: Current page display quantity

    Returns:
        package info

    Attributes:
        SQLAlchemyError: sqlalchemy error
        DisconnectionError: Cannot connect to database error
        Error: Error
    """
    try:
        with DBHelper(db_name="lifecycle") as database_name:
            if tablename not in database_name.engine.table_names():
                response = ResponseCode.response_json(
                    ResponseCode.TABLE_NAME_NOT_EXIST)
                response['total_count'] = None
                response['total_page'] = None
                return jsonify(response)
            cls_model = Packages.package_meta(tablename)
            # If srcname is empty, it will query all the information in the
            # library
            package_info_set_one = database_name.session.query(cls_model).outerjoin(
                PackagesMaintainer, cls_model.name == PackagesMaintainer.name)
            if srcname:
                package_info_set_one = package_info_set_one.filter(
                    cls_model.name.like('%{srcname}%'.format(srcname=srcname)))
            if maintainner:
                package_info_set_one = package_info_set_one.filter(
                    PackagesMaintainer.maintainer == maintainner)
            if maintainlevel:
                package_info_set_one = package_info_set_one.filter(
                    PackagesMaintainer.maintainlevel == maintainlevel)
            package_info_set = package_info_set_one.limit(
                int(pagesize)).offset((int(pagenum) - 1) * int(pagesize)).all()
            packageinfo_dicts = AllPackInfoSchema(
                many=True).dump(package_info_set)
            total_count = package_info_set_one.count()
            total_page = math.ceil(total_count / int(pagesize))
            packageinfo_dicts = parsing_dictionary_issuse(packageinfo_dicts)
            packageinfo_dicts = parsing_dictionary_maintainner(
                packageinfo_dicts)
            response = ResponseCode.response_json(
                ResponseCode.SUCCESS, packageinfo_dicts)
            response["total_count"] = total_count
            response["total_page"] = total_page
            return response
    except (SQLAlchemyError, DisconnectionError, Error) as error:
        current_app.logger.error(error)
        response = ResponseCode.response_json(
            ResponseCode.TABLE_NAME_NOT_EXIST)
        response["total_count"] = None
        response["total_page"] = None
        return jsonify(response)


def parsing_dictionary_issuse(packageinfo_dicts):
    """

    Args:
        packageinfo_dicts: package info dict

    Returns:
        packageinfo_dicts
    """
    with DBHelper(db_name="lifecycle") as database_name:
        for packageinfo_dict in packageinfo_dicts:
            issue_count = database_name.session.query(PackagesIssue).filter_by(
                pkg_name=packageinfo_dict.get("name")).count()
            packageinfo_dict["issue"] = issue_count
        return packageinfo_dicts


def parsing_dictionary_maintainner(packageinfo_dicts):
    """
    parsing dictionary maintainner

    Args:
        packageinfo_dicts:

    Returns:
        packageinfo_dicts
    """
    with DBHelper(db_name="lifecycle") as database_name:
        for packageinfo_dict in packageinfo_dicts:
            maintainer_obj = database_name.session.query(PackagesMaintainer).filter_by(
                name=packageinfo_dict.get("name")).first()
            if maintainer_obj is None:
                packageinfo_dict["maintainer"] = None
                packageinfo_dict["maintainlevel"] = None
            else:
                packageinfo_dict["maintainer"] = maintainer_obj.maintainer
                packageinfo_dict["maintainlevel"] = maintainer_obj.maintainlevel
        return packageinfo_dicts


def sing_pack(srcname, tablename):
    """
    Query information about a single source package, including a layer
    of installation dependencies and compilation dependencies
    Args:
        srcname: The name of the source package
        tablename: The name of the table in the database

    Returns:
        single pack package info

    Attributes:
        SQLAlchemyError: sqlalchemy error
        DisconnectionError: Cannot connect to database error
        Error: Error
    """
    try:
        with DBHelper(db_name="lifecycle") as database_name:
            if tablename not in database_name.engine.table_names():
                return jsonify(
                    ResponseCode.response_json(
                        ResponseCode.TABLE_NAME_NOT_EXIST))
            cls_model = Packages.package_meta(tablename)
            package_info_obj = database_name.session.query(
                cls_model).filter_by(name=srcname).first()
            if package_info_obj is None:
                return jsonify(
                    ResponseCode.response_json(
                        ResponseCode.PACK_NAME_NOT_FOUND))
            pack_info_dict = SinglePackInfoSchema(
                many=False).dump(package_info_obj)
            issue_count = database_name.session.query(
                PackagesIssue).filter_by(pkg_name=package_info_obj.name).count()
            pack_info_dict["issue"] = issue_count
            buildrequired = buildrequired_search(srcname, tablename)
            pack_info_dict["buildrequired"] = buildrequired
            subpack = _sub_pack(srcname, tablename)
            pack_info_dict["gitee_url"] = "www.gitee.com/src-openeuler/" + \
                str(srcname)
            pack_info_dict["subpack"] = subpack
            pack_info_dict.update(
                {"license": pack_info_dict.pop("rpm_license")})
            pack_info_dict.update({"pkg_name": pack_info_dict.pop("name")})
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.SUCCESS, pack_info_dict))
    except (SQLAlchemyError, DisconnectionError, Error, AttributeError) as error:
        current_app.logger.error(error)
        return jsonify(
            ResponseCode.response_json(
                ResponseCode.DIS_CONNECTION_DB))


def buildrequired_search(srcname, tablename):
    """
    Source code package one-level compilation dependency
    Args:
        srcname: The name of the source package
        tablename: The name of the table in the database

    Returns:
        Source code package one-level compilation dependency
    """
    with DBHelper(db_name=tablename) as data_name:

        src_pack_obj = data_name.session.query(
            SrcPack).filter_by(name=srcname).first()
        if src_pack_obj is None:
            return None

        src_pack_pkgkey = src_pack_obj.pkgKey
        s_pack_requires_set = data_name.session.query(
            SrcRequires).filter_by(pkgKey=src_pack_pkgkey).all()
        # src_requires pkykey to find the name of the dependent component
        s_pack_requires_names = [
            s_pack_requires_obj.name for s_pack_requires_obj in s_pack_requires_set]

        # Find pkgkey in BinProvides by the name of the dependent component
        b_pack_provides_set = data_name.session.query(BinProvides).filter(
            BinProvides.name.in_(s_pack_requires_names)).all()
        b_pack_provides_pkg_list = [
            b_pack_provides_obj.pkgKey for b_pack_provides_obj in b_pack_provides_set]

        # Go to bin_pack to find the name by pkgkey of BinProvides
        b_bin_pack_set = data_name.session.query(BinPack).filter(
            BinPack.pkgKey.in_(b_pack_provides_pkg_list)).all()
        builddep = [b_bin_pack_obj.name for b_bin_pack_obj in b_bin_pack_set]
        return builddep


def _sub_pack(srcname, tablename):
    """
    One-level installation dependency of the source package
    to generate the binary package
    Args:
        srcname: The name of the source package
        tablename: The name of the table in the database

    Returns:
        One-level installation dependency of the source package to
        generate the binary package
    """
    with DBHelper(db_name=tablename) as data_name:
        src_pack_obj = data_name.session.query(
            SrcPack).filter_by(name=srcname).first()
        if src_pack_obj is None:
            return []
      # Sub-packages generated by the source package
        bin_pack_set = data_name.session.query(
            BinPack).filter_by(src_name=src_pack_obj.name).all()
        pack_list = list()
        for bin_pack_obj in bin_pack_set:
            bin_pack_dict = dict()
            bin_pack_dict['id'] = bin_pack_obj.pkgKey
            bin_pack_dict['name'] = bin_pack_obj.name
            # Sub-package lookup provided components

            bin_provides_set = data_name.session.query(
                BinProvides).filter_by(pkgKey=bin_pack_obj.pkgKey).all()
            provide_list = provide_(tablename, bin_provides_set)
            bin_pack_dict['provides'] = provide_list
            bin_require_set = data_name.session.query(
                BinRequires).filter_by(pkgKey=bin_pack_obj.pkgKey).all()
            require_list = require_(tablename, bin_require_set)
            bin_pack_dict['requires'] = require_list
            pack_list.append(bin_pack_dict)
        return pack_list


def provide_(tablename, bin_provides_set):
    """
    pkgKey goes to the bin_pack table to obtain
    bin_name corresponding to requiredby

    Args:
        tablename: table name
        bin_provides_set: Query set provided by the binary package

    Returns:
        provide_list: Provided list
    """
    with DBHelper(db_name=tablename) as data_name:
        provide_list = []
        for bin_provides_obj in bin_provides_set:
            bin_provides_dict = dict()
            bin_provides_dict['id'] = bin_provides_obj.id
            bin_provides_dict['name'] = bin_provides_obj.name
            reqired_set = data_name.session.query(
                BinRequires).filter_by(name=bin_provides_obj.name).all()
            required_pkgkey_list = [
                reqired_obj.pkgKey for reqired_obj in reqired_set]
            required_bin_set = data_name.session.query(BinPack).filter(
                BinPack.pkgKey.in_(required_pkgkey_list)).all()
            requiredby = [
                required_bin_obj.name for required_bin_obj in required_bin_set]
            bin_provides_dict['requiredby'] = requiredby
            provide_list.append(bin_provides_dict)
        return provide_list


def require_(tablename, bin_require_set):
    """
    pkgKey goes to the bin_pack table to obtain
    bin_name corresponding to provideBy

    Args:
        tablename: table name
        bin_provides_set: Query set provided by the binary package

    Returns:
        require_list: require list
    """
    with DBHelper(db_name=tablename) as data_name:
        # Sub-package to find the required components
        require_list = []

        for bin_require_obj in bin_require_set:
            bin_require_dict = dict()
            bin_require_dict['id'] = bin_require_obj.id
            bin_require_dict['name'] = bin_require_obj.name
            provide_set = data_name.session.query(
                BinProvides).filter_by(name=bin_require_obj.name).all()
            provide_pkg_list = [
                provide_obj.pkgKey for provide_obj in provide_set]
            required_bin_set = data_name.session.query(BinPack).filter(
                BinPack.pkgKey.in_(provide_pkg_list)).all()
            providedby = [
                required_bin_obj.name for required_bin_obj in required_bin_set]
            bin_require_dict['providedby'] = providedby
            require_list.append(bin_require_dict)
        return require_list
