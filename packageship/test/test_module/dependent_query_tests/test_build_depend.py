#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
 build_depend unittest
"""
import json
import unittest

from test.base_code.read_data_base import ReadTestBase
from test.base_code.common_test_code import compare_two_values, get_correct_json_by_filename
from packageship.application.apps.package.function.constants import ResponseCode


class TestBuildDepend(ReadTestBase):
    """
    class for test build_depend
    """

    def test_empty_source_name_dblist(self):
        """
        test empty parameters:sourceName,dbList
        :return:
        """
        resp = self.client.post("/packages/findBuildDepend",
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

        resp = self.client.post("/packages/findBuildDepend",
                                data=json.dumps({"sourceName": "A"}),
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

    def test_wrong_source_name_dblist(self):
        """
        test wrong parameters:sourceName,dbList
        :return: None
        """
        resp = self.client.post("/packages/findBuildDepend",
                                data=json.dumps({"sourceName": 0}),
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

        resp = self.client.post("/packages/findBuildDepend",
                                data=json.dumps({"sourceName": "qitiandasheng"}),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)
        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PACK_NAME_NOT_FOUND,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.PACK_NAME_NOT_FOUND),
                         resp_dict.get("msg"),
                         msg="Error in status prompt return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(resp_dict.get("data"), msg="Error in data information return")

        resp = self.client.post("/packages/findBuildDepend",
                                data=json.dumps({"sourceName": "CUnit",
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

        resp = self.client.post("/packages/findBuildDepend",
                                data=json.dumps({"sourceName": "CUnit",
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
        test_true_params_result
        Returns:

        """
        correct_list = get_correct_json_by_filename("build_depend")

        self.assertNotEqual([], correct_list, msg="Error reading JSON file")

        for correct_data in correct_list:
            input_value = correct_data["input"]
            resp = self.client.post("/packages/findBuildDepend",
                                    data=json.dumps(input_value),
                                    content_type="application/json")
            output_for_input = correct_data["output"]
            resp_dict = json.loads(resp.data)
            self.assertTrue(compare_two_values(output_for_input, resp_dict),
                            msg="The answer is not correct")


if __name__ == '__main__':
    unittest.main()
