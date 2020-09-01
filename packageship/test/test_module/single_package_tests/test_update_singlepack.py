#!/usr/bin/python3
"""TestUpdatePackage"""
# -*- coding:utf-8 -*-
import os
from test.base_code.operate_data_base import OperateTestBase
from packageship import system_config

import json

from packageship.application.apps.package.function.constants import ResponseCode


class TestBatchUpdatePackage(OperateTestBase):
    """TestUpdatePackage"""

    def test_missing_required_parameters(self):
        """
        Parameter error
        """
        # all miss required parameters
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"batch": ""}),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # all miss wrong parameters
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"batch": "1"}),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SPECIFIED_FILE_NOT_EXIST,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.SPECIFIED_FILE_NOT_EXIST),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_read_yaml_update(self):
        """

        Returns:

        """

        # Missing file path
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"batch": 1}),
                               content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SPECIFIED_FILE_NOT_EXIST,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.SPECIFIED_FILE_NOT_EXIST),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # File path error
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"batch": 1,
                                                "filepath": "D\\"}),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SPECIFIED_FILE_NOT_EXIST,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.SPECIFIED_FILE_NOT_EXIST),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Data error in yaml file
        yaml_path = os.path.join(
            os.path.dirname(system_config.BASE_PATH),
            "test",
            "common_files",
            "test_wrong_format_yaml")
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"filepath": yaml_path,
                                                "batch": 1
                                                }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.YAML_FILE_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.YAML_FILE_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Data error in yaml file
        yaml_path = os.path.join(
            os.path.dirname(system_config.BASE_PATH),
            "test",
            "common_files",
            "test_wrong_main_yaml")
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"filepath": yaml_path,
                                                "batch": 1
                                                }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.YAML_FILE_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.YAML_FILE_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_batch_error(self):
        """
        test_batch_error
        Returns:

        """

        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"filepath": "C:\\",
                                                "batch": 2
                                                }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_true_yaml(self):
        """

        Returns:

        """
        yaml_path = os.path.join(
            os.path.dirname(system_config.BASE_PATH),
            "test",
            "common_files",
            "test_true_yaml")
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({"filepath": yaml_path,
                                                "batch": 1
                                                }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.SUCCESS),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_single_update(self):
        """

        Returns:

        """

        # Various parameters are missing
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({
                                   "pkg_name": "",
                                   "batch": 0
                               }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PACK_NAME_NOT_FOUND,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PACK_NAME_NOT_FOUND),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({
                                   "pkg_name": "CUnit",
                                   "batch": 0,
                                   "maintainlevel": "a"
                               }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({
                                   "pkg_name": "CUnit",
                                   "batch": 0,
                                   "maintainlevel": "6"
                               }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_ture_name(self):
        """
        test table name
        Returns:

        """
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({
                                   "pkg_name": "CUnit",
                                   "batch": 0,
                                   "maintainlevel": "4"
                               }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.SUCCESS),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_pkg_name(self):
        """
        test_pkg_name
        Returns:

        """
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({
                                   "pkg_name": "",
                                   "batch": 0,
                                   "maintainlevel": "4"
                               }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PACK_NAME_NOT_FOUND,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PACK_NAME_NOT_FOUND),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_true_updata_single(self):
        """
        test_true_single
        Returns:

        """
        resp = self.client.put("/lifeCycle/updatePkgInfo",
                               data=json.dumps({
                                   "pkg_name": "CUnit",
                                   "batch": 0,
                                   "maintainlevel": "4"
                               }),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.SUCCESS),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")
