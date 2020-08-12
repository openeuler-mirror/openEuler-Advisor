#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
TestSelfDepend
"""
import unittest
import json

from test.base_code.common_test_code import get_correct_json_by_filename, compare_two_values
from test.base_code.read_data_base import ReadTestBase
from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.function.searchdb import db_priority


class TestSelfDepend(ReadTestBase):
    """
    TestSelfDepend
    """

    def test_empty_parameter(self):
        """
        test_empty_parameter
        Returns:

        """
        resp = self.client.post("/packages/findSelfDepend",
                                data='{}',
                                content_type="application/json")

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

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status information return!")

        self.assertIn("data", resp_dict, msg="Wrong return format!")
        self.assertIsNotNone(resp_dict.get("data"), msg="Data return error!")

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": db_priority()
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status information return!")

        self.assertIn("data", resp_dict, msg="Wrong return format!")
        self.assertIsNotNone(resp_dict.get("data"), msg="Data return error!")

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": db_priority(),
                                    "selfbuild": "0"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status information return!")

        self.assertIn("data", resp_dict, msg="Wrong return format!")
        self.assertIsNotNone(resp_dict.get("data"), msg="Data return error!")

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": db_priority(),
                                    "selfbuild": "0",
                                    "withsubpack": "0"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status information return!")

        self.assertIn("data", resp_dict, msg="Wrong return format!")
        self.assertIsNotNone(resp_dict.get("data"), msg="Data return error!")

    def test_wrong_parameter(self):
        """
        test_wrong_parameter
        Returns:

        """
        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "wukong"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.PACK_NAME_NOT_FOUND,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.PACK_NAME_NOT_FOUND),
                         resp_dict.get("msg"),
                         msg="Error in status information return!")

        self.assertIn("data", resp_dict, msg="Wrong return format!")
        self.assertIsNone(resp_dict.get("data"), msg="Data return error!")

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": [1, 2, 3, 4]
                                }),
                                content_type="application/json")

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

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": ["bajie", "shifu"]
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.DB_NAME_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Wrong return format!")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.DB_NAME_ERROR),
                         resp_dict.get("msg"),
                         msg="Error in status information return!")

        self.assertIn("data", resp_dict, msg="Wrong return format!")
        self.assertIsNone(resp_dict.get("data"), msg="Data return error!")

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": db_priority(),
                                    "selfbuild": "nverguo"
                                }),
                                content_type="application/json")

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

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": db_priority(),
                                    "selfbuild": "0",
                                    "withsubpack": "pansidong",
                                }),
                                content_type="application/json")

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

        resp = self.client.post("/packages/findSelfDepend",
                                data=json.dumps({
                                    "packagename": "A1",
                                    "db_list": db_priority(),
                                    "selfbuild": "0",
                                    "withsubpack": "0",
                                    "packtype": "pansidaxian"
                                }),
                                content_type="application/json")

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

    def test_true_params_result(self):
        """
        test_true_params_result
        Returns:

        """
        correct_list = get_correct_json_by_filename("self_depend")

        self.assertNotEqual([], correct_list, msg="Error reading JSON file")

        for correct_data in correct_list:
            input_value = correct_data["input"]
            resp = self.client.post("/packages/findSelfDepend",
                                    data=json.dumps(input_value),
                                    content_type="application/json")
            output_for_input = correct_data["output"]
            from pprint import pprint

            resp_dict = json.loads(resp.data)

            self.assertTrue(compare_two_values(output_for_input, resp_dict),
                            msg="The answer is not correct")


if __name__ == '__main__':
    unittest.main()
