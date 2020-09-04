#!/usr/bin/python3
"""
description: Interface processing
class: BeDepend, BuildDepend, InitSystem, InstallDepend, Packages,
Repodatas, SelfDepend, SinglePack
"""
import yaml
from flask import request
from flask import jsonify
from flask import current_app
from flask_restful import Resource
from sqlalchemy.exc import DisconnectionError

from packageship import system_config
from packageship.application.initsystem.data_import import InitDataBase
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.exception import Error
from packageship.libs.exception import ContentNoneException
from packageship.libs.exception import DataMergeException
from packageship.libs.exception import ConfigurationException
from packageship.libs.log import Log
from packageship.system_config import DATABASE_FILE_INFO
from .function.constants import ResponseCode
from .function.packages import get_all_package_info
from .function.packages import sing_pack
from .function.searchdb import db_priority
from .serialize import AllPackagesSchema, SinglepackSchema

from .serialize import DeletedbSchema
from .serialize import InitSystemSchema
from .serialize import BeDependSchema
from .function.be_depend import BeDepend as be_depend
from .function.install_depend import InstallDepend as installdepend
from .function.build_depend import BuildDepend as builddepend
from .function.self_depend import SelfDepend as self_depend
from .serialize import InstallDependSchema
from .serialize import BuildDependSchema
from .serialize import SelfDependSchema
from .serialize import have_err_db_name

LOGGER = Log(__name__)


# pylint: disable = no-self-use


class Packages(Resource):
    """
    Description: interface for package info management
    Restful API: get
    changeLog:
    """

    def get(self):
        """
        Get all package info from a database

        Args:
            dbName: Data path name, not required parameter
        Returns:
            for
            example::
               {
                   "code": "",
                    "data": [{
                        "dbname": "",
                        "license": "",
                        "maintainlevel":,
                        "maintaniner": ,
                        "rpm_packager": "",
                        "sourceName": "",
                        "sourceURL": "",
                        "version": ""
                        }],
                "msg": ""
                }
        Raises:
            DisconnectionError: Unable to connect to database exception
            AttributeError: Object does not have this property
            Error: Abnormal error
        """
        # Get verification parameters
        schema = AllPackagesSchema()
        data = request.args
        if schema.validate(data):
            response = ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            response['total_count'] = None
            response['total_page'] = None
            return jsonify(response)
        table_name = data.get("table_name")
        page_num = data.get("page_num")
        page_size = data.get("page_size")
        src_name = data.get("query_pkg_name", None)
        maintainner = data.get("maintainner", None)
        maintainlevel = data.get("maintainlevel", None)
        result = get_all_package_info(
            table_name,
            page_num,
            page_size,
            src_name,
            maintainner,
            maintainlevel)
        return result


class SinglePack(Resource):
    """
    description: single package management
    Restful API: get
    ChangeLog:
    """

    def get(self):
        """
        Searching a package info

        Args:
            dbName: Database name, not required parameter
            sourceName: Source code package name, must pass
        Returns:
            for
            examples::
                {
                "code": "",
                "data": [{
                "buildDep": [],
                "dbname": "",
                "license": "",
                "maintainlevel": "",
                "maintaniner": "",
                "rpm_packager": "",
                "sourceName": "",
                "sourceURL": "",
                "subpack": { },
                "version": ""}],
                "msg": ""
                 }
        Raises:
            DisconnectionError: Unable to connect to database exception
            AttributeError: Object does not have this property
            TypeError: Exception of type
            Error: Abnormal error
        """
        # Get verification parameters
        schema = SinglepackSchema()
        data = request.args
        if schema.validate(data):
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        srcname = data.get("pkg_name")
        tablename = data.get("table_name")
        result = sing_pack(srcname, tablename)
        return result


class InstallDepend(Resource):
    """
    Description: install depend of binary package
    Restful API: post
    changeLog:
    """

    def post(self):
        """
        Query a package's install depend(support
        querying in one or more databases)

        Args:
            binaryName
            dbPreority: the array for database preority
        Returns:
            resultDict{
                binary_name: //binary package name
                [
                    src, //the source package name for
                            that binary packge
                    dbname,
                    version,
                    [
                        parent_node, //the binary package name which is
                                       the install depend for binaryName
                        type //install  install or build, which
                                depend on the function
                    ]
                ]
            }
        Raises:
        """
        schema = InstallDependSchema()

        data = request.get_json()
        validate_err = schema.validate(data)
        if validate_err:
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        pkg_name = data.get("binaryName")

        db_pri = db_priority()
        if not db_pri:
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.FILE_NOT_FIND_ERROR
                )
            )

        db_list = data.get("db_list") if data.get("db_list") \
            else db_pri

        if not all([pkg_name, db_list]):
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )

        if have_err_db_name(db_list, db_pri):
            return jsonify(
                ResponseCode.response_json(ResponseCode.DB_NAME_ERROR)
            )

        response_code, install_dict, not_found_components = \
            installdepend(db_list).query_install_depend([pkg_name])

        if not install_dict:
            return jsonify(
                ResponseCode.response_json(response_code)
            )
        elif len(install_dict) == 1 and install_dict.get(pkg_name)[2] == 'NOT FOUND':
            return jsonify(
                ResponseCode.response_json(ResponseCode.PACK_NAME_NOT_FOUND)
            )
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, data={
                "install_dict": install_dict,
                'not_found_components': list(not_found_components)
            })
        )


class BuildDepend(Resource):
    """
    Description: build depend of binary package
    Restful API: post
    changeLog:
    """

    def post(self):
        """
        Query a package's build depend and
        build depend package's install depend
        (support querying in one or more databases)

        Args:
            sourceName :name of the source package
            dbPreority：the array for database preority
        Returns:
            for
            example::
                {
                  "code": "",
                  "data": "",
                  "msg": ""
                }
        Raises:
        """
        schema = BuildDependSchema()

        data = request.get_json()
        if schema.validate(data):
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        pkg_name = data.get("sourceName")

        db_pri = db_priority()

        if not db_pri:
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.FILE_NOT_FIND_ERROR
                )
            )

        db_list = data.get("db_list") if data.get("db_list") \
            else db_pri

        if have_err_db_name(db_list, db_pri):
            return jsonify(
                ResponseCode.response_json(ResponseCode.DB_NAME_ERROR)
            )

        build_ins = builddepend([pkg_name], db_list)

        res_code, res_dict, _, not_found_com = build_ins.build_depend_main()
        if res_dict:
            res_code = ResponseCode.SUCCESS
        else:
            return jsonify(
                ResponseCode.response_json(
                    res_code
                )
            )

        return jsonify(
            ResponseCode.response_json(
                res_code,
                data={
                    'build_dict': res_dict,
                    'not_found_components': list(not_found_com)
                }
            )
        )


class SelfDepend(Resource):
    """
    Description: querying install and build depend for a package
                 and others which has the same src name
    Restful API: post
    changeLog:
    """

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
        response_code, binary_dicts, source_dicts, not_fd_components = \
            self_depend(db_list).query_depend(pkg_name, int(self_build),
                                              int(with_sub_pack), pack_type)

        if not all([binary_dicts, source_dicts]):
            return jsonify(
                ResponseCode.response_json(response_code)
            )

        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, data={
                "binary_dicts": binary_dicts,
                "source_dicts": source_dicts,
                "not_found_components": list(not_fd_components)
            })
        )


class BeDepend(Resource):
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

        bedepnd_ins = be_depend(package_name, db_name, with_sub_pack)

        res_dict = bedepnd_ins.main()

        if not res_dict:
            return jsonify(
                ResponseCode.response_json(ResponseCode.PACK_NAME_NOT_FOUND)
            )
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, data=res_dict)
        )


class Repodatas(Resource):
    """
    description: Get database information and delete database
    Restful API: get, delete
    ChangeLog:
    """

    def get(self):
        """
        get all database

        Returns:
            for
            example::
                {
                  "code": "",
                  "data": [
                        {
                            "database_name": "",
                            "priority": "",
                            "status": ""
                        }
                    ],
                    "msg": ""
                }
        Raises:
            FileNotFoundError: File not found exception
            TypeError: Exception of wrong type
            Error: abnormal Error
        """
        try:
            with open(DATABASE_FILE_INFO, 'r', encoding='utf-8') as file_context:
                init_database_date = yaml.load(
                    file_context.read(), Loader=yaml.FullLoader)
                if init_database_date is None:
                    raise ContentNoneException(
                        "The content of the database initialization configuration "
                        "file cannot be empty ")
                init_database_date.sort(
                    key=lambda x: x['priority'], reverse=False)
                return jsonify(
                    ResponseCode.response_json(
                        ResponseCode.SUCCESS,
                        data=init_database_date))
        except (FileNotFoundError, TypeError, Error) as file_not_found:
            current_app.logger.error(file_not_found)
            return jsonify(
                ResponseCode.response_json(ResponseCode.FILE_NOT_FOUND)
            )

    def delete(self):
        """
        get all database

        Returns:
            for
            example::
                {
                  "code": "",
                  "data": "",
                  "msg": ""
                }
        Raises:
            FileNotFoundError: File not found exception,
            TypeError: Exception of wrong type
            Error: Abnormal error
        """
        schema = DeletedbSchema()
        data = request.args
        if schema.validate(data):
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        db_name = data.get("dbName")
        db_list = db_priority()
        if db_list is None:
            return jsonify(
                ResponseCode.response_json(ResponseCode.FILE_NOT_FOUND)
            )
        if db_name not in db_priority():
            return jsonify(
                ResponseCode.response_json(ResponseCode.DB_NAME_ERROR)
            )
        try:
            drop_db = InitDataBase()
            del_result = drop_db.delete_db(db_name)
            if del_result is False:
                return jsonify(
                    ResponseCode.response_json(ResponseCode.DELETE_DB_ERROR))
            return jsonify(
                ResponseCode.response_json(ResponseCode.SUCCESS)
            )
        except (FileNotFoundError, TypeError, Error) as error:
            current_app.logger.error(error)
            return jsonify(
                ResponseCode.response_json(ResponseCode.DELETE_DB_ERROR)
            )


class InitSystem(Resource):
    """
    description: Initialize database
    Restful API: post
    ChangeLog:
    """

    def post(self):
        """
        InitSystem

        Returns:
            for
            example::
                {
                  "code": "",
                  "data": "",
                  "msg": ""
                }
        Raises:
            ContentNoneException: Unable to connect to the exception of the database
            DisconnectionError：Exception connecting to database
            TypeError：Exception of wrong type
            DataMergeException：Exception of merging data
            FileNotFoundError：File not found exception
            Error: abnormal Error
        """
        schema = InitSystemSchema()

        data = request.get_json()
        validate_err = schema.validate(data)
        if validate_err:
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.PARAM_ERROR))
        configfile = data.get("configfile", None)
        try:
            abnormal = None
            if not configfile:
                _config_path = ReadConfig(
                    system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
                InitDataBase(config_file_path=_config_path).init_data()
            else:
                InitDataBase(config_file_path=configfile).init_data()
        except ContentNoneException as content_none_error:
            LOGGER.logger.error(content_none_error)
            abnormal = ResponseCode.CONFIGFILE_PATH_EMPTY
        except DisconnectionError as dis_connection_error:
            LOGGER.logger.error(dis_connection_error)
            abnormal = ResponseCode.DIS_CONNECTION_DB
        except TypeError as type_error:
            LOGGER.logger.error(type_error)
            abnormal = ResponseCode.TYPE_ERROR
        except ConfigurationException as error:
            LOGGER.logger.error(error)
            abnormal = error
            return jsonify(ResponseCode.response_json('5000', msg=abnormal.message))
        except DataMergeException as data_merge_error:
            LOGGER.logger.error(data_merge_error)
            abnormal = ResponseCode.DATA_MERGE_ERROR
        except FileNotFoundError as file_not_found_error:
            LOGGER.logger.error(file_not_found_error)
            abnormal = ResponseCode.FILE_NOT_FIND_ERROR
        except Error as error:
            LOGGER.logger.error(error)
            abnormal = ResponseCode.FAILED_CREATE_DATABASE_TABLE
        if abnormal is not None:
            return jsonify(ResponseCode.response_json(abnormal))
        db_list = db_priority()
        if db_list is None:
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.FAILED_CREATE_DATABASE_TABLE))
        return jsonify(ResponseCode.response_json(ResponseCode.SUCCESS))
