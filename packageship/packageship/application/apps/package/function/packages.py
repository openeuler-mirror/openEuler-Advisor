#!/usr/bin/python3
"""
Description: Get package information and modify package information
functions: get_packages, buildep_packages, sub_packages, get_single_package,
 update_single_package, update_maintaniner_info
"""
import math


from flask import current_app, jsonify
from sqlalchemy import text
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
            pack_info_dict = parsing_maintainner(srcname, pack_info_dict)
            issue_count = database_name.session.query(PackagesIssue).filter_by(
                pkg_name=package_info_obj.name).count()
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


def parsing_maintainner(srcname, pack_info_dict):
    """
    Single package query maintainer and maintainlevel
    Args:
        srcname: Source package name
        pack_info_dict:
    Returns: Dictionary of package information

    """
    with DBHelper(db_name="lifecycle") as database_name:
        maintainer_obj = database_name.session.query(
            PackagesMaintainer).filter_by(name=srcname).first()
        if maintainer_obj is None:
            pack_info_dict["maintainer"] = None
            pack_info_dict["maintainlevel"] = None
        else:
            pack_info_dict["maintainer"] = maintainer_obj.maintainer
            pack_info_dict["maintainlevel"] = maintainer_obj.maintainlevel
        return pack_info_dict


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


def helper(cls):
    """
    Auxiliary function
    The returned data format is converted,
    the main function is to convert a dictionary to a list

    Args:
        cls: Data before conversion
    Returns:
        Converted data
    """
    for obj in cls:
        if "provides" in obj:
            obj["provides"] = list(obj["provides"].values())
            for values_p in obj["provides"]:
                if 'requiredby' in values_p:
                    values_p['requiredby'] = list(
                        values_p['requiredby'].values())
        if "requires" in obj:
            obj["requires"] = list(obj["requires"].values())
            for values_r in obj["requires"]:
                if "providedby" in values_r:
                    values_r['providedby'] = list(
                        values_r['providedby'].values())


def _sub_pack(src_name, table_name):
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
    with DBHelper(db_name=table_name) as database:
        sql_str = """
            SELECT DISTINCT
                b2.pkgKey AS sub_id,
                b2.name AS sub_name,
                pro.id AS sub_pro_id,
                pro.name AS sub_pro_name,
                b1.name AS sub_reqby_name
            FROM
                ( select pkgKey,name,src_name from bin_pack where src_name=:src_name) b2
                left join bin_provides pro on b2.pkgKey=pro.pkgKey
                LEFT JOIN bin_requires req ON req.name = pro.name
                LEFT JOIN bin_pack b1 ON req.pkgKey = b1.pkgKey;
                """
        res = {}
        res_pro = database.session.execute(
            text(sql_str), {"src_name": src_name}).fetchall()

        for pro_obj in res_pro:
            if pro_obj.sub_name not in res:
                res[pro_obj.sub_name] = {
                    "id": pro_obj.sub_id,
                    "name": pro_obj.sub_name,
                    "provides": {
                        pro_obj.sub_pro_name: {
                            "id": pro_obj.sub_pro_id,
                            "name": pro_obj.sub_pro_name,
                            "requiredby": {
                                pro_obj.sub_reqby_name: pro_obj.sub_reqby_name
                            } if pro_obj.sub_reqby_name else {}
                        }
                    } if pro_obj.sub_pro_name else {}
                }
            else:
                pro_info = res[pro_obj.sub_name]["provides"]
                if pro_obj.sub_pro_name in pro_info:
                    pro_info[pro_obj.sub_pro_name]["requiredby"].update(
                        {pro_obj.sub_reqby_name: pro_obj.sub_reqby_name})
                else:
                    pro_info.update(
                        {
                            pro_obj.sub_pro_name: {
                                "id": pro_obj.sub_pro_id,
                                "name": pro_obj.sub_pro_name,
                                "requiredby": {
                                    pro_obj.sub_reqby_name: pro_obj.sub_reqby_name
                                } if pro_obj.sub_reqby_name else {}
                            } if pro_obj.sub_pro_name else {}
                        }
                    )

        sql_re = """
            SELECT DISTINCT
                b2.pkgKey AS sub_id,
                b2.name AS sub_name,
                req.id AS sub_req_id,
                req.name AS sub_req_name,
                b1.name AS sub_proby_name
            FROM
                ( SELECT pkgKey, name, src_name FROM bin_pack WHERE src_name = :src_name ) b2
                LEFT JOIN bin_requires req ON b2.pkgKey = req.pkgKey
                LEFT JOIN bin_provides pro ON pro.name = req.name
                LEFT JOIN bin_pack b1 ON pro.pkgKey = b1.pkgKey;
                """
        res_req = database.session.execute(
            text(sql_re), {"src_name": src_name}).fetchall()

        for req_obj in res_req:
            sub_pkg_info = res[req_obj.sub_name]
            # if req_obj.sub_name not in sub_pkg_info:

            if "requires" not in sub_pkg_info:
                if not req_obj.sub_req_name:
                    sub_pkg_info['requires'] = {}
                else:
                    sub_pkg_info.update(
                        {
                            "requires": {
                                req_obj.sub_req_name: {
                                    "id": req_obj.sub_req_id,
                                    "name": req_obj.sub_req_name,
                                    "providedby": {
                                        req_obj.sub_proby_name: req_obj.sub_proby_name
                                    } if req_obj.sub_proby_name else {}
                                }
                            }
                        }
                    )
            else:
                req_info = sub_pkg_info["requires"]
                if req_obj.sub_req_name in req_info:
                    req_info[req_obj.sub_req_name]["providedby"].update(
                        {req_obj.sub_proby_name: req_obj.sub_proby_name})
                else:
                    req_info.update(
                        {
                            req_obj.sub_req_name: {
                                "id": req_obj.sub_req_id,
                                "name": req_obj.sub_req_name,
                                "providedby": {
                                    req_obj.sub_proby_name: req_obj.sub_proby_name
                                } if req_obj.sub_proby_name else {}
                            }
                        }
                    )
        helper([values for k, values in res.items()])
        return (list(res.values()))
