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
from packageship.libs.exception import Error
from packageship.libs.exception import ConfigurationException

try:

    system_config.SYS_CONFIG_PATH = os.path.join(
        os.path.dirname(
            system_config.BASE_PATH),
        'test',
        'common_files',
        'package.ini')

    system_config.DATABASE_FOLDER_PATH = os.path.join(os.path.dirname(
        system_config.BASE_PATH), 'test', 'init_system_files', 'dbs')

    from test.base_code.init_config_path import init_config

except Error:
    raise Error

from sqlalchemy.exc import SQLAlchemyError
from packageship.application.initsystem.data_import import InitDataBase
from packageship.libs.exception import ContentNoneException
from packageship.libs.exception import DatabaseRepeatException
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.application.models.package import DatabaseInfo
from packageship.libs.dbutils import DBHelper


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
            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
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
            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
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

            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
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
            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
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
            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
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
            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            shutil.copyfile(_config_path, _config_path + '.bak')
            with open(_config_path, 'r', encoding='utf-8') as file:
                origin_yaml = yaml.load(file.read(), Loader=yaml.FullLoader)
                for obj in origin_yaml:
                    obj["priority"] = "-1"
                with open(_config_path, 'w', encoding='utf-8') as w_f:
                    yaml.dump(origin_yaml, w_f)
            InitDataBase(config_file_path=_config_path).init_data()

            with DBHelper(db_name='lifecycle') as data_name:
                name_list = data_name.session.query(
                    DatabaseInfo.name).order_by(DatabaseInfo.priority).all()
                init_database_date = [name[0] for name in name_list]
            self.assertEqual(
                init_database_date,
                [],
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
        try:
            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            InitDataBase(config_file_path=_config_path).init_data()
            with DBHelper(db_name='lifecycle') as data_name:
                name_list = data_name.session.query(
                    DatabaseInfo.name, DatabaseInfo.priority).order_by(DatabaseInfo.priority).all()
                data_list = [dict(zip(ven.keys(), ven)) for ven in name_list]
            _config_path = ReadConfig(
                system_config.SYS_CONFIG_PATH).get_system('init_conf_path')
            with open(_config_path, 'r', encoding='utf-8') as file:
                origin_yaml = yaml.load(file.read(), Loader=yaml.FullLoader)
                origin_list = list()
                for item in origin_yaml:
                    data_dict = dict()
                    data_dict['name'] = item.get("dbname")
                    data_dict['priority'] = item.get("priority")
                    origin_list.append(data_dict)

            self.assertEqual(
                data_list,
                origin_list,
                msg="The name and priority of the data generated by the initialization are correct")

        except (Error, SQLAlchemyError, FileNotFoundError, yaml.YAMLError):
            return None
