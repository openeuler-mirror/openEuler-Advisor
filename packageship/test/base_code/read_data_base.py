#!/usr/bin/python3
# -*- coding:utf-8 -*-
import os
import unittest
import json
from .basetest import TestBase

from packageship.libs.exception import Error
try:
    from packageship import system_config

    system_config.SYS_CONFIG_PATH = os.path.join(os.path.dirname(system_config.BASE_PATH),
                                                 'test',
                                                 'common_files',
                                                 'package.ini')

    system_config.DATABASE_FILE_INFO = os.path.join(os.path.dirname(system_config.BASE_PATH),
                                                    'test',
                                                    'common_files',
                                                    'database_file_info.yaml')
    system_config.DATABASE_FOLDER_PATH = os.path.join(os.path.dirname(system_config.BASE_PATH),
                                                      'test',
                                                      'common_files',
                                                      'dbs')

    from test.base_code.init_config_path import init_config
    from packageship.selfpkg import app

except Error:
    raise


class ReadTestBase(TestBase):

    def client_request(self, url):
        """
            Simulate client sending request
        """
        response = self.client.get(url)
        response_content = json.loads(response.data)
        return response_content

    def setUp(self):
        self.client = app.test_client()
