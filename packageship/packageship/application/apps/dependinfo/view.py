#!/usr/bin/python3
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
# ******************************************************************************/
"""
description: Interface processing
class: BeDepend, BuildDepend, InitSystem, InstallDepend, Packages,
Repodatas, SelfDepend, SinglePack
"""
from flask import request
from flask import jsonify
from flask_restful import Resource
from packageship.libs.log import Log

from packageship.application.apps.package.serialize import SelfDependSchema
from packageship.application.apps.package.serialize import BeDependSchema
from packageship.application.apps.package.serialize import have_err_db_name
from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.function.searchdb import db_priority
from packageship.application.apps.package.function.constants import ListNode
from .function.graphcache import bedepend
from .function.graphcache import self_build as selfbuild

DB_NAME = 0
LOGGER = Log(__name__)


# pylint: disable = no-self-use
# pylint: disable = too-many-locals

# licensed under the Mulan PSL v2.
class ParseDependPackageMethod(Resource):
    """
    Description: Common Method
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        self.statistics = dict()

    def _parse_database(self, db_list):
        data_name = []
        for _, v in enumerate(db_list):
            data_name.append({"database": v, "binary_num": 0, "source_num": 0})
        return data_name

    # pylint: disable = too-many-nested-blocks
    def parse_depend_package(self, package_all, db_list=None):
        """
        Description: Parsing package data with dependencies
        Args:
            package_all: http request response content
        Returns:
            Summarized data table
        Raises:
        """
        depend_bin_data = []
        depend_src_data = []
        statistics = self._parse_database(db_list)
        if isinstance(package_all, dict):
            for bin_package, package_depend in package_all.items():
                if isinstance(package_depend, list) and \
                        package_depend[ListNode.SOURCE_NAME] != 'source':
                    row_data = {"binary_name": bin_package,
                                "source_name": package_depend[ListNode.SOURCE_NAME],
                                "version": package_depend[ListNode.VERSION],
                                "database": package_depend[ListNode.DBNAME]}
                    row_src_data = {"source_name": package_depend[ListNode.SOURCE_NAME],
                                    "version": package_depend[ListNode.VERSION],
                                    "database": package_depend[ListNode.DBNAME]}
                    if package_depend[ListNode.DBNAME] not in self.statistics:
                        self.statistics[package_depend[ListNode.DBNAME]] = {
                            'binary': [],
                            'source': []
                        }
                    if bin_package not in \
                            self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                        self.statistics[package_depend[ListNode.DBNAME]]['binary'].append(
                            bin_package)
                        for con in statistics:
                            if package_depend[ListNode.DBNAME] == con["database"]:
                                con["binary_num"] += 1
                    if package_depend[ListNode.SOURCE_NAME] not in \
                            self.statistics[package_depend[ListNode.DBNAME]]['source']:
                        self.statistics[package_depend[ListNode.DBNAME]]['source'].append(
                            package_depend[ListNode.SOURCE_NAME])
                        for con in statistics:
                            if package_depend[ListNode.DBNAME] == con["database"]:
                                con["source_num"] += 1
                    depend_bin_data.append(row_data)
                    depend_src_data.append(row_src_data)
        src_data = [dict(t) for t in set([tuple(d.items()) for d in depend_src_data])]
        statistics_table = {
            "binary_dicts": depend_bin_data,
            "source_dicts": src_data,
            "statistics": statistics}
        return statistics_table


class InfoSelfDepend(ParseDependPackageMethod):
    """
    Description: querying install and build depend for a package
                 and others which has the same src name
    Restful API: post
    changeLog:
    """

    def _parse_bin_package(self, bin_packages, db_list):
        """
        Description: Parsing binary result data
        Args:
            bin_packages: Binary package data
        Returns:
        Raises:
        """
        bin_package_data = []
        statistics = self._parse_database(db_list)
        if bin_packages:
            for bin_package, package_depend in bin_packages.items():
                # distinguish whether the current data is the data of the root node
                if isinstance(package_depend, list) and package_depend[ListNode.PARENT_LIST][DB_NAME][
                    DB_NAME] != 'root':
                    row_data = {"binary_name": bin_package,
                                "source_name": package_depend[ListNode.SOURCE_NAME],
                                "version": package_depend[ListNode.VERSION],
                                "database": package_depend[ListNode.DBNAME]}
                    for con in statistics:
                        if package_depend[ListNode.DBNAME] == con["database"]:
                            con["binary_num"] += 1
                    if package_depend[ListNode.DBNAME] not in self.statistics:
                        self.statistics[package_depend[ListNode.DBNAME]] = {
                            'binary': [],
                            'source': []
                        }
                    if bin_package not in \
                            self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                        self.statistics[package_depend[ListNode.DBNAME]]['binary'].append(
                            bin_package)
                    bin_package_data.append(row_data)
        return bin_package_data, statistics

    def _parse_src_package(self, src_packages, db_list):
        """
        Description: Source package data analysis
        Args:
            src_packages: Source package

        Returns:
            Source package data
        Raises:

        """
        src_package_data = []
        statistics = db_list
        if src_packages:
            for src_package, package_depend in src_packages.items():
                if isinstance(package_depend, list):
                    row_data = {"source_name": src_package,
                                "version": package_depend[ListNode.VERSION],
                                "database": package_depend[DB_NAME]}
                    for con in statistics:
                        if package_depend[DB_NAME] == con["database"]:
                            con["source_num"] += 1
                    if package_depend[DB_NAME] not in self.statistics:
                        self.statistics[package_depend[DB_NAME]] = {
                            'binary': [],
                            'source': []
                        }
                    if src_package not in self.statistics[package_depend[DB_NAME]]['source']:
                        self.statistics[package_depend[DB_NAME]]['source'].append(src_package)
                    src_package_data.append(row_data)
        return src_package_data, statistics

    def post(self):
        """
        Query a package's all dependencies including install and build depend
        (support quering a binary or source package in one or more databases)
        Args:
            packageName:package name
            packageType: source/binary
            selfBuild :0/1
            withSubpack: 0/1
            dbPreority：the array for database preority
        Returns:
            for
            example::
                {
                  "code": "",
                  "data": "",
                  "msg": ""
                }
        """
        schema = SelfDependSchema()
        data = request.get_json()
        validate_err = schema.validate(data)

        if validate_err:
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        pkg_name = data.get("packagename")
        db_pri = db_priority()
        if not db_pri:
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.FILE_NOT_FIND_ERROR
                )
            )
        db_list = data.get("db_list") if data.get("db_list") \
            else db_pri
        self_build = data.get("selfbuild", 0)
        with_sub_pack = data.get("withsubpack", 0)
        pack_type = data.get("packtype", "binary")
        if have_err_db_name(db_list, db_pri):
            return jsonify(
                ResponseCode.response_json(ResponseCode.DB_NAME_ERROR)
            )
        query_parameter = {"db_list": db_list,
                           "packagename": pkg_name,
                           "selfbuild": self_build,
                           "withsubpack": with_sub_pack,
                           "packtype": pack_type}

        result_data = selfbuild(query_parameter)
        response_code = result_data["code"]
        binary_dicts = result_data["binary_dicts"]
        source_dicts = result_data["source_dicts"]
        if not all([binary_dicts, source_dicts]):
            return jsonify(
                ResponseCode.response_json(response_code)
            )
        bin_package, package_count = self._parse_bin_package(binary_dicts, db_list)
        src_package, statistics = self._parse_src_package(source_dicts, package_count)
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, data={
                "binary_dicts": bin_package,
                "source_dicts": src_package,
                "statistics": statistics
            })
        )


class InfoBeDepend(ParseDependPackageMethod):
    """
    Description: querying be installed and built depend for a package
                 and others which has the same src name
    Restful API: post
    changeLog:
    """

    def post(self):
        """
        Query a package's all dependencies including
        be installed and built depend
        Args:
            packageName:package name
            withSubpack: 0/1
            dbname:database name
        Returns:
            for
            example::
                resultList[
                    restult[
                        binaryName:
                        srcName:
                        dbName:
                        type: beinstall or bebuild, which depend on the function
                        childNode: the binary package name which is the be built/installed
                                   depend for binaryName
                    ]
                ]
        """
        schema = BeDependSchema()
        data = request.get_json()
        validate_err = schema.validate(data)
        if validate_err:
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        package_name = data.get("packagename")
        with_sub_pack = data.get("withsubpack")
        db_name = data.get("dbname")
        if db_name not in db_priority():
            return jsonify(
                ResponseCode.response_json(ResponseCode.DB_NAME_ERROR)
            )
        query_parameter = {"packagename": package_name,
                           "withsubpack": with_sub_pack,
                           "dbname": db_name}

        result_data = bedepend(query_parameter)
        res_code = result_data["code"]
        res_dict = result_data["bedepend"]
        if not res_dict:
            return jsonify(
                ResponseCode.response_json(res_code)
            )
        result_dict = self.parse_depend_package(res_dict, [db_name])
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, data=result_dict)
        )


class DataBaseInfo(Resource):
    """
     Get  the database name of all packages
    """

    def get(self):
        """
        Returns: name_list: database name list
        """
        name_list = db_priority()
        if not name_list:
            return jsonify(
                ResponseCode.response_json(ResponseCode.NOT_FOUND_DATABASE_INFO)
            )
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, data=name_list)
        )
