#!/usr/bin/python3
"""TestUpdatePackage"""
# -*- coding:utf-8 -*-
from test.base_code.operate_data_base import OperateTestBase
import unittest
import json

from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.function.searchdb import db_priority

class TestUpdatePackage(OperateTestBase):
    """TestUpdatePackage"""
    db_name = db_priority()[0]
    def test_empty_dbname(self):
        """Parameter error"""

        resp = self.client.put("/packages/packageInfo",
                               data=json.dumps({"dbName": "",
                                                "sourceName": "xx",
                                                "maintainer": "",
                                                "maintainlevel": "1"}),
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

        # wrong dbname
        resp = self.client.put("/packages/packageInfo",
                               data=json.dumps({"dbName": "xhhz",
                                                "sourceName": "xx",
                                                "maintainer": "",
                                                "maintainlevel": "1"}),
                               content_type="application/json")
        resp_dict = json.loads(resp.data)
        resp_dict.get("data")

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

    def test_empty_sourcename(self):
        """Parameter error"""

        resp = self.client.put("/packages/packageInfo",
                               data=json.dumps({"dbName": f"{self.db_name}",
                                                "sourceName": "xx",
                                                "maintainer": "1"}),
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
        #  miss maintainer maintainlevel
        resp = self.client.put("/packages/packageInfo",
                               data=json.dumps({"dbName": f"{self.db_name}",
                                                "sourceName": "xx"}),
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

    def test_true_parram(self):
        """
        Returns:
        """
        resp = self.client.put("/packages/packageInfo",
                               data=json.dumps({"dbName": f"{self.db_name}",
                                                "sourceName": "A",
                                                "maintainer": "x",
                                                "maintainlevel": "1"}),
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


if __name__ == '__main__':
    unittest.main()
