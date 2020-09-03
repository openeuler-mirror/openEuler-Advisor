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

    def test_missing_required_parameters(self):
        """
        Missing required parameters
        """
        # Missing required parameters pkg_name
        resp = self.client.get(
            f"packages/packageInfo?pkg_name=&table_name=mainline")
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

        # Missing required parameters table_name
        resp = self.client.get(f"packages/packageInfo?pkg_name=A&table_name=")
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

    def test_wrong_parameters(self):
        """
        test wrong parramters
        """

        # Missing required parameters table_name
        resp = self.client.get(
            f"packages/packageInfo?pkg_name=A&table_name=test")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.TABLE_NAME_NOT_EXIST,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.TABLE_NAME_NOT_EXIST),
            resp_dict.get("msg"),
            msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Missing required parameters pkg_name
        resp = self.client.get(
            f"packages/packageInfo?pkg_name=test&table_name=fedora30")
        resp_dict = json.loads(resp.data)

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

    def test_true_parameters(self):
        """
        test true parameters
        """
        resp = self.client.get(
            "/packages/packageInfo?pkg_name=A&table_name=fedora30")
        resp_dict = json.loads(resp.data)

        correct_list = get_correct_json_by_filename(
            "get_single_package")

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
                correct_list),
            msg="Error in data information return")
