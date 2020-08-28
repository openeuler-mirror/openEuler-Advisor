#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
TestGetIssue

"""
from test.base_code.common_test_code import get_correct_json_by_filename
from test.base_code.operate_data_base import OperateTestBase
import unittest
import json

from packageship.application.apps.package.function.constants import ResponseCode


class TestIssueCatch(OperateTestBase):
    """
    Test Get Issue info
    """

    def test_wrong_params(self):
        """
        test issue catch
        """
        # No arguments passed
        resp = self.client.post("/lifeCycle/issuecatch",
                                json='')
        resp_dict = json.loads(resp.data)


        self.assertIn("code", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.PARAM_ERROR),
                         resp_dict.get("msg"),
                         msg="Error in status information return!")

        self.assertIn("data", resp_dict, msg="Wrong return format!")
        self.assertIsNone(resp_dict.get("data"), msg="Data return error!")

    def test_correct_params(self):
        # Correct params
        correct_list = get_correct_json_by_filename("issues")

        self.assertNotEqual([], correct_list, msg="Error reading JSON file")

        input_value = correct_list[2]["input"]
        resp = self.client.post("/lifeCycle/issuecatch",
                                json=input_value)
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
