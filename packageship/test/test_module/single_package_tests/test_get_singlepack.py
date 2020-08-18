#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
test_get_single_packages
"""
from test.base_code.common_test_code import get_correct_json_by_filename
from test.base_code.common_test_code import compare_two_values
from test.base_code.read_data_base import ReadTestBase
import unittest
import json

from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.function.searchdb import db_priority
class TestGetSinglePack(ReadTestBase):
    """
    Single package test case
    """
    db_name = db_priority()[-1]
    def test_error_sourcename(self):
        """sourceName  is none or err"""

        resp = self.client.get(f"packages/packageInfo?dbName={self.db_name}")
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

        resp = self.client.get(
            f"packages/packageInfo?sourceName=&dbName={self.db_name}")
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

        resp = self.client.get(
            "packages/packageInfo?sourceName=test&dbName=for")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.DB_NAME_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.DB_NAME_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_true_dbname(self):
        """dbName is null or err"""

        resp = self.client.get("packages/packageInfo?sourceName=A")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNotNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        correct_list = get_correct_json_by_filename("get_single_package")
        self.assertNotEqual([], correct_list, msg="Error reading JSON file")
        input_value = correct_list[0]["url"]
        resp = self.client.get(
            f"{input_value}")
        resp_dict = json.loads(resp.data)
        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertTrue(
            compare_two_values(
                resp_dict.get("data"),
                correct_list[0]['data']),
            msg="Error in data information return")

    def test_wrong_dbname(self):
        """test_wrong_dbname"""
        resp = self.client.get(
            "/packages/packageInfo?sourceName=A&dbName=open")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.DB_NAME_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.DB_NAME_ERROR),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")


if __name__ == '__main__':
    unittest.main()
