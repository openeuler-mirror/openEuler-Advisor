#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
test_get_single_packages
"""
import os
import unittest
import pandas as pd
from test.base_code.read_data_base import ReadTestBase
from packageship import system_config
from packageship.application.apps.package.function.constants import ResponseCode


class TestDownloadExcelFile(ReadTestBase):
    """
    Download test of excel file
    """

    def test_file_type_error(self):
        """
            The file type to be downloaded for the test is incorrect
        """

        response = self.client_request("/lifeCycle/download/xxx")
        self.response_json_format(response)
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         response.get("code"),
                         msg="Error in status code return")

        self.assertIsNone(
            response.get("data"),
            msg="Error in data information return")

    def _save_download_file(self, response_data, path):
        """
            Save the downloaded file
        """
        with open(path, 'wb') as f:
            f.write(response_data)

    def test_issue_file(self):
        """
            Issue file download test
        """
        response = self.client.get("/lifeCycle/download/issues")
        data_frame = pd.read_excel(
            response.data, sheet_name='Summary',engine='xlrd')
        datas = data_frame.values.tolist()
        self.assertEqual(
            14, len(datas), msg="An error occurred in the downloaded data")
        data_dict = dict(zip(data_frame.columns.tolist(), datas[0]))
        data = {
            'issue_id': 'I1OQW8',
            'issue_url': 'https://gitee.com/openeuler/openEuler-Advisor/issues/I1PGWQ',
            'issue_content': 'def get_yaml(self, pkg):',
            'issue_title': '【CI加固】对识别修改对周边组件和升级影响',
            'issue_status': 'open',
            'pkg_name': 'dnf',
            'issue_type': 'defect',
            'related_release': 'hahaxx'
        }
        self.assertEqual(data, data_dict,
                         msg='An error occurred in the downloaded data')

    def test_package_file(self):
        """
            download packages file
        """
        response = self.client.get(
            "/lifeCycle/download/packages?table_name=mainline")

        data_frame = pd.read_excel(
            response.data, sheet_name='Summary')
        datas = data_frame.values.tolist()
        self.assertEqual(
            5, len(datas), msg="An error occurred in the downloaded data")
        data_dict = dict(zip(data_frame.columns.tolist(), datas[0]))
        data = {
            'name': 'CUnit',
            'url': 'http://cunit.sourceforge.net/',
            'rpm_license': 'LGPLv2+',
            'version': '2.1.3',
            'release': '21.oe1',
            'release_time': 1.0,
            'used_time': 2.0,
            'latest_version': 3.0,
            'latest_version_time': 4.0,
            'feature': 5,
            'cve': 0,
            'defect': 0,
            'maintainer': 'userA',
            'maintainlevel': 6.0,
        }
        self.assertEqual(data, data_dict,
                         msg='An error occurred in the downloaded data')

    def test_package_file_no_table_name(self):
        """
            download packages file
        """
        response = self.client_request(
            "/lifeCycle/download/packages")
        self.response_json_format(response)
        self.assertEqual(ResponseCode.SERVICE_ERROR, response.get(
            'code'), msg='Error in status code return')


if __name__ == '__main__':
    unittest.main()
