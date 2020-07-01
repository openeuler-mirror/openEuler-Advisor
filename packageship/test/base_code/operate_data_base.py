# -*- coding:utf-8 -*-
import os
import unittest

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
                                                      'operate_dbs')

    from test.base_code.init_config_path import init_config
    from packageship.manage import app
except Exception as e:
    raise


class OperateTestBase(unittest.TestCase):
    """

    """

    def setUp(self) -> None:
        self.client = app.test_client()
