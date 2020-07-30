#!/usr/bin/python3
"""
Description: Get package information and modify package information
functions: get_packages, buildep_packages, sub_packages, get_single_package,
 update_single_package, update_maintaniner_info
"""
from flask import current_app
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.function.searchdb import db_priority

from packageship.libs.dbutils import DBHelper
from packageship.application.models.package import src_pack
from packageship.application.models.package import src_requires
from packageship.application.models.package import bin_pack
from packageship.application.models.package import maintenance_info
from packageship.application.models.package import bin_requires
from packageship.application.models.package import bin_provides
from packageship.libs.exception import Error


def get_packages(dbname):
    """
    Get all packages info in search databases

    Args:
        dbname: Database name
    Returns:
        Package information is returned as a list
    Raises:
        AttributeError: Object does not have this property
        Error: Abnormal error
    """
    with DBHelper(db_name=dbname) as db_name:
        src_pack_queryset = db_name.session.query(src_pack).all()
        if src_pack_queryset is None:
            return None
        resp_list = list()
        for src_pack_obj in src_pack_queryset:
            package = dict()
            package["sourceName"] = src_pack_obj.name
            package["version"] = src_pack_obj.version
            package["license"] = src_pack_obj.rpm_license
            package["sourceURL"] = src_pack_obj.url
            package["rpm_packager"] = src_pack_obj.rpm_packager
            package["maintaniner"] = src_pack_obj.maintaniner
            package["maintainlevel"] = src_pack_obj.maintainlevel
            package["dbname"] = dbname
            resp_list.append(package)
        return resp_list


def get_all_packages(db_name):
    """
    all packages info

    Args:
        db_name: database name
    Returns:
        response code:  response status code
    """
    dbpreority = db_priority()
    if dbpreority is None:
        return jsonify(
            ResponseCode.response_json(ResponseCode.FILE_NOT_FOUND)
        )
    if not db_name:
        response = []
        for dbname in dbpreority:
            query_result = get_packages(dbname)
            if query_result is None:
                return None
            for item in query_result:
                if item is None:
                    query_result.remove(item)
                response.append(item)
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, response)
        )
    if db_name not in dbpreority:
        return jsonify(
            ResponseCode.response_json(ResponseCode.DB_NAME_ERROR)
        )
    response = get_packages(db_name)
    if not response:
        return jsonify(
            ResponseCode.response_json(ResponseCode.PACK_NAME_NOT_FOUND)
        )
    return jsonify(
        ResponseCode.response_json(ResponseCode.SUCCESS, response)
    )


def buildep_packages(dbname, src_pack_pkgkey):
    """
    Query package layer 1 compilation dependency

    Args:
        dbname:  databases name
        src_pack_pkgkey: The ID of the source package
    Returns:
        buildDep Compile dependencies of source packages
    Raises:
        AttributeError: Object does not have this property
    """
    with DBHelper(db_name=dbname) as db_name:
        # srcpack's pkgkey to src_requires find pkgkey
        s_pack_requires_set = db_name.session.query(
            src_requires).filter_by(pkgKey=src_pack_pkgkey).all()
        # src_requires pkykey to find the name of the dependent component
        s_pack_requires_names = [
            s_pack_requires_obj.name for s_pack_requires_obj in s_pack_requires_set]

        # Find pkgkey in bin_provides by the name of the dependent component
        b_pack_provides_set = db_name.session.query(bin_provides).filter(
            bin_provides.name.in_(s_pack_requires_names)).all()
        b_pack_provides_pkg_list = [
            b_pack_provides_obj.pkgKey for b_pack_provides_obj in b_pack_provides_set]

        # Go to bin_pack to find the name by pkgkey of bin_provides
        b_bin_pack_set = db_name.session.query(bin_pack).filter(
            bin_pack.pkgKey.in_(b_pack_provides_pkg_list)).all()
        builddep = [b_bin_pack_obj.name for b_bin_pack_obj in b_bin_pack_set]
        return builddep


def sub_packages(dbname, sourcename):
    """
    Query package layer 1 installation dependency

    Args:
        dbname:  databases name
        src_pack_pkgkey: srcpackage id
    Returns:
        subpack  Source package to binary package, then find the installation dependencies
        of the binary package
    Raises:
         AttributeError: Object does not have this property
    """
    with DBHelper(db_name=dbname) as db_name:
        subpack = dict()
        # The name of src_pack finds the sub-package bin_pack query set
        i_bin_pack_set = db_name.session.query(
            bin_pack).filter_by(src_name=sourcename).all()
        if i_bin_pack_set is None:
            return subpack
        # Find the objects of each sub-package
        for b_bin_pack_obj in i_bin_pack_set:
            i_bin_pack_name = b_bin_pack_obj.name
            i_bin_pack_pkgkey = b_bin_pack_obj.pkgKey
            # Find the names of the components required to install bin_requires
            # dependencies
            i_bin_requires_set = db_name.session.query(
                bin_requires).filter_by(pkgKey=i_bin_pack_pkgkey).all()
            i_bin_requires_names = [
                b_bin_requires_obj.name for b_bin_requires_obj in i_bin_requires_set]
            # Find pkykey in bin_provides by the name of the dependent
            # component
            i_bin_provides_set = db_name.session.query(bin_provides).filter(
                bin_provides.name.in_(i_bin_requires_names))
            i_bin_provides_pkg_list = [
                i_bin_provides_obj.pkgKey for i_bin_provides_obj in i_bin_provides_set]
            # Find the name in bin_pack by pkgkey
            i_bin_pack_set = db_name.session.query(bin_pack).filter(
                bin_pack.pkgKey.in_(i_bin_provides_pkg_list))
            i_bin_pack_names = [
                in_bin_pack_obj.name for in_bin_pack_obj in i_bin_pack_set]
            subpack[i_bin_pack_name] = i_bin_pack_names
        return subpack


def get_single_package(dbname, sourcename):
    """
    Get single packages info

    Args：
        dbname: Database name
        sourcename: Source package name
    Returns：
        package info
    Raises:
        AttributeError: Object does not have this property
    """
    with DBHelper(db_name=dbname) as db_name:
        package = dict()
        src_pack_obj = db_name.session.query(src_pack).filter_by(
            name=sourcename).first()
        if src_pack_obj is None:
            return None
        package["sourceName"] = src_pack_obj.name
        package["version"] = src_pack_obj.version
        package["license"] = src_pack_obj.rpm_license
        package["sourceURL"] = src_pack_obj.url
        package["rpm_packager"] = src_pack_obj.rpm_packager
        package["maintaniner"] = src_pack_obj.maintaniner
        package["maintainlevel"] = src_pack_obj.maintainlevel
        package["dbname"] = dbname
        src_pack_pkgkey = src_pack_obj.pkgKey
        builddep = buildep_packages(dbname, src_pack_pkgkey)
        subpack = sub_packages(dbname, sourcename)
        package['buildDep'] = builddep
        package['subpack'] = subpack
        return package


def get_single(dbnames, sourcename):
    """
    get single package

    Args:
        dbname: database name
        sourcename: source name
    """
    response_data = None
    dbpreority = db_priority()
    if db_priority is None:
        response_data = ResponseCode.FILE_NOT_FOUND

    if not dbnames:
        response = []
        for db_names in dbpreority:
            query_result = get_single_package(db_names, sourcename)
            response.append(query_result)
            for key in response:
                if key is None:
                    response.remove(key)
        if not response:
            return jsonify(
                ResponseCode.response_json(ResponseCode.PACK_NAME_NOT_FOUND)
            )
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, response)
        )

    # Database queries data and catches exceptions
    if dbnames not in dbpreority:
        return jsonify(
            ResponseCode.response_json(ResponseCode.DB_NAME_ERROR)
        )
    response = get_single_package(dbnames, sourcename)
    if response is None:
        response_data = ResponseCode.PACK_NAME_NOT_FOUND
    if response_data is not None:
        return jsonify(ResponseCode.response_json(response_data))
    return jsonify(
        ResponseCode.response_json(ResponseCode.SUCCESS, [response])
    )


def _update_package_info(
        package_name,
        dbname,
        maintainer,
        maintain_level):
    """
    change single package management

    Args:
        package_name: package name
        dbname: Database name
        maintainer: maintainer info
        maintain_level: maintain_level info
    Returns:
        message  success or failed
    Raises:
        AttributeError: Object does not have this property
        SQLAlchemyError: Exception of type
        Error: Abnormal error
    """
    try:
        result_data = True
        with DBHelper(db_name=dbname) as data_name:
            update_obj = data_name.session.query(
                src_pack).filter_by(name=package_name).first()
            if update_obj is None:
                return False
            update_obj.maintaniner = maintainer
            update_obj.maintainlevel = maintain_level
            data_name.session.commit()
            name = update_obj.name
            version = update_obj.version
        with DBHelper(db_name='maintenance.information') as dbs_name:
            information_obj = dbs_name.session.query(maintenance_info).filter_by(
                name=package_name, version=version).first()
            if information_obj is None:
                information = maintenance_info(
                    name=name,
                    version=version,
                    maintaniner=maintainer,
                    maintainlevel=maintain_level)
                dbs_name.session.add(information)
                dbs_name.session.commit()
            else:
                information_obj.maintaniner = maintainer
                information_obj.maintainlevel = maintain_level
                dbs_name.session.commit()
        return result_data
    except (AttributeError, SQLAlchemyError, Error) as attri_error:
        current_app.logger.error(attri_error)
        raise attri_error
