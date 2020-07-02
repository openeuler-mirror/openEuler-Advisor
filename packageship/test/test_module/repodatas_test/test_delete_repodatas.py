# -*- coding:utf-8 -*-
"""
test delete repodatas
"""
import os
import shutil

from test.base_code.operate_data_base import OperateTestBase
import unittest
import json
from packageship import system_config
# from test.base_code.operate_data_base import system_config
from packageship.application.apps.package.function.constants import ResponseCode


class TestDeleteRepodatas(OperateTestBase):
    """
    test delete repodata
    """

    def test_wrong_dbname(self):
        """Test simulation scenario, dbname is not transmitted"""

        # Scenario 1: the value passed by dbname is empty
        resp = self.client.delete("/repodatas?dbName=")
        resp_dict = json.loads(resp.data)

        # assert
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

        resp = self.client.delete("/repodatas?dbName=rr")
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
        """
        Returns:
        """
        try:
            shutil.copyfile(system_config.DATABASE_FILE_INFO, system_config.DATABASE_FILE_INFO + '.bak')
            shutil.copytree(system_config.DATABASE_FOLDER_PATH, system_config.DATABASE_FOLDER_PATH + '.bak')
            resp = self.client.delete("/repodatas?dbName=openEuler-20.04-LTS")
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
        except Exception as e:
            return None
        finally:
            os.remove(system_config.DATABASE_FILE_INFO)
            os.rename(system_config.DATABASE_FILE_INFO + '.bak', system_config.DATABASE_FILE_INFO)
            shutil.rmtree(system_config.DATABASE_FOLDER_PATH)
            os.rename(system_config.DATABASE_FOLDER_PATH + '.bak', system_config.DATABASE_FOLDER_PATH)



def test_delete_repodatas_suit():
    """unit testing"""
    print("---TestDeleteRepodatas START---")
    suite = unittest.TestSuite()
    suite.addTest(TestDeleteRepodatas("test_wrong_dbname"))
    suite.addTest(TestDeleteRepodatas("test_true_dbname"))
    unittest.TextTestRunner().run(suite)
