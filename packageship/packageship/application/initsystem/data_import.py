#!/usr/bin/python3
"""
Description: Initialization of data import
            Import the data in the sqlite database into the mysql database
Class: InitDataBase,MysqlDatabaseOperations,SqliteDatabaseOperations
"""
import os
import pathlib
import yaml
from sqlalchemy.exc import SQLAlchemyError, InternalError
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper
from packageship.libs.exception import ContentNoneException
from packageship.libs.exception import DatabaseRepeatException
from packageship.libs.exception import Error
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.log import Log
from packageship.application.models.package import src_pack
from packageship.application.models.package import bin_pack
from packageship.application.models.package import bin_requires
from packageship.application.models.package import src_requires
from packageship.application.models.package import bin_provides
from packageship.application.models.package import maintenance_info
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
        self._read_config = ReadConfig()

        self.db_type = self._read_config.get_database('dbtype')
        self.sql = None
        self._database = None
        self.mainter_infos = dict()
        if self.db_type is None:
            self.db_type = 'mysql'

        if self.db_type not in ['mysql', 'sqlite']:
            _msg = "The database type is incorrectly configured.\
                The system temporarily supports only sqlite and mysql databases"
            LOGGER.logger.error(_msg)
            raise Error(_msg)
        self._sqlite_db = None

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
                'system initialization configuration file \
                    does not exist: %s' % self.config_file_path)
        # load yaml configuration file
        with open(self.config_file_path, 'r', encoding='utf-8') as file_context:
            init_database_config = yaml.load(
                file_context.read(), Loader=yaml.FullLoader)
            if init_database_config is None:
                raise ContentNoneException(
                    'The content of the database initialization configuration file cannot be empty')
            if not isinstance(init_database_config, list):
                raise TypeError('wrong type of configuration file')
            for config_item in init_database_config:
                if not isinstance(config_item, dict):
                    raise TypeError('wrong type of configuration file')
            return init_database_config

    def init_data(self):
        """
        Initialization of the database

        Raises:
            IOError: An error occurred while deleting the database information file
        """
        if getattr(self, 'config_file_datas', None) is None or \
                self.config_file_datas is None:
            raise ContentNoneException('The content of the database initialization \
                configuration file is empty')

        if self.__exists_repeat_database():
            raise DatabaseRepeatException(
                'There is a duplicate database configuration')
        if not InitDataBase.delete_settings_file():
            raise IOError(
                'An error occurred while deleting the database configuration file')

        # Create a database maintained by benchmark information
        if self.db_type == 'mysql':
            MysqlDatabaseOperations(
                db_name='maintenance.information',
                tables=['maintenance_info'],
                is_datum=True).create_database()
        else:
            SqliteDatabaseOperations(
                db_name='maintenance.information',
                tables=['maintenance_info'],
                is_datum=True).create_database()
        # Obtain the maintenance information of the previous data of the system
        self._get_maintenance_info()

        for database in self.config_file_datas:
            if not database.get('dbname'):
                LOGGER.logger.error(
                    'The database name in the database initialization configuration file is empty')
                continue
            priority = database.get('priority')
            if not isinstance(priority, int) or priority < 0 or priority > 100:
                LOGGER.logger.error('The priority value type in the database initialization \
                    configuration file is incorrect')
                continue
            if database.get('status') not in ['enable', 'disable']:
                LOGGER.logger.error('The database status value in the database \
                    initialization configuration file is incorrect')
                continue
            # Initialization data
            self._init_data(database)

    def _create_database(self, database):
        """
        create related databases

        Args:
            database: Initialize the configuration content of the database
        Returns:
            The generated mysql database or sqlite database
        Raises:
            SQLAlchemyError: Abnormal database operation
        """

        db_name = database.get('dbname')
        tables = ['src_pack', 'bin_pack',
                  'bin_requires', 'src_requires', 'bin_provides']
        if self.db_type == 'mysql':
            creatadatabase = MysqlDatabaseOperations(
                db_name=db_name, tables=tables)
            if not creatadatabase.create_database():
                raise SQLAlchemyError("failed to create database or table")
            return db_name
        self._sqlite_db = SqliteDatabaseOperations(
            db_name=db_name, tables=tables)

        sqltedb_file = self._sqlite_db.create_database()
        if sqltedb_file is None:
            raise SQLAlchemyError(
                "failed to create database or table")
        return sqltedb_file

    def _init_data(self, database):
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
            db_name = self._create_database(database)
            # 2. get the data of binary packages and source packages
            src_db_file = database.get('src_db_file')
            bin_db_file = database.get('bin_db_file')

            if src_db_file is None or bin_db_file is None:
                raise ContentNoneException(
                    'The path to the sqlite file in the database initialization configuration \
                    is incorrect ')
            if os.path.exists(src_db_file) or os.path.exists(bin_db_file):
                raise FileNotFoundError("sqlite file {src} or {bin} does not exist, please \
                    check and try again".format(src=src_db_file, bin=bin_db_file))
            # 3. Obtain temporary source package files and binary package files
            if self.__save_data(src_db_file, bin_db_file, db_name):
                # Update the configuration file of the database
                database_content = {
                    'database_name': database.get('dbname'),
                    'priority': database.get('priority'),
                    'status': database.get('status')
                }
                InitDataBase.__updata_settings_file(
                    database_content=database_content)

        except (SQLAlchemyError, ContentNoneException, TypeError,
                Error, FileNotFoundError) as error_msg:
            LOGGER.logger.error(error_msg)
            # Delete the specified database
            self.__del_fail_database(database.get('dbname'))

    def __del_fail_database(self, db_name):
        try:
            if self.db_type == 'mysql':
                MysqlDatabaseOperations.drop_database(db_name)
            else:
                self._sqlite_db.drop_database()
        except (IOError, Error) as exception_msg:
            LOGGER.logger.error(exception_msg)

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

    def __save_data(self, src_db_file, bin_db_file, db_name):
        """
        integration of multiple data files

        Args:
            src_package_paths: Source package database file
            bin_package_paths: Binary package database file
        Returns:
            Path of the generated temporary database file
        Raises:

        """
        try:
            with DBHelper(db_name=src_db_file, db_type='sqlite:///', import_database=True) \
                    as database:
                self._database = database
                # Save data related to source package
                self._save_src_packages(db_name)
                self._save_src_requires(db_name)

            with DBHelper(db_name=bin_db_file, db_type='sqlite:///', import_database=True)\
                    as database:
                self._database = database
                # Save binary package related data
                self._save_bin_packages(db_name)
                self._save_bin_requires(db_name)
                self._save_bin_provides(db_name)
        except (SQLAlchemyError, ContentNoneException) as sql_error:
            LOGGER.logger.error(sql_error)
            self.__del_fail_database(db_name)
            return False
        else:
            return True

    def _save_src_packages(self, db_name):
        """
        Save the source package data

        Args:
            db_name: Saved database name
        Returns:

        Raises:

        """
        # Query all source packages
        self.sql = " select * from packages "
        packages_datas = self.__get_data()
        if packages_datas is None:
            raise ContentNoneException(
                '{db_name}:There is no relevant data in the source \
                    package provided '.format(db_name=db_name))
        for index, src_package_item in enumerate(packages_datas):
            maintaniner, maintainlevel = self._get_mainter_info(
                src_package_item.get('name'), src_package_item.get('version'))
            packages_datas[index]['maintaniner'] = maintaniner
            packages_datas[index]['maintainlevel'] = maintainlevel

        with DBHelper(db_name=db_name) as database:
            database.batch_add(packages_datas, src_pack)

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
            raise ContentNoneException('{db_name}: The package data that the source package \
                depends on is empty'.format(db_name=db_name))
        with DBHelper(db_name=db_name) as database:
            database.batch_add(requires_datas, src_requires)

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
                '{db_name}:There is no relevant data in the provided \
                     binary package '.format(db_name=db_name))
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
            database.batch_add(bin_packaegs, bin_pack)

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
                '{db_name}:There is no relevant data in the provided binary \
                    dependency package'.format(db_name=db_name))

        with DBHelper(db_name=db_name) as database:
            database.batch_add(requires_datas, bin_requires)

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
                '{db_name}:There is no relevant data in the provided \
                    binary component '.format(db_name=db_name))

        with DBHelper(db_name=db_name) as database:
            database.batch_add(provides_datas, bin_provides)

    def _get_maintenance_info(self):
        """
        Description: Obtain the information of the maintainer

        Returns:
            Maintainer related information
        Raises:
            SQLAlchemyError: An error occurred while executing the sql statement
        """
        try:
            with DBHelper(db_name='maintenance.information') as database:
                for info in database.session.query(maintenance_info).all():
                    if info.name not in self.mainter_infos.keys():
                        self.mainter_infos[info.name] = []
                    self.mainter_infos[info.name].append({
                        'version': info.version,
                        'maintaniner': info.maintaniner,
                        'maintainlevel': info.maintainlevel
                    })
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)

    def _get_mainter_info(self, src_package_name, version):
        '''
            Get the maintainer information of the source package

        Args:
            src_package_name: Source package name
            version: Source package version number
        Returns:
            Maintainer's name
        Raises:

        '''
        maintenance_infos = self.mainter_infos.get(src_package_name)
        maintaniner = None
        if maintenance_infos:
            for maintenance_item in maintenance_infos:
                if maintenance_item.get('version') == version:
                    maintaniner = (maintenance_item.get(
                        'maintaniner'), maintenance_item.get('maintainlevel'))
                    break
        if maintaniner is None:
            maintaniner = (None, None)
        return maintaniner

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
    def __updata_settings_file(**Kwargs):
        """
        update some configuration files related to the database in the system

        Args:
            **Kwargs: data related to configuration file nodes
            database_name: Name database
        Returns:

        Raises:
            FileNotFoundError: The specified file was not found
            IOError: File or network operation io abnormal
        """
        try:
            if not os.path.exists(system_config.DATABASE_FILE_INFO):
                pathlib.Path(system_config.DATABASE_FILE_INFO).touch()
            with open(system_config.DATABASE_FILE_INFO, 'a+', encoding='utf8') as file_context:
                setting_content = []
                if 'database_content' in Kwargs.keys():
                    content = Kwargs.get('database_content')
                    if content:
                        setting_content.append(content)
                yaml.dump(setting_content, file_context)

        except FileNotFoundError as not_found:
            LOGGER.logger.error(not_found)
        except IOError as exception_msg:
            LOGGER.logger.error(exception_msg)

    @staticmethod
    def delete_settings_file():
        """
        Delete the configuration file of the database

        Args:

        Returns:
            True if the deletion is successful, otherwise false
        Raises:
            IOError: File or network operation io abnormal
        """

        try:
            if os.path.exists(system_config.DATABASE_FILE_INFO):
                os.remove(system_config.DATABASE_FILE_INFO)
        except (IOError, Error) as exception_msg:
            LOGGER.logger.error(exception_msg)
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
        if self.db_type == 'mysql':
            del_result = MysqlDatabaseOperations.drop_database(db_name)
        else:
            if not hasattr(self, '_sqlite_db') or getattr(self, '_sqlite_db') is None:
                self._sqlite_db = SqliteDatabaseOperations(db_name=db_name)
            del_result = self._sqlite_db.drop_database()

        if del_result:
            try:
                file_read = open(
                    system_config.DATABASE_FILE_INFO, 'r', encoding='utf-8')
                _databases = yaml.load(
                    file_read.read(), Loader=yaml.FullLoader)
                for database in _databases:
                    if database.get('database_name') == db_name:
                        _databases.remove(database)
                # Delete the successfully imported database configuration node
                with open(system_config.DATABASE_FILE_INFO, 'w+', encoding='utf-8') as file_context:
                    yaml.safe_dump(_databases, file_context)
            except (IOError, Error) as del_config_error:
                LOGGER.logger.error(del_config_error)
            finally:
                file_read.close()


class MysqlDatabaseOperations():
    """
    Related to database operations, creating databases, creating tables

    Attributes:
        db_name: The name of the database
        create_database_sql: SQL statement to create a database
        drop_database_sql: Delete the SQL statement of the database
    """

    def __init__(self, db_name, tables=None, is_datum=False):
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
        self.is_datum = is_datum

    def create_database(self):
        """
        create a mysql database

        Returns:
            True if successful, otherwise false
        Raises:
            SQLAlchemyError: An exception occurred while creating the database
        """

        with DBHelper(db_name='mysql') as data_base:

            try:
                # create database
                if not self.is_datum:
                    data_base.session.execute(self.drop_database_sql)
                data_base.session.execute(self.create_database_sql)
            except (SQLAlchemyError, InternalError) as exception_msg:
                LOGGER.logger.error(exception_msg)
                return False
            else:
                # create  tables
                return self.__create_tables()

    @classmethod
    def drop_database(cls, db_name):
        """
        Delete the database according to the specified name

        Args:
            db_name: The name of the database to be deleted
        Returns:
            True if successful, otherwise false
        Raises:
            SQLAlchemyError: An exception occurred while creating the database
        """
        if db_name is None:
            raise IOError(
                "The name of the database to be deleted cannot be empty")
        with DBHelper(db_name='mysql') as data_base:
            drop_database = '''  drop DATABASE if exists `{db_name}` '''.format(
                db_name=db_name)
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
                    database.create_table(self.tables)

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

    def __init__(self, db_name, tables=None, is_datum=False, ** kwargs):
        """
        Class instance initialization

        Args:
            db_name: Database name
            kwargs: data related to configuration file nodes
        """
        self.db_name = db_name
        self._read_config = ReadConfig()
        if getattr(kwargs, 'database_path', None) is None:
            self._database_file_path()
        else:
            self.database_file_folder = kwargs.get('database_path')
        self.tables = tables
        self.is_datum = is_datum

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

    def create_database(self):
        """
        create sqlite database and table

        Returns:
            After successful generation, return the database file address,
            otherwise return none
        Raises:
            FileNotFoundError: The specified folder path does not exist
            SQLAlchemyError: An error occurred while generating the database
        """
        if self.database_file_folder is None:
            raise FileNotFoundError('Database folder does not exist')

        _db_file = os.path.join(
            self.database_file_folder, self.db_name)

        if os.path.exists(_db_file + '.db'):
            os.remove(_db_file + '.db')

        # create a  sqlite database
        if (self.is_datum and not os.path.exists(_db_file + '.db')) or not self.is_datum:
            with DBHelper(db_name=_db_file) as database:
                try:
                    database.create_table(self.tables)
                except (SQLAlchemyError, InternalError) as create_table_err:
                    LOGGER.logger.error(create_table_err)
                    return None

        return _db_file

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
