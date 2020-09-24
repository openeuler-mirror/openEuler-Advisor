#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
test delete repodatas
"""
import os
import shutil

from sqlalchemy.exc import SQLAlchemyError

from test.base_code.operate_data_base import OperateTestBase
import json
from packageship import system_config
from packageship.libs.exception import Error
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
            shutil.copytree(
                system_config.DATABASE_FOLDER_PATH,
                system_config.DATABASE_FOLDER_PATH + '.bak')
            resp = self.client.delete("/repodatas?dbName=fedora30")
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
        except (SQLAlchemyError, FileExistsError, Error):
            return None
        finally:
            shutil.rmtree(system_config.DATABASE_FOLDER_PATH)
            os.rename(
                system_config.DATABASE_FOLDER_PATH + '.bak',
                system_config.DATABASE_FOLDER_PATH)
