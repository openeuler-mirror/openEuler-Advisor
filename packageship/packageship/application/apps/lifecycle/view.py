#!/usr/bin/python3
"""
Life cycle related api interface
"""
import io
import json
import math
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import yaml

from flask import request
from flask import jsonify, make_response
from flask import current_app
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import DisconnectionError, SQLAlchemyError

from packageship import system_config
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.exception import Error
from packageship.application.apps.package.function.constants import ResponseCode
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper
from packageship.application.models.package import PackagesIssue
from packageship.application.models.package import Packages
from packageship.application.models.package import PackagesMaintainer
from packageship.libs.log import Log
from .serialize import IssueDownloadSchema, PackagesDownloadSchema, IssuePageSchema, IssueSchema
from ..package.serialize import DataFormatVerfi, UpdatePackagesSchema
from .function.gitee import Gitee as gitee

LOGGER = Log(__name__)


# pylint: disable = no-self-use

class DownloadFile(Resource):
    """
        Download the content of the issue or the excel file of the package content
    """

    def _download_excel(self, file_type, table_name=None):
        """
            Download excel file
        """
        file_name = 'packages.xlsx'
        if file_type == 'packages':
            download_content = self.__get_packages_content(table_name)
        else:
            file_name = 'issues.xlsx'
            download_content = self.__get_issues_content()
        if download_content is None:
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.SERVICE_ERROR))
        pd_dataframe = self.__to_dataframe(download_content)

        _response = self.__bytes_save(pd_dataframe)
        return self.__set_response_header(_response, file_name)

    def __bytes_save(self, data_frame):
        """
            Save the file content in the form of a binary file stream
        """
        try:
            bytes_io = io.BytesIO()
            writer = pd.ExcelWriter(  # pylint: disable=abstract-class-instantiated
                bytes_io, engine='xlsxwriter')
            data_frame.to_excel(writer, sheet_name='Summary', index=False)
            writer.save()
            writer.close()
            bytes_io.seek(0)
            _response = make_response(bytes_io.getvalue())
            bytes_io.close()
            return _response
        except (IOError, Error) as io_error:
            current_app.logger.error(io_error)
            return make_response()

    def __set_response_header(self, response, file_name):
        """
            Set http response header information
        """
        response.headers['Content-Type'] = \
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response.headers["Cache-Control"] = "no-cache"
        response.headers['Content-Disposition'] = 'attachment; filename={file_name}'.format(
            file_name=file_name)
        return response

    def __get_packages_content(self, table_name):
        """
            Get package list information
        """
        try:
            with DBHelper(db_name='lifecycle') as database:
                # Query all package data in the specified table
                _model = Packages.package_meta(table_name)
                _packageinfos = database.session.query(_model).all()
                packages_dicts = PackagesDownloadSchema(
                    many=True).dump(_packageinfos)
                return packages_dicts

        except (SQLAlchemyError, DisconnectionError) as error:
            current_app.logger.error(error)
            return None

    def __get_issues_content(self):
        """
            Get the list of issues
        """
        try:
            with DBHelper(db_name='lifecycle') as database:
                _issues = database.session.query(PackagesIssue).all()
                issues_dicts = IssueDownloadSchema(many=True).dump(_issues)
                return issues_dicts
        except (SQLAlchemyError, DisconnectionError) as error:
            current_app.logger.error(error)
            return None

    def __to_dataframe(self, datas):
        """
            Convert the obtained information into pandas content format
        """

        data_frame = pd.DataFrame(datas)
        return data_frame

    def get(self, file_type):
        """
            Download package collection information and isse list information

        """
        if file_type not in ['packages', 'issues']:
            return jsonify(
                ResponseCode.response_json(
                    ResponseCode.PARAM_ERROR))

        table_name = request.args.get('table_name', None)
        response = self._download_excel(file_type, table_name)
        return response


class MaintainerView(Resource):
    """
        Maintainer name collection
    """

    def __query_maintainers(self):
        """
            Query the names of all maintainers in the specified table
        """
        try:
            with DBHelper(db_name='lifecycle') as database:
                maintainers = database.session.query(
                    PackagesMaintainer.maintainer).group_by(PackagesMaintainer.maintainer).all()
                return [maintainer_item[0] for maintainer_item in maintainers
                        if maintainer_item[0]]
        except (SQLAlchemyError, DisconnectionError) as error:
            current_app.logger.error(error)
            return []

    def get(self):
        """
            Get the list of maintainers
        """
        # Group query of the names of all maintainers in the current table
        maintainers = self.__query_maintainers()
        return jsonify(ResponseCode.response_json(
            ResponseCode.SUCCESS,
            maintainers))


class TableColView(Resource):
    """
        The default column of the package shows the interface
    """

    def __columns_names(self):
        """
            Mapping of column name and title
        """
        columns = [
            ('name', 'Name', True),
            ('version', 'Version', True),
            ('release', 'Release', True),
            ('url', 'Url', True),
            ('rpm_license', 'License', False),
            ('feature', 'Feature', False),
            ('maintainer', 'Maintainer', True),
            ('maintainlevel', 'Maintenance Level', True),
            ('release_time', 'Release Time', False),
            ('used_time', 'Used Time', True),
            ('maintainer_status', 'Maintain Status', True),
            ('latest_version', 'Latest Version', False),
            ('latest_version_time', 'Latest Version Release Time', False),
            ('issue', 'Issue', True)]
        return columns

    def __columns_mapping(self):
        """

        """
        columns = list()
        for column in self.__columns_names():
            columns.append({
                'column_name': column[0],
                'label': column[1],
                'default_selected': column[2]
            })
        return columns

    def get(self):
        """
            Get the default display column of the package

        """
        table_mapping_columns = self.__columns_mapping()
        return jsonify(
            ResponseCode.response_json(
                ResponseCode.SUCCESS,
                table_mapping_columns))


class LifeTables(Resource):
    """
    description: LifeTables
    Restful API: get
    ChangeLog:
    """

    def get(self):
        """
        return all table names in the database

        Returns:
            Return the table names in the database as a list
        """
        try:
            with DBHelper(db_name="lifecycle") as database_name:
                # View all table names in the package-info database
                all_table_names = database_name.engine.table_names()
                all_table_names.remove("packages_issue")
                all_table_names.remove("packages_maintainer")
                all_table_names.remove("databases_info")
                return jsonify(
                    ResponseCode.response_json(
                        ResponseCode.SUCCESS, data=all_table_names)
                )
        except (SQLAlchemyError, DisconnectionError, Error, ValueError) as sql_error:
            LOGGER.logger.error(sql_error)
            return jsonify(
                ResponseCode.response_json(ResponseCode.DATABASE_NOT_FOUND)
            )


class IssueView(Resource):
    """
        Issue content collection
    """

    def _query_issues(self, request_data):
        """
        Args:
            request_data:
        Returns:
        """
        try:
            with DBHelper(db_name='lifecycle') as database:
                issues_query = database.session.query(PackagesIssue.issue_id,
                                                      PackagesIssue.issue_url,
                                                      PackagesIssue.issue_title,
                                                      PackagesIssue.issue_status,
                                                      PackagesIssue.pkg_name,
                                                      PackagesIssue.issue_type,
                                                      PackagesMaintainer.maintainer). \
                    outerjoin(PackagesMaintainer,
                              PackagesMaintainer.name == PackagesIssue.pkg_name)
                if request_data.get("pkg_name"):
                    issues_query = issues_query.filter(
                        PackagesIssue.pkg_name == request_data.get("pkg_name"))
                if request_data.get("issue_type"):
                    issues_query = issues_query.filter(
                        PackagesIssue.issue_type == request_data.get("issue_type"))
                if request_data.get("issue_status"):
                    issues_query = issues_query.filter(
                        PackagesIssue.issue_status == request_data.get("issue_status"))
                if request_data.get("maintainer"):
                    issues_query = issues_query.filter(
                        PackagesMaintainer.maintainer == request_data.get("maintainer"))
                total_count = issues_query.count()
                total_page = math.ceil(
                    total_count / int(request_data.get("page_size")))
                issues_query = issues_query.limit(request_data.get("page_size")).offset(
                    (int(request_data.get("page_num")) - 1) * int(request_data.get("page_size")))
                issue_dicts = IssuePageSchema(
                    many=True).dump(issues_query.all())
                issue_data = ResponseCode.response_json(
                    ResponseCode.SUCCESS, issue_dicts)
                issue_data['total_count'] = total_count
                issue_data['total_page'] = total_page
                return issue_data
        except (SQLAlchemyError, DisconnectionError) as error:
            current_app.logger.error(error)
            return ResponseCode.response_json(ResponseCode.DATABASE_NOT_FOUND)

    def get(self):
        """
        Description: Get all issues info or one specific issue
        Args:
        Returns:
            [
            {
            "issue_id": "",
            "issue_url": "",
            "issue_title": "",
            "issue_content": "",
            "issue_status": "",
            "issue_type": ""
            },
            ]
        Raises:
            DisconnectionError: Unable to connect to database exception
            AttributeError: Object does not have this property
            TypeError: Exception of type
            Error: Abnormal error
        """
        schema = IssueSchema()
        if schema.validate(request.args):
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        issue_dict = self._query_issues(request.args)
        return issue_dict


class IssueType(Resource):
    """
        Issue type collection
    """

    def _get_issue_type(self):
        """
        Description: Query issue type
        Returns:
        """
        try:
            with DBHelper(db_name='lifecycle') as database:
                issues_query = database.session.query(PackagesIssue.issue_type).group_by(
                    PackagesIssue.issue_type).all()
                return jsonify(ResponseCode.response_json(
                    ResponseCode.SUCCESS, [issue_query[0] for issue_query in issues_query]))
        except (SQLAlchemyError, DisconnectionError) as error:
            current_app.logger.error(error)
            return jsonify(ResponseCode.response_json(
                ResponseCode.PARAM_ERROR))

    def get(self):
        """
        Description: Get all issues info or one specific issue
        Args:
        Returns:
            [
            "issue_type",
            "issue_type"
            ]
        Raises:
            DisconnectionError: Unable to connect to database exception
            AttributeError: Object does not have this property
            TypeError: Exception of type
            Error: Abnormal error
        """
        return self._get_issue_type()


class IssueStatus(Resource):
    """
        Issue status collection
    """

    def _get_issue_status(self):
        """
        Description: Query issue status
        Returns:
        """
        try:
            with DBHelper(db_name='lifecycle') as database:
                issues_query = database.session.query(PackagesIssue.issue_status).group_by(
                    PackagesIssue.issue_status).all()
                return jsonify(ResponseCode.response_json(
                    ResponseCode.SUCCESS, [issue_query[0] for issue_query in issues_query]))
        except (SQLAlchemyError, DisconnectionError) as error:
            current_app.logger.error(error)
            return jsonify(ResponseCode.response_json(
                ResponseCode.PARAM_ERROR))

    def get(self):
        """
        Description: Get all issues info or one specific issue
        Args:
        Returns:
            [
            "issue_status",
            "issue_status"
            ]
        Raises:
            DisconnectionError: Unable to connect to database exception
            AttributeError: Object does not have this property
            TypeError: Exception of type
            Error: Abnormal error
        """
        return self._get_issue_status()


class IssueCatch(Resource):
    """
    description: Catch issue content
    Restful API: put
    ChangeLog:
    """

    def post(self):
        """
        Searching issue content
        Args:
        Returns:
            for examples:
                [
            {
            "issue_id": "",
            "issue_url": "",
            "issue_title": "",
            "issue_content": "",
            "issue_status": "",
            "issue_type": ""
            },
            ]
        Raises:
            DisconnectionError: Unable to connect to database exception
            AttributeError: Object does not have this property
            TypeError: Exception of type
            Error: Abnormal error
        """
        data = json.loads(request.get_data())
        if not isinstance(data, dict):
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR))
        pkg_name = data["repository"]["path"]
        try:
            _readconfig = ReadConfig(system_config.SYS_CONFIG_PATH)
            pool_workers = _readconfig.get_config('LIFECYCLE', 'pool_workers')
            _warehouse = _readconfig.get_config('LIFECYCLE', 'warehouse')
            if _warehouse is None:
                _warehouse = 'src-openeuler'
            if not isinstance(pool_workers, int):
                pool_workers = 10
            pool = ThreadPoolExecutor(max_workers=pool_workers)
            with DBHelper(db_name="lifecycle") as database:
                for table_name in filter(lambda x: x not in ['packages_issue', 'packages_maintainer',
                                                             'databases_info'],
                                         database.engine.table_names()):
                    cls_model = Packages.package_meta(table_name)
                    for package_item in database.session.query(cls_model).filter(
                            cls_model.name == pkg_name).all():
                        gitee_issue = gitee(
                            package_item, _warehouse, package_item.name, table_name)
                        pool.submit(gitee_issue.issue_hooks, data)
            pool.shutdown()
            return jsonify(ResponseCode.response_json(ResponseCode.SUCCESS))
        except SQLAlchemyError as error_msg:
            current_app.logger.error(error_msg)


class UpdatePackages(Resource):
    """
    description:Life cycle update information of a single package
    Restful API: post
    ChangeLog:
    """

    def _get_all_yaml_name(self, filepath):
        """
        List of all yaml file names in the folder

        Args:
            filepath: file path

        Returns:
            yaml_file_list：List of all yaml file names in the folder

        Attributes：
            Error：Error
            NotADirectoryError：Invalid directory name
            FileNotFoundError：File not found error

        """
        try:
            yaml_file_list = os.listdir(filepath)
            return yaml_file_list
        except (Error, NotADirectoryError, FileNotFoundError) as error:
            current_app.logger.error(error)
            return None

    def _get_yaml_content(self, yaml_file, filepath):
        """
        Read the content of the yaml file

        Args:
            yaml_file: yaml file
            filepath: file path

        Returns:
            Return a dictionary containing name, maintainer and maintainlevel
        """
        yaml_data_dict = dict()
        if not yaml_file.endswith(".yaml"):
            return None
        pkg_name = yaml_file.rsplit('.yaml')[0]
        single_yaml_path = os.path.join(filepath, yaml_file)
        with open(single_yaml_path, 'r', encoding='utf-8') as file_context:
            yaml_flie_data = yaml.load(
                file_context.read(), Loader=yaml.FullLoader)
            if yaml_flie_data is None or not isinstance(yaml_flie_data, dict):
                return None
            maintainer = yaml_flie_data.get("maintainer")
            maintainlevel = yaml_flie_data.get("maintainlevel")
        yaml_data_dict['name'] = pkg_name
        if maintainer:
            yaml_data_dict['maintainer'] = maintainer
        if maintainlevel:
            yaml_data_dict['maintainlevel'] = maintainlevel
        return yaml_data_dict

    def _read_yaml_file(self, filepath):
        """
        Read the yaml file and combine the data of the nested dictionary of the list

        Args:
            filepath: file path

        Returns:
            yaml.YAMLError：yaml file error
            SQLAlchemyError：SQLAlchemy Error
            DisconnectionError：Connect to database error
            Error：Error
        """
        yaml_file_list = self._get_all_yaml_name(filepath)
        if not yaml_file_list:
            return None
        try:
            yaml_data_list = list()
            _readconfig = ReadConfig(system_config.SYS_CONFIG_PATH)
            pool_workers = _readconfig.get_config('LIFECYCLE', 'pool_workers')
            if not isinstance(pool_workers, int):
                pool_workers = 10
            with ThreadPoolExecutor(max_workers=pool_workers) as pool:
                for yaml_file in yaml_file_list:
                    pool_result = pool.submit(
                        self._get_yaml_content, yaml_file, filepath)
                    yaml_data_dict = pool_result.result()
                    yaml_data_list.append(yaml_data_dict)
            return yaml_data_list
        except (yaml.YAMLError, SQLAlchemyError, DisconnectionError, Error) as error:
            current_app.logger.error(error)
            return None

    def _verification_yaml_data_list(self, yaml_data_list):
        """
        Verify the data obtained in the yaml file

        Args:
            yaml_data_list: yaml data list

        Returns:
            yaml_data_list: After verification yaml data list

        Attributes:
            ValidationError: Validation error

        """
        try:
            DataFormatVerfi(many=True).load(yaml_data_list)
            return yaml_data_list
        except ValidationError as error:
            current_app.logger.error(error.messages)
            return None

    def _save_in_database(self, yaml_data_list):
        """
        Save the data to the database

        Args:
            tbname: Table Name
            name_separate_list: Split name list
            _update_pack_data: Split new list of combined data

        Returns:
           SUCCESS or UPDATA_DATA_FAILED

        Attributes
            DisconnectionError: Connect to database error
            SQLAlchemyError: SQLAlchemy Error
            Error: Error

        """
        try:
            with DBHelper(db_name="lifecycle") as database_name:
                if 'packages_maintainer' not in database_name.engine.table_names():
                    return jsonify(ResponseCode.response_json(
                        ResponseCode.TABLE_NAME_NOT_EXIST))
                database_name.session.begin(subtransactions=True)
                for yaml_data in yaml_data_list:
                    name = yaml_data.get("name")
                    maintainer = yaml_data.get("maintainer")
                    maintainlevel = yaml_data.get("maintainlevel")
                    packages_maintainer_obj = database_name.session.query(
                        PackagesMaintainer).filter_by(name=name).first()
                    if packages_maintainer_obj:
                        if maintainer:
                            packages_maintainer_obj.maintainer = maintainer
                        if maintainlevel:
                            packages_maintainer_obj.maintainlevel = maintainlevel
                    else:
                        database_name.add(PackagesMaintainer(
                            name=name, maintainer=maintainer, maintainlevel=maintainlevel
                        ))
                    database_name.session.commit()
                return jsonify(ResponseCode.response_json(
                    ResponseCode.SUCCESS))
        except (DisconnectionError, SQLAlchemyError, Error, AttributeError) as error:
            current_app.logger.error(error)
            return jsonify(ResponseCode.response_json(
                ResponseCode.UPDATA_DATA_FAILED))

    def _overall_process(
            self,
            filepath):
        """
        Call each method to complete the entire function

        Args:
            filepath: file path
            tbname: table name

        Returns:
            SUCCESS or UPDATA_DATA_FAILED

        Attributes
            DisconnectionError: Connect to database error
            SQLAlchemyError: SQLAlchemy Error
            Error: Error
        """
        try:
            if filepath is None or not os.path.exists(filepath):
                return jsonify(ResponseCode.response_json(
                    ResponseCode.SPECIFIED_FILE_NOT_EXIST))
            yaml_file_list = self._get_all_yaml_name(filepath)
            if not yaml_file_list:
                return jsonify(ResponseCode.response_json(
                    ResponseCode.EMPTY_FOLDER))
            yaml_data_list_result = self._read_yaml_file(filepath)
            yaml_data_list = self._verification_yaml_data_list(
                yaml_data_list_result)
            if yaml_data_list is None:
                return jsonify(ResponseCode.response_json(
                    ResponseCode.YAML_FILE_ERROR))
            result = self._save_in_database(
                yaml_data_list)
            return result
        except (DisconnectionError, SQLAlchemyError, Error) as error:
            current_app.logger.error(error)
            return jsonify(ResponseCode.response_json(
                ResponseCode.UPDATA_DATA_FAILED))

    def _update_single_package_info(
            self, srcname, maintainer, maintainlevel):
        """
            Update the maintainer field and maintainlevel
            field of a single package

           Args:
               srcname: The name of the source package
               maintainer: Package maintainer
               maintainlevel: Package maintenance level

           Returns:
               success or failed

           Attributes
               SQLAlchemyError: sqlalchemy error
               DisconnectionError: Cannot connect to database error
               Error: Error
           """
        if not srcname:
            return jsonify(
                ResponseCode.response_json(ResponseCode.PACK_NAME_NOT_FOUND)
            )
        if not maintainer and not maintainlevel:
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        try:
            with DBHelper(db_name='lifecycle') as database_name:
                if 'packages_maintainer' not in database_name.engine.table_names():
                    return jsonify(ResponseCode.response_json(
                        ResponseCode.TABLE_NAME_NOT_EXIST))
                update_obj = database_name.session.query(
                    PackagesMaintainer).filter_by(name=srcname).first()
                if update_obj:
                    if maintainer:
                        update_obj.maintainer = maintainer
                    if maintainlevel:
                        update_obj.maintainlevel = maintainlevel
                else:
                    database_name.add(PackagesMaintainer(
                        name=srcname, maintainer=maintainer, maintainlevel=maintainlevel
                    ))
                database_name.session.commit()
                return jsonify(
                    ResponseCode.response_json(
                        ResponseCode.SUCCESS))
        except (SQLAlchemyError, DisconnectionError, Error) as sql_error:
            current_app.logger.error(sql_error)
            database_name.session.rollback()
            return jsonify(ResponseCode.response_json(
                ResponseCode.UPDATA_DATA_FAILED
            ))

    def put(self):
        """
        Life cycle update information of a single package or
        All packages

        Returns:
            for example::
            {
                "code": "",
                "data": "",
                "msg": ""
            }
        """
        schema = UpdatePackagesSchema()
        data = request.get_json()
        if schema.validate(data):
            return jsonify(
                ResponseCode.response_json(ResponseCode.PARAM_ERROR)
            )
        srcname = data.get('pkg_name', None)
        maintainer = data.get('maintainer', None)
        maintainlevel = data.get('maintainlevel', None)
        batch = data.get('batch')
        filepath = data.get('filepath', None)

        if batch:
            result = self._overall_process(filepath)
        else:
            result = self._update_single_package_info(
                srcname, maintainer, maintainlevel)
        return result
