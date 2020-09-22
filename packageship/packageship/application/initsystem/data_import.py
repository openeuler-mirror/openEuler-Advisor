#!/usr/bin/python3
"""
Description: Initialization of data import
            Import the data in the sqlite database into the mysql database
Class: InitDataBase,MysqlDatabaseOperations,SqliteDatabaseOperations
"""
import os
import yaml
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, InternalError
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper
from packageship.libs.exception import ContentNoneException
from packageship.libs.exception import DatabaseRepeatException
from packageship.libs.exception import Error
from packageship.libs.exception import ConfigurationException
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.log import Log
from packageship.application.models.package import SrcPack
from packageship.application.models.package import DatabaseInfo
from packageship.application.models.package import BinPack
from packageship.application.models.package import BinRequires
from packageship.application.models.package import SrcRequires
from packageship.application.models.package import BinProvides
from packageship.application.models.package import BinFiles
from packageship.application.models.package import Packages
from packageship import system_config

LOGGER = Log(__name__)


class InitDataBase():
    """
    Description: Database initialization, generate multiple databases and data
                 based on configuration files

    Attributes:
        config_file_path: configuration file path
        config_file_datas: initialize the configuration content of the database
        db_type: type of database
    """

    def __init__(self, config_file_path=None):
        """
        Description: Class instance initialization

        Args:
            config_file_path: Configuration file path
        """
        self.config_file_path = config_file_path

        if self.config_file_path:
            # yaml configuration file content
            self.config_file_datas = self.__read_config_file()
        self._read_config = ReadConfig(system_config.SYS_CONFIG_PATH)
        self.db_type = 'sqlite'
        self.sql = None
        self._database = None
        self._sqlite_db = None
        self._database_engine = {
            'sqlite': SqliteDatabaseOperations,
            'mysql': MysqlDatabaseOperations
        }
        self.database_name = None
        self._tables = ['src_pack', 'bin_pack',
                        'bin_requires', 'src_requires', 'bin_provides', 'bin_files']
        # Create life cycle related databases and tables
        if not self.create_database(db_name='lifecycle',
                                    tables=['packages_issue',
                                            'packages_maintainer',
                                            'databases_info'],
                                    storage=True):
            raise SQLAlchemyError(
                'Failed to create the specified database and table：lifecycle')

    def __read_config_file(self):
        """
        Read the contents of the configuration file load each
        node data in the yaml configuration file as a list to return

        Returns:
            Initialize the contents of the database configuration file
        Raises:
            FileNotFoundError: The specified file does not exist
            TypeError: Wrong type of data
        """

        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(
                "system initialization configuration file"
                "does not exist: %s" % self.config_file_path)
        # load yaml configuration file
        with open(self.config_file_path, 'r', encoding='utf-8') as file_context:
            try:
                init_database_config = yaml.load(
                    file_context.read(), Loader=yaml.FullLoader)
            except yaml.YAMLError as yaml_error:

                raise ConfigurationException(
                    "The format of the yaml configuration"
                    "file is wrong please check and try again:{0}".format(yaml_error))

            if init_database_config is None:
                raise ConfigurationException(
                    'The content of the database initialization configuration file cannot be empty')
            if not isinstance(init_database_config, list):
                raise ConfigurationException(
                    "The format of the initial database configuration file"
                    "is incorrect.When multiple databases need to be initialized,"
                    "it needs to be configured in the form of multiple"
                    "nodes:{}".format(self.config_file_path))
            for config_item in init_database_config:
                if not isinstance(config_item, dict):
                    raise ConfigurationException(
                        "The format of the initial database"
                        "configuration file is incorrect, and the value in a single node should"
                        "be presented in the form of key - val pairs:{}".format(self.config_file_path))
            return init_database_config

    def init_data(self):
        """
        Initialization of the database

        Raises:
            IOError: An error occurred while deleting the database information file
        """
        if getattr(self, 'config_file_datas', None) is None or \
                self.config_file_datas is None:
            raise ContentNoneException("The content of the database initialization"
                                       "configuration file is empty")

        if self.__exists_repeat_database():
            raise DatabaseRepeatException(
                'There is a duplicate database configuration')

        if not self.__clear_database():
            raise SQLAlchemyError(
                'Failed to delete the database, throw an exception')

        if not InitDataBase.__clear_database_info():
            raise SQLAlchemyError(
                'Failed to clear data in database_info or lifecycle database')

        for database_config in self.config_file_datas:
            if not database_config.get('dbname'):
                LOGGER.logger.error(
                    'The database name in the database initialization configuration file is empty')
                continue
            priority = database_config.get('priority')
            if not isinstance(priority, int) or priority < 0 or priority > 100:
                LOGGER.logger.error("The priority value type in the database initialization"
                                    "configuration file is incorrect")
                continue
            lifecycle_status_val = database_config.get('lifecycle')
            if lifecycle_status_val not in ('enable', 'disable'):
                LOGGER.logger.error("The value of the life cycle in the initialization"
                                    "configuration file can only be enable or disable")
                continue
            # Initialization data
            self._init_data(database_config)

    def _create_database(self, db_name, tables, storage=False):
        """
        create related databases

        Args:
            database_config: Initialize the configuration content of the database_config
        Returns:
            The generated mysql database or sqlite database
        Raises:
            SQLAlchemyError: Abnormal database operation
        """
        _database_engine = self._database_engine.get(self.db_type)
        if not _database_engine:
            raise Error("The database engine is set incorrectly,"
                        "currently only the following engines are supported: %s "
                        % '、'.join(self._database_engine.keys()))
        _create_table_result = _database_engine(
            db_name=db_name, tables=tables, storage=storage).create_database(self)
        return _create_table_result

    def _init_data(self, database_config):
        """
        data initialization operation

        Args:
            database: Initialize the configuration content of the database
        Returns:

        Raises:
            ContentNoneException: Exception with empty content
            TypeError: Data type error
            SQLAlchemyError: Abnormal database operation
            IOError: An error occurred while deleting the database information file
        """

        try:
            # 1. create a database and related tables in the database
            _db_name = database_config.get('dbname')
            _create_database_result = self._create_database(
                _db_name, self._tables)
            if not _create_database_result:
                raise SQLAlchemyError(
                    'Failed to create the specified database and table：%s'
                    % database_config['dbname'])
            # 2. get the data of binary packages and source packages
            src_db_file = database_config.get('src_db_file')
            bin_db_file = database_config.get('bin_db_file')

            if src_db_file is None or bin_db_file is None:
                raise ContentNoneException(
                    "The path to the sqlite file in the database initialization"
                    "configuration is incorrect ")
            if not os.path.exists(src_db_file) or not os.path.exists(bin_db_file):
                raise FileNotFoundError(
                    "sqlite file {src} or {bin} does not exist, please"
                    "check and try again".format(src=src_db_file, bin=bin_db_file))
            # 3. Obtain temporary source package files and binary package files
            if self.__save_data(database_config,
                                self.database_name):
                # Update the configuration file of the database
                database_content = {
                    'database_name': _db_name,
                    'priority': database_config.get('priority'),
                }
                InitDataBase.__update_database_info(database_content)

        except (SQLAlchemyError, ContentNoneException, TypeError,
                Error, FileNotFoundError) as error_msg:
            LOGGER.logger.error(error_msg)
            # Delete the specified database
            self.__del_database(_db_name)

    def __del_database(self, db_name):
        try:
            _database_engine = self._database_engine.get(self.db_type)
            del_result = _database_engine(db_name=db_name).drop_database()
            return del_result
        except (IOError, Error) as exception_msg:
            LOGGER.logger.error(exception_msg)
            return False

    @staticmethod
    def __columns(cursor):
        """
        functional description:Returns all the column names
        queried by the current cursor

        Args:
            cursor: Cursor
        Returns:
            The first columns
        Raises:

        """
        return [col[0] for col in cursor.description]

    def __get_data(self):
        """
        According to different sql statements, query related table data

        Args:

        Returns:

        Raises:

        """
        if self.sql is None:
            return None
        try:
            src_packages_data = self._database.session.execute(self.sql)
            columns = InitDataBase.__columns(
                src_packages_data.cursor)
            return [dict(zip(columns, row)) for row in src_packages_data.fetchall()]
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            return None

    def __save_data(self, database_config, db_name):
        """
        integration of multiple data files

        Args:
            src_package_paths: Source package database file
            bin_package_paths: Binary package database file
        Returns:
            Path of the generated temporary database file
        Raises:

        """
        src_db_file = database_config.get('src_db_file')
        bin_db_file = database_config.get('bin_db_file')
        table_name = database_config.get('dbname')
        lifecycle_status_val = database_config.get('lifecycle')
        try:
            with DBHelper(db_name=src_db_file, db_type='sqlite:///', complete_route_db=True) \
                    as database:
                self._database = database
                # Save data related to source package
                self._save_src_packages(
                    db_name, table_name, lifecycle_status_val)
                self._save_src_requires(db_name)

            with DBHelper(db_name=bin_db_file, db_type='sqlite:///', complete_route_db=True)\
                    as database:
                self._database = database
                # Save binary package related data
                self._save_bin_packages(db_name)
                self._save_bin_requires(db_name)
                self._save_bin_provides(db_name)
                self._save_bin_files(db_name)
        except (SQLAlchemyError, ContentNoneException) as sql_error:
            LOGGER.logger.error(sql_error)
            self.__del_database(db_name)
            return False
        else:
            return True

    def _save_src_packages(self, db_name, table_name, lifecycle_status_val):
        """
        Save the source package data

        Args:
            db_name: Saved database name
        """
        # Query all source packages
        self.sql = " select * from packages "
        packages_datas = self.__get_data()
        if packages_datas is None:
            raise ContentNoneException(
                "{db_name}:There is no relevant data in the source "
                "package provided ".format(db_name=db_name))
        for index, src_package_item in enumerate(packages_datas):
            try:
                src_package_name = '-'.join([src_package_item.get('name'),
                                             src_package_item.get('version'),
                                             src_package_item.get(
                                                 'release') + '.src.rpm'
                                             ])
            except AttributeError as exception_msg:
                src_package_name = None
                LOGGER.logger.warning(exception_msg)
            finally:
                packages_datas[index]['src_name'] = src_package_name
        with DBHelper(db_name=db_name) as database:
            database.batch_add(packages_datas, SrcPack)
        if lifecycle_status_val == 'enable':
            InitDataBase._storage_packages(table_name, packages_datas)

    @staticmethod
    def _storage_packages(table_name, package_data):
        """
            Bulk storage of source code package data
        """
        add_packages = []
        cls_model = Packages.package_meta(table_name)
        pkg_keys = ('name', 'url', 'rpm_license', 'version',
                    'release', 'summary', 'description')
        with DBHelper(db_name="lifecycle") as database:
            if table_name not in database.engine.table_names():
                database.create_table([table_name])
            # Query data that already exists in the database
            exist_packages_dict = dict()
            for pkg in database.session.query(cls_model).all():
                exist_packages_dict[pkg.name] = pkg
            _packages = []
            for pkg in package_data:
                _package_dict = {key: pkg[key] for key in pkg_keys}
                _packages.append(_package_dict)

            # Combine all package data, save or update
            for package_item in _packages:
                package_model = exist_packages_dict.get(package_item['name'])
                if package_model:
                    for key, val in package_item.items():
                        setattr(package_model, key, val)
                else:
                    add_packages.append(package_item)

            if add_packages:
                database.batch_add(add_packages, cls_model)
                database.session.commit()

    def _save_src_requires(self, db_name):
        """
        Save the dependent package data of the source package

        Args:
            db_name：Name database
        Returns:

        Raises:

        """
        # Query all source packages
        self.sql = " select * from requires "
        requires_datas = self.__get_data()
        if requires_datas is None:
            raise ContentNoneException(
                "{db_name}: The package data that the source package "
                "depends on is empty".format(db_name=db_name))
        with DBHelper(db_name=db_name) as database:
            database.batch_add(requires_datas, SrcRequires)

    def _save_bin_packages(self, db_name):
        """
        Save binary package data

        Args:
            db_name：Name database
        Returns:

        Raises:

        """
        self.sql = " select * from packages "
        bin_packaegs = self.__get_data()
        if bin_packaegs is None:
            raise ContentNoneException(
                "{db_name}:There is no relevant data in the provided "
                "binary package ".format(db_name=db_name))
        for index, bin_package_item in enumerate(bin_packaegs):
            try:
                src_package_name = bin_package_item.get('rpm_sourcerpm').split(
                    '-' + bin_package_item.get('version'))[0]
            except AttributeError as exception_msg:
                src_package_name = None
                LOGGER.logger.warning(exception_msg)
            finally:
                bin_packaegs[index]['src_name'] = src_package_name

        with DBHelper(db_name=db_name) as database:
            database.batch_add(bin_packaegs, BinPack)

    def _save_bin_requires(self, db_name):
        """
        Save the dependent package data of the binary package

        Args:
            db_name：Name database
        Returns:

        Raises:

        """
        self.sql = " select * from requires "
        requires_datas = self.__get_data()
        if requires_datas is None:
            raise ContentNoneException(
                "{db_name}:There is no relevant data in the provided binary "
                "dependency package".format(db_name=db_name))

        with DBHelper(db_name=db_name) as database:
            database.batch_add(requires_datas, BinRequires)

    def _save_bin_provides(self, db_name):
        """
        Save the component data provided by the binary package

        Args:
            db_name：Name database
        Returns:

        Raises:

        """
        self.sql = " select * from provides "
        provides_datas = self.__get_data()
        if provides_datas is None:
            raise ContentNoneException(
                "{db_name}:There is no relevant data in the provided "
                "binary component ".format(db_name=db_name))

        with DBHelper(db_name=db_name) as database:
            database.batch_add(provides_datas, BinProvides)

    def _save_bin_files(self, db_name):

        self.sql = " select * from files "
        files_datas = self.__get_data()
        if files_datas is None:
            raise ContentNoneException(
                "{db_name}:There is no relevant binary file installation "
                "path data in the provided database ".format(db_name=db_name))

        with DBHelper(db_name=db_name) as database:
            database.batch_add(files_datas, BinFiles)

    def __exists_repeat_database(self):
        """
        Determine if the same database name exists

        Returns:
            True if there are duplicate databases, false otherwise
        Raises:

        """
        db_names = [name.get('dbname')
                    for name in self.config_file_datas]

        if len(set(db_names)) != len(self.config_file_datas):
            return True

        return False

    @staticmethod
    def __update_database_info(database_content):
        """
        Update the database_name table

        Args:
            database_content:
                Dictionary of database names and priorities
        Returns:

        """
        try:
            with DBHelper(db_name="lifecycle") as database_name:
                name = database_content.get("database_name")
                priority = database_content.get("priority")
                database_name.add(DatabaseInfo(
                    name=name, priority=priority
                ))
                database_name.session.commit()
        except (SQLAlchemyError, Error, AttributeError) as error:
            LOGGER.logger.error(error)

    @staticmethod
    def __clear_database_info():
        """
            Delete the tables in the lifecycle except for the specific three tables
        Returns:

        """
        try:
            with DBHelper(db_name="lifecycle") as database_name:
                clear_sql = """delete from databases_info;"""
                database_name.session.execute(text(clear_sql))
                table_list = database_name.engine.table_names()
                for item in table_list:
                    if item not in ['packages_maintainer', 'databases_info', 'packages_issue']:
                        drop_sql = '''DROP TABLE if exists `{table_name}`'''.format(
                            table_name=item)
                        database_name.session.execute(text(drop_sql))
                database_name.session.commit()
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            return False
        else:
            return True

    def __clear_database(self):
        """
            Delete database
        Returns:

        """
        try:
            with DBHelper(db_name='lifecycle') as data_name:
                name_data_list = data_name.session.query(
                    DatabaseInfo.name).order_by(DatabaseInfo.priority).all()
                name_list = [name[0] for name in name_data_list if name[0]]
                for item in name_list:
                    self.__del_database(item)
        except (SQLAlchemyError, Error, IOError) as error:
            LOGGER.logger.error(error)
            return False
        else:
            return True

    def delete_db(self, db_name):
        """
        delete the database

        Args:
            db_name: The name of the database
        Returns:

        Raises:
            IOError: File or network operation io abnormal
        """
        try:
            del_result = True
            with DBHelper(db_name='lifecycle') as database_name:
                database_name.session.query(DatabaseInfo).filter(
                    DatabaseInfo.name == db_name).delete()
                drop_sql = '''DROP TABLE if exists `{table_name}`''' \
                    .format(table_name=db_name)
                database_name.session.execute(text(drop_sql))
                database_name.session.commit()
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            del_result = False
        if del_result:
            del_result = self.__del_database(db_name)
        return del_result

    def create_database(self, db_name, tables=None, storage=True):
        """
            Create databases and tables related to the package life cycle

            Args:
                db_name: The name of the database
                tables: Table to be created
        """
        _create_database_result = self._create_database(
            db_name, tables, storage)
        return _create_database_result


class MysqlDatabaseOperations():
    """
    Related to database operations, creating databases, creating tables

    Attributes:
        db_name: The name of the database
        create_database_sql: SQL statement to create a database
        drop_database_sql: Delete the SQL statement of the database
    """

    def __init__(self, db_name, tables=None, storage=False):
        """
        Class instance initialization

        Args:
            db_name: Database name
        """
        self.db_name = db_name
        self.create_database_sql = ''' CREATE DATABASE if not exists `{db_name}` \
                                    DEFAULT CHARACTER SET utf8mb4; '''.format(db_name=self.db_name)
        self.drop_database_sql = '''drop DATABASE if exists `{db_name}` '''.format(
            db_name=self.db_name)
        self.tables = tables
        self.storage = storage

    def create_database(self, init_db):
        """
        create a mysql database

        Returns:
            True if successful, otherwise false
        Raises:
            SQLAlchemyError: An exception occurred while creating the database
        """
        _create_success = True
        if isinstance(init_db, InitDataBase):
            init_db.database_name = self.db_name
        with DBHelper(db_name='mysql') as data_base:

            try:
                # create database
                if not self.storage:
                    data_base.session.execute(self.drop_database_sql)
                data_base.session.execute(self.create_database_sql)
            except InternalError as internal_error:
                LOGGER.logger.info(internal_error)
            except SQLAlchemyError as exception_msg:
                LOGGER.logger.error(exception_msg)
                return False
        if self.tables:
            _create_success = self.__create_tables()
        return _create_success

    def drop_database(self):
        """
        Delete the database according to the specified name

        Args:
            db_name: The name of the database to be deleted
        Returns:
            True if successful, otherwise false
        Raises:
            SQLAlchemyError: An exception occurred while creating the database
        """
        if self.db_name is None:
            raise IOError(
                "The name of the database to be deleted cannot be empty")
        with DBHelper(db_name='mysql') as data_base:
            drop_database = '''  drop DATABASE if exists `{db_name}` '''.format(
                db_name=self.db_name)
            try:
                data_base.session.execute(drop_database)
            except SQLAlchemyError as exception_msg:
                LOGGER.logger.error(exception_msg)
                return False
            else:
                return True

    def __create_tables(self):
        """
        Create the specified data table

        Returns:
            True if successful, otherwise false
        Raises:
            SQLAlchemyError: An exception occurred while creating the database
        """
        try:
            with DBHelper(db_name=self.db_name) as database:
                if self.tables:
                    _tables = list(set(self.tables).difference(
                        set(database.engine.table_names())))
                    database.create_table(_tables)

        except SQLAlchemyError as exception_msg:
            LOGGER.logger.error(exception_msg)
            return False
        else:
            return True


class SqliteDatabaseOperations():
    """
    sqlite database related operations

    Attributes:
        db_name: Name database
        database_file_folder: Database folder path
    """

    def __init__(self, db_name, tables=None, storage=False, ** kwargs):
        """
        Class instance initialization

        Args:
            db_name: Database name
            kwargs: data related to configuration file nodes
        """
        self.db_name = db_name
        self._read_config = ReadConfig(system_config.SYS_CONFIG_PATH)
        if getattr(kwargs, 'database_path', None) is None:
            self._database_file_path()
        else:
            self.database_file_folder = kwargs.get('database_path')
        self.tables = tables
        self.storage = storage

    def _database_file_path(self):
        """
        Database file path

        Returns:

        Raises:
            IOError: File or network operation io abnormal
        """
        self.database_file_folder = self._read_config.get_system(
            'data_base_path')
        if not self.database_file_folder:
            self.database_file_folder = system_config.DATABASE_FOLDER_PATH

        if not os.path.exists(self.database_file_folder):
            try:
                os.makedirs(self.database_file_folder)
            except IOError as makedirs_error:
                LOGGER.logger.error(makedirs_error)
                self.database_file_folder = None

    def create_database(self, init_db):
        """
        create sqlite database and table

        Returns:
            After successful generation, return the database file address,
            otherwise return none
        Raises:
            FileNotFoundError: The specified folder path does not exist
            SQLAlchemyError: An error occurred while generating the database
        """
        _create_success = False
        if self.database_file_folder is None:
            raise FileNotFoundError('Database folder does not exist')

        _db_file = os.path.join(
            self.database_file_folder, self.db_name)

        if not self.storage and os.path.exists(_db_file + '.db'):
            os.remove(_db_file + '.db')

        # create a sqlite database
        with DBHelper(db_name=_db_file) as database:
            try:
                if self.tables:
                    _tables = list(set(self.tables).difference(
                        set(database.engine.table_names())))
                    database.create_table(_tables)
            except (SQLAlchemyError, InternalError) as create_table_err:
                LOGGER.logger.error(create_table_err)
                return _create_success
        if isinstance(init_db, InitDataBase):
            init_db.database_name = _db_file
            _create_success = True
        return _create_success

    def drop_database(self):
        """
        Delete the specified sqlite database

        Returns:
            Return true after successful deletion, otherwise return false
        Raises:
            IOError: An io exception occurred while deleting the specified database file
        """
        try:
            db_path = os.path.join(
                self.database_file_folder, self.db_name + '.db')
            if os.path.exists(db_path):
                os.remove(db_path)
        except IOError as exception_msg:
            LOGGER.logger.error(exception_msg)
            return False
        else:
            return True
