#!/usr/bin/python3
"""
Description: Get package information and modify package information
functions: get_packages, buildep_packages, sub_packages, get_single_package,
 update_single_package, update_maintaniner_info
"""
from flask import current_app

from packageship.libs.dbutils import DBHelper
from packageship.application.models.package import src_pack
from packageship.application.models.package import pack_provides
from packageship.application.models.package import maintenance_info
from packageship.application.models.package import pack_requires
from packageship.application.models.package import bin_pack
from packageship.libs.exception import Error


def get_packages(dbname):
    """
    Description: Get all packages info
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
        resp_list = []
        for src_pack_obj in src_pack_queryset:
            package = {}
            package["sourceName"] = src_pack_obj.name
            package["version"] = src_pack_obj.version
            package["license"] = src_pack_obj.license
            package["maintainer"] = src_pack_obj.Maintaniner
            package["maintainlevel"] = src_pack_obj.MaintainLevel
            package["sourceURL"] = src_pack_obj.sourceURL
            package["maintainlevel"] = src_pack_obj.MaintainLevel
            package["downloadURL"] = src_pack_obj.downloadURL
            package["dbname"] = dbname
            resp_list.append(package)
        return resp_list


def buildep_packages(dbname, src_pack_id):
    """
    Description: Query package layer 1 compilation dependency
    Args:
        dbname:  databases name
        src_pack_id: The ID of the source package
    Returns:
        buildDep Compile dependencies of source packages
    Raises:
        AttributeError: Object does not have this property
    """
    with DBHelper(db_name=dbname) as db_name:
        b_pack_requires_set = db_name.session.query(
            pack_requires).filter_by(srcIDkey=src_pack_id).all()
        b_dep_proid_keys = [
            dep_proid_obj.depProIDkey for dep_proid_obj in b_pack_requires_set]
        b_pack_pro_set = db_name.session.query(pack_provides).filter(
            pack_provides.id.in_(b_dep_proid_keys)).all()
        b_bin_pack_ids = [
            bin_pack_obj.binIDkey for bin_pack_obj in b_pack_pro_set]
        b_bin_pack_set = db_name.session.query(bin_pack).filter(
            bin_pack.id.in_(b_bin_pack_ids)).all()
        builddep = [bin_pack_obj.name for bin_pack_obj in b_bin_pack_set]
        return builddep


def sub_packages(dbname, src_pack_id):
    """
    Description: Query package layer 1 installation dependency
    Args:
        dbname:  databases name
        src_pack_id: srcpackage id
    Returns:
        subpack  Source package to binary package, then find the installation dependencies
     of the binary package
    Raises:
         AttributeError: Object does not have this property
    """
    with DBHelper(db_name=dbname) as db_name:
        subpack = {}
        i_bin_pack_set = db_name.session.query(
            bin_pack).filter_by(srcIDkey=src_pack_id).all()
        i_bin_pack_ids = [
            bin_pack_obj.id for bin_pack_obj in i_bin_pack_set]
        for i_bin_pack_id in i_bin_pack_ids:
            i_bin_pack_name = db_name.session.query(
                bin_pack).filter_by(id=i_bin_pack_id).first().name
            i_pack_req_set = db_name.session.query(
                pack_requires).filter_by(binIDkey=i_bin_pack_id).all()
            i_dep_proid_keys = [
                dep_proid_obj.depProIDkey for dep_proid_obj in i_pack_req_set]
            i_dep_proid_keys = list(set(i_dep_proid_keys))
            i_pack_provides_set = db_name.session.query(pack_provides).filter(
                pack_provides.id.in_(i_dep_proid_keys)).all()
            i_bin_pack_ids = [
                bin_pack_obj.binIDkey for bin_pack_obj in i_pack_provides_set]
            i_bin_pack_set = db_name.session.query(bin_pack).filter(
                bin_pack.id.in_(i_bin_pack_ids)).all()
            i_bin_pack_names = [
                bin_pack_obj.name for bin_pack_obj in i_bin_pack_set]
            subpack[i_bin_pack_name] = i_bin_pack_names
        return subpack


def get_single_package(dbname, sourcename):
    """
    Description: Get all packages info
    Args：
        dbname: Database name
        sourcename: Source package name
    Returns：
        package info
    Raises:
        AttributeError: Object does not have this property
    """
    with DBHelper(db_name=dbname) as db_name:
        package = {}
        src_pack_obj = db_name.session.query(src_pack).filter_by(
            name=sourcename).first()
        package["sourceName"] = src_pack_obj.name
        package["version"] = src_pack_obj.version
        package["license"] = src_pack_obj.license
        package["maintainer"] = src_pack_obj.Maintaniner
        package["maintainlevel"] = src_pack_obj.MaintainLevel
        package["sourceURL"] = src_pack_obj.sourceURL
        package["downloadURL"] = src_pack_obj.downloadURL
        package["dbname"] = dbname
        src_pack_id = src_pack_obj.id
        builddep = buildep_packages(dbname, src_pack_id)
        subpack = sub_packages(dbname, src_pack_id)
        package['buildDep'] = builddep
        package['subpack'] = subpack
        return package


def update_single_package(
        package_name,
        dbname,
        maintainer,
        maintain_level):
    """
    Description: change single package management
    Args：
        package_name: package name
        dbname: Database name
        maintainer: maintainer info
        maintain_level: maintain_level info
    Returns：
        message  success or failed
    Raises:
        AttributeError: Object does not have this property
        TypeError: Abnormal error
    """
    with DBHelper(db_name=dbname) as db_name:
        update_obj = db_name.session.query(
            src_pack).filter_by(name=package_name).first()
        update_obj.Maintaniner = maintainer
        update_obj.MaintainLevel = maintain_level
        db_name.session.commit()


def update_maintaniner_info(package_name,
                            dbname,
                            maintaniner,
                            maintainlevel):
    """
    Description: update separately maintaniner info
    Args：
       package_name: package name
       dbname: Database name
       maintainer: maintainer info
       maintain_level: maintain_level info
    Returns：
       message  success or failed
    Raises:
       AttributeError: Object does not have this property
       Error: Abnormal error
    """
    with DBHelper(db_name=dbname) as db_name:
        src_pack_obj = db_name.session.query(src_pack).filter_by(
            name=package_name).first()
        name = src_pack_obj.name
        version = src_pack_obj.version
    with DBHelper(db_name='maintenance.information') as dbs_name:
        try:
            information_obj = dbs_name.session.query(maintenance_info).filter_by(
                name=package_name, version=version).first()
            if information_obj is None:
                information = maintenance_info(
                    name=name,
                    version=version,
                    maintaniner=maintaniner,
                    maintainlevel=maintainlevel)
                dbs_name.session.add(information)
                dbs_name.session.commit()
            else:
                information_obj.maintaniner = maintaniner
                information_obj.maintainlevel = maintainlevel
                dbs_name.session.commit()
        except (AttributeError, Error) as attri_error:
            current_app.logger.error(attri_error)
            return
