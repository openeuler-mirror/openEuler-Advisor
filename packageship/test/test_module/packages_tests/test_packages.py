# -*- coding:utf-8 -*-
"""
packges test
"""
from test.base_code.read_data_base import ReadTestBase
import unittest
import json

from packageship.application.apps.package.function.constants import ResponseCode


class TestPackages(ReadTestBase):
    """
    All package test cases
    """

    def test_empty_dbName(self):
        """dbName is none"""

        resp = self.client.get("/packages")
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

        resp = self.client.get("/packages?dbName=")
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

    def test_wrong_dbName(self):
        """dbName is err"""

        resp = self.client.get("/packages?dbName=test")
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
            msg="Error in data format return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")


def test_packages_suit():
    print("---TestPackages START---")
    suite = unittest.TestSuite()
    suite.addTest(TestPackages("test_empty_dbName"))
    suite.addTest(TestPackages("test_wrong_dbName"))
    unittest.TextTestRunner().run(suite)


if __name__ == '__main__':
    unittest.main()
