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
from packageship.application.apps.package.serialize import DataFormatVerfi, UpdatePackagesSchema
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.exception import Error
from packageship.application.apps.package.function.constants import ResponseCode
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper
from packageship.application.models.package import PackagesIssue
from packageship.application.models.package import Packages
from packageship.application.models.package import PackagesMaintainer
from packageship.libs.log import Log
from .serialize import IssueDownloadSchema, PackagesDownloadSchema
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
                return [maintainer_item[0]
                        for maintainer_item in maintainers if maintainer_item[0]]
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
            ('linense', 'License', False),
            ('feature', 'Feature', False),
            ('maintainer', 'Maintainer', True),
            ('maintainlevel', 'Maintenance Level', True),
            ('release_time', 'Release Time', False),
            ('end_of_lifecycle', 'End of Life Cycle', True),
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
