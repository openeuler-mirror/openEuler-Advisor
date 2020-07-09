#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
TestInstallDepend
"""
import unittest
import json

from test.base_code.common_test_code import get_correct_json_by_filename, compare_two_values
from test.base_code.read_data_base import ReadTestBase
from packageship.application.apps.package.function.constants import ResponseCode


class TestInstallDepend(ReadTestBase):
    """
    TestInstallDepend
    """

    def test_empty_binaryName_dbList(self):
        """
        test_empty_binaryName_dbList
        Returns:

        """
        resp = self.client.post("/packages/findInstallDepend",
                                data="{}",
                                content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.PARAM_ERROR),
                         resp_dict.get("msg"),
                         msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(resp_dict.get("data"), msg="Error in data information return")

        resp = self.client.post("/packages/findInstallDepend",
                                data=json.dumps({"binaryName": "A1"}),
                                content_type="application/json")

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
        self.assertIsNotNone(resp_dict.get("data"), msg="Error in data information return")

    def test_wrong_binaryName_dbList(self):
        """
        test_empty_binaryName_dbList
        Returns:

        """
        resp = self.client.post("/packages/findInstallDepend",
                                data=json.dumps({"binaryName": 0}),
                                content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.PARAM_ERROR),
                         resp_dict.get("msg"),
                         msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(resp_dict.get("data"), msg="Error in data information return")

        resp = self.client.post("/packages/findInstallDepend",
                                data=json.dumps(
                                    {"binaryName": "qitiandasheng"}),
                                content_type="application/json")

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
        self.assertIsNotNone(resp_dict.get("data"), msg="Error in data information return")

        resp = self.client.post("/packages/findInstallDepend",
                                data=json.dumps({"binaryName": "A1",
                                                 "db_list": [12, 3, 4]}),
                                content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.PARAM_ERROR),
                         resp_dict.get("msg"),
                         msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(resp_dict.get("data"), msg="Error in data information return")

        resp = self.client.post("/packages/findInstallDepend",
                                data=json.dumps({"binaryName": "A1",
                                                 "db_list": ["shifu", "bajie"]
                                                 }), content_type="application/json")
        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.DB_NAME_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.DB_NAME_ERROR),
                         resp_dict.get("msg"),
                         msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(resp_dict.get("data"), msg="Error in data information return")

    def test_true_params_result(self):
        """
        test_empty_binaryName_dbList
        Returns:

        """
        correct_list = get_correct_json_by_filename("install_depend")

        self.assertNotEqual([], correct_list, msg="Error reading JSON file")

        for correct_data in correct_list:
            input_value = correct_data["input"]
            resp = self.client.post("/packages/findInstallDepend",
                                    data=json.dumps(input_value),
                                    content_type="application/json")
            output_for_input = correct_data["output"]
            resp_dict = json.loads(resp.data)
            self.assertTrue(compare_two_values(output_for_input, resp_dict),
                            msg="The answer is not correct")


if __name__ == '__main__':
    unittest.main()
