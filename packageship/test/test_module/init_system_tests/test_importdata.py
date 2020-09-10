#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
test import_databases
"""
import os
import shutil
import unittest
import warnings
from configparser import ConfigParser
import yaml
from packageship import system_config
from packageship.libs.exception import Error,ConfigurationException

try:

    system_config.SYS_CONFIG_PATH = os.path.join(
        os.path.dirname(
            system_config.BASE_PATH),
        'test',
        'common_files',
        'package.ini')

    system_config.DATABASE_FILE_INFO = os.path.join(
        os.path.dirname(
            system_config.BASE_PATH),
        'test',
        'init_system_files',
        'database_file_info.yaml')

    system_config.DATABASE_FOLDER_PATH = os.path.join(os.path.dirname(
        system_config.BASE_PATH), 'test', 'init_system_files', 'dbs')

    from test.base_code.init_config_path import init_config

except Error:
    raise Error

from packageship.application.initsystem.data_import import InitDataBase
from packageship.libs.exception import ContentNoneException
from packageship.libs.exception import DatabaseRepeatException
from packageship.libs.configutils.readconfig import ReadConfig


class ImportData(unittest.TestCase):
    """
    test importdatabases
    """

    def setUp(self):

        warnings.filterwarnings("ignore")

    def test_empty_param(self):
        """If init is not obtained_ conf_ Path parameter"""
        try:
            InitDataBase(config_file_path=None).init_data()
        except ContentNoneException as error:
            self.assertEqual(
                error.__class__,
                ContentNoneException,
                msg="No init in package_ conf_ Path parameter, wrong exception type thrown")

        # Yaml file exists but the content is empty

        try:
            _config_path = ReadConfig(system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            shutil.copyfile(_config_path, _config_path + '.bak')

            with open(_config_path, 'w', encoding='utf-8') as w_f:
                w_f.write("")

            InitDataBase(config_file_path=_config_path).init_data()
        except ConfigurationException as error:
            self.assertEqual(
                error.__class__,
                ConfigurationException,
                msg="Yaml file exists, but the content is empty. The exception type is wrong")
        finally:
            # Restore files
            os.remove(_config_path)
            os.rename(_config_path + '.bak', _config_path)

        # Yaml file exists but DB exists_ The same with name
        try:
            _config_path = ReadConfig(system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            shutil.copyfile(_config_path, _config_path + '.bak')
            with open(_config_path, 'r', encoding='utf-8') as file:
                origin_yaml = yaml.load(file.read(), Loader=yaml.FullLoader)
                for obj in origin_yaml:
                    obj["dbname"] = "openEuler"
                with open(_config_path, 'w', encoding='utf-8') as w_f:
                    yaml.dump(origin_yaml, w_f)

            InitDataBase(config_file_path=_config_path).init_data()
        except DatabaseRepeatException as error:

            self.assertEqual(
                error.__class__,
                DatabaseRepeatException,
                msg="Yaml file exists but DB_ Name duplicate exception type is wrong")
        finally:
            # Restore files
            os.remove(_config_path)
            os.rename(_config_path + '.bak', _config_path)

    def test_wrong_param(self):
        """If the corresponding current init_ conf_ The directory
        specified by path is incorrect"""
        try:
            # Back up source files
            shutil.copyfile(
                system_config.SYS_CONFIG_PATH,
                system_config.SYS_CONFIG_PATH + ".bak")
            # Modify dbtype to "test"_ dbtype"
            config = ConfigParser()
            config.read(system_config.SYS_CONFIG_PATH)
            config.set("SYSTEM", "init_conf_path", "D:\\Users\\conf.yaml")
            config.write(open(system_config.SYS_CONFIG_PATH, "w"))

            _config_path = ReadConfig(system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            InitDataBase(config_file_path=_config_path).init_data()
        except FileNotFoundError as error:
            self.assertEqual(
                error.__class__,
                FileNotFoundError,
                msg="init_ conf_ Path specified directory is empty exception type is wrong")
        finally:
            # To restore a file, delete the file first and then rename it back
            os.remove(system_config.SYS_CONFIG_PATH)
            os.rename(
                system_config.SYS_CONFIG_PATH + ".bak",
                system_config.SYS_CONFIG_PATH)

    def test_dbname(self):
        """test dbname"""
        try:
            _config_path = ReadConfig(system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            shutil.copyfile(_config_path, _config_path + '.bak')
            with open(_config_path, 'r', encoding='utf-8') as file:
                origin_yaml = yaml.load(file.read(), Loader=yaml.FullLoader)
                for obj in origin_yaml:
                    obj["dbname"] = ""
                with open(_config_path, 'w', encoding='utf-8') as w_f:
                    yaml.dump(origin_yaml, w_f)

            InitDataBase(config_file_path=_config_path).init_data()
        except DatabaseRepeatException as error:

            self.assertEqual(
                error.__class__,
                DatabaseRepeatException,
                msg="Yaml file exists but DB_ Name duplicate exception type is wrong")
        finally:
            # Restore files
            os.remove(_config_path)
            os.rename(_config_path + '.bak', _config_path)

    def test_src_db_file(self):
        """test src db file"""
        try:
            _config_path = ReadConfig(system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            shutil.copyfile(_config_path, _config_path + '.bak')
            with open(_config_path, 'r', encoding='utf-8') as file:
                origin_yaml = yaml.load(file.read(), Loader=yaml.FullLoader)
                for obj in origin_yaml:
                    obj["src_db_file"] = ""
                with open(_config_path, 'w', encoding='utf-8') as w_f:
                    yaml.dump(origin_yaml, w_f)

            InitDataBase(config_file_path=_config_path).init_data()
        except TypeError as error:

            self.assertEqual(
                error.__class__,
                TypeError,
                msg="Yaml file exists but DB_ Name duplicate exception type is wrong")
        finally:
            # Restore files
            os.remove(_config_path)
            os.rename(_config_path + '.bak', _config_path)

    def test_priority(self):
        """test priority"""
        try:
            _config_path = ReadConfig(system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            shutil.copyfile(_config_path, _config_path + '.bak')
            with open(_config_path, 'r', encoding='utf-8') as file:
                origin_yaml = yaml.load(file.read(), Loader=yaml.FullLoader)
                for obj in origin_yaml:
                    obj["priority"] = "-1"
                with open(_config_path, 'w', encoding='utf-8') as w_f:
                    yaml.dump(origin_yaml, w_f)
            InitDataBase(config_file_path=_config_path).init_data()
            with open(system_config.DATABASE_FILE_INFO, 'r', encoding='utf-8') as file_context:
                init_database_date = yaml.load(
                    file_context.read(), Loader=yaml.FullLoader)
            self.assertEqual(
                init_database_date,
                None,
                msg=" Priority must be a positive integer between 0 and 100 ")
        except FileNotFoundError:
            return
        finally:
            # Restore files
            os.remove(_config_path)
            os.rename(_config_path + '.bak', _config_path)

    def test_true_init_data(self):
        """
            Initialization of system data
        """
        # Normal configuration
        _config_path = ReadConfig(system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
        InitDataBase(config_file_path=_config_path).init_data()

        # In the correct case, an import will be generated under the initsystem
        # directory_ success_ databse.yaml
        path = system_config.DATABASE_FILE_INFO

        self.assertTrue(
            os.path.exists(path),
            msg="Import was not generated successfully "
                "after initialization_ success_ databse.yaml file")

        # And there is data in this file, and it comes from the yaml file of
        # conf
        with open(_config_path, 'r', encoding='utf-8') as file:
            yaml_config = yaml.load(file.read(), Loader=yaml.FullLoader)

        with open(path, 'r', encoding='utf-8') as files:
            yaml_success = yaml.load(files.read(), Loader=yaml.FullLoader)

        self.assertEqual(
            len(yaml_config),
            len(yaml_success),
            msg="The success file is inconsistent with the original yaml file")

        # Compare name and priority
        success_name_priority = dict()
        config_name_priority = dict()
        len_con = len(yaml_config)
        for i in range(len_con):
            success_name_priority[yaml_success[i]["database_name"]] = \
                yaml_success[i]["priority"]
            config_name_priority[yaml_config[i]["dbname"]] = \
                yaml_config[i]["priority"]

        self.assertEqual(
            success_name_priority,
            config_name_priority,
            msg="The database and priority after initialization are"
                "inconsistent with the original file")
