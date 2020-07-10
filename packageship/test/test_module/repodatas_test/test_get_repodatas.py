#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
test get repodatas
"""
from test.base_code.common_test_code import get_correct_json_by_filename
from test.base_code.common_test_code import compare_two_values
from test.base_code.read_data_base import ReadTestBase
import unittest
import json

from packageship.application.apps.package.function.constants import ResponseCode


class TestGetRepodatas(ReadTestBase):
    """
    test get repodatas
    """

    def test_dbname(self):
        """no dbName"""
        correct_list = get_correct_json_by_filename("get_repodatas")
        self.assertNotEqual([], correct_list, msg="Error reading JSON file")
        resp = self.client.get("/repodatas")
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
                correct_list),
            msg="Error in data information return")

        resp = self.client.get("/repodatas?ddd")
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
                correct_list),
            msg="Error in data information return")


if __name__ == '__main__':
    unittest.main()
