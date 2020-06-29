'''
    Initialization of data import
    Import the data in the sqlite database into the mysql database
'''
import os
import pathlib
import yaml
from sqlalchemy.exc import SQLAlchemyError, InternalError
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper
from packageship.libs.exception import ContentNoneException
from packageship.libs.exception import DatabaseRepeatException
from packageship.libs.exception import DataMergeException
from packageship.libs.exception import Error
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.log import Log
from packageship.application.models.package import bin_pack, src_pack, pack_requires, pack_provides
from packageship.application.initsystem.datamerge import MergeData
from packageship.application.models.temporarydb import src_package
from packageship.application.models.temporarydb import src_requires
from packageship.application.models.temporarydb import bin_package
from packageship.application.models.temporarydb import bin_requiresment
from packageship.application.models.temporarydb import bin_provides
from packageship.system_config import DATABASE_SUCCESS_FILE
from packageship.system_config import DATABASE_FOLDER_PATH

LOGGER = Log(__name__)


class InitDataBase():
    '''
        Database initialization, generate multiple databases and data based on configuration files
    '''

    def __init__(self, config_file_path=None):
        '''
        parameter:
            config_file_path:The path of the configuration file that needs to initialize
            the database in the project
        '''

        self.config_file_path = config_file_path

        if self.config_file_path:
            # yaml configuration file content
            self.config_file_datas = self.__read_config_file()

        self._read_config = ReadConfig()

        self.db_type = self._read_config.get_database('dbtype')

        if self.db_type is None:
            self.db_type = 'mysql'

        if self.db_type not in ['mysql', 'sqlite']:
            LOGGER.logger.error("database type configuration error")
            raise Exception('database type configuration error')

    def __read_config_file(self):
        '''
        functional description:
            Read the contents of the configuration file load each node data in the yaml
            configuration file as a list to return
        '''

        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(
                'system initialization configuration file does not exist')
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
        '''
            functional description:Initialization of the database
        '''
        if getattr(self, 'config_file_datas', None) is None or \
                self.config_file_datas is None:
            raise ContentNoneException('Initialization file content is empty')

        if self.__exists_repeat_database():
            raise DatabaseRepeatException(
                'There is a duplicate database configuration')
        if not InitDataBase.delete_settings_file():
            raise IOError(
                'An error occurred while deleting the database configuration file')

        # Create a database maintained by benchmark information
        if self.db_type == 'mysql':
            MysqlDatabaseOperations(
                'maintenance.information').create_datum_database()
        else:
            SqliteDatabaseOperations(
                'maintenance.information').create_datum_database()

        for database in self.config_file_datas:
            if not database.get('dbname'):
                continue
            priority = database.get('priority')
            if not isinstance(priority, int) or priority < 0 or priority > 100:
                continue
            status = database.get('status')
            if status not in ['enable', 'disable']:
                continue

            # Initialization data
            self._init_data(database)

    def _create_database(self, database):
        '''
        create related databases
        '''
        db_name = database.get('dbname')
        self._sqlite_db = SqliteDatabaseOperations(db_name=db_name)

        if self.db_type == 'mysql':
            creatadatabase = MysqlDatabaseOperations(db_name)
            if not creatadatabase.create_database():
                raise SQLAlchemyError("failed to create database or table")
            return db_name

        sqltedb_file = self._sqlite_db.create_sqlite_database()
        if sqltedb_file is None:
            raise SQLAlchemyError(
                "failed to create database or table")
        return sqltedb_file

    def _init_data(self, database):
        '''
        functional description:data initialization operation
        parameter:
            database:database configuration information
        '''
        try:
            db_file = None
            # 1. create a database and related tables in the database
            db_name = self._create_database(database)
            # 2. get the data of binary packages and source packages
            src_package_paths = database.get('src_db_file')
            bin_package_paths = database.get('bin_db_file')

            if src_package_paths is None or bin_package_paths is None:
                raise ContentNoneException(
                    'The configured database file path is empty')
            if not isinstance(src_package_paths, list) \
                    or not isinstance(bin_package_paths, list):
                raise TypeError(
                    'The source code and binary path types in the initialization file are abnormal')
            # 3. Obtain temporary source package files and binary package files
            db_file = self.file_merge(
                src_package_paths, bin_package_paths)
            # 4. dependencies between combined data
            self.data_relationship(db_file)
            # # 5. save data
            self.save_data(db_name)

        except (SQLAlchemyError, ContentNoneException,
                DataMergeException, TypeError, Error) as error_msg:
            # Delete the specified database
            try:
                if self.db_type == 'mysql':
                    MysqlDatabaseOperations.drop_database(
                        database.get('dbname'))
                else:
                    self._sqlite_db.drop_database()

            except (IOError, Error) as exception_msg:
                LOGGER.logger.error(exception_msg)
        else:
            # Update the configuration file of the database
            database_content = {
                'database_name': database.get('dbname'),
                'priority': database.get('priority'),
                'status': database.get('status')
            }
            InitDataBase.__updata_settings_file(
                database_content=database_content)
        finally:
            try:
                if os.path.exists(db_file):
                    os.remove(db_file)
            except (IOError, UnboundLocalError) as error_msg:
                LOGGER.logger.error(error_msg)

    def _src_package_relation(self, src_package_data):
        '''
            Mapping of data relations of source packages
        '''
        _src_package_name = src_package_data.name
        _src_package = {
            "name": src_package_data.name,
            "version": src_package_data.version,
            "license": src_package_data.rpm_license,
            "sourceURL": src_package_data.url,
            "Maintaniner": src_package_data.maintaniner
        }
        if _src_package_name not in self._src_packages.keys():
            self._src_packages[_src_package_name] = _src_package
        else:
            # Determine the version number
            if src_package_data.version > \
                    self._src_packages[_src_package_name]['version']:

                self._src_packages[_src_package_name] = _src_package
                # Delete previous version
                for key in [names[0] for names in self._src_package_names.items()
                            if _src_package_name == names[1]]:
                    del self._src_package_names[key]

        self._src_package_names[src_package_data.pkgKey] = _src_package_name

    def _src_requires_relation(self, src_requires_data):
        '''
            Source package dependent package data relationship mapping
        '''
        _src_package_name = self._src_package_names.get(
            src_requires_data.pkgKey)
        if _src_package_name:
            if _src_package_name not in self._src_requires_dicts.keys():
                self._src_requires_dicts[_src_package_name] = []
            self._src_requires_dicts[_src_package_name].append({
                'name': src_requires_data.name
            })

    def _bin_package_relation(self, bin_package_data):
        '''
            Binary package relationship mapping problem
        '''
        _bin_pkg_key = bin_package_data.pkgKey
        self._bin_package_name[bin_package_data.name] = _bin_pkg_key

        src_package_name = bin_package_data.src_pack_name
        _bin_package = {
            'name': bin_package_data.name,
            'version': bin_package_data.version,
            'relation': True
        }
        if src_package_name not in self._bin_package_dicts.keys():
            self._bin_package_dicts[src_package_name] = []

        # Determine whether the version number is consistent with the source code package
        # If they are the same, an association relationship is established.
        for index, bin_package_item in enumerate(self._bin_package_dicts[src_package_name]):
            if bin_package_item.get('name') == bin_package_data.name:
                if bin_package_item.get('version') < bin_package_data.version:
                    self._bin_package_dicts[src_package_name][index]['relation'] = False

        self._bin_package_dicts[src_package_name].append(_bin_package)

    def _bin_requires_relation(self, bin_requires_data):
        '''
            Binary package dependency package relationship mapping problem
        '''
        _bin_pkg_key = bin_requires_data.pkgKey
        if _bin_pkg_key:
            if _bin_pkg_key not in self._bin_requires_dicts:
                self._bin_requires_dicts[_bin_pkg_key] = []

            self._bin_requires_dicts[_bin_pkg_key].append({
                'name': bin_requires_data.name
            })

    def _bin_provides_relation(self, bin_provides_data):
        '''
            Binary package provided by the relationship mapping problem
        '''
        _bin_pkg_key = bin_provides_data.pkgKey
        if _bin_pkg_key:
            if _bin_pkg_key not in self._bin_provides_dicts:
                self._bin_provides_dicts[_bin_pkg_key] = []
            self._bin_provides_dicts[_bin_pkg_key].append({
                'name': bin_provides_data.name
            })

    def data_relationship(self, db_file):
        '''
        dependencies between combined data
        '''
        self._bin_provides_dicts = dict()
        self._bin_requires_dicts = dict()
        self._bin_package_name = dict()
        self._bin_package_dicts = dict()
        self._src_requires_dicts = dict()
        self._src_packages = dict()
        self._src_package_names = dict()
        try:
            with DBHelper(db_name=db_file, db_type='sqlite:///') as database:
                # source package data
                for src_package_item in database.session.query(src_package).all():
                    self._src_package_relation(src_package_item)

                # combine all dependent packages of source packages
                for src_requires_item in database.session.query(src_requires).all():
                    self._src_requires_relation(src_requires_item)

                # combine all binary packages
                for bin_package_item in database.session.query(bin_package).all():
                    self._bin_package_relation(bin_package_item)

                # combine all dependent packages under the current binary package
                for bin_requires_item in database.session.query(
                        bin_requiresment).all():
                    self._bin_requires_relation(bin_requires_item)

                # combine the packages provided by the current binary package

                for bin_provides_item in database.session.query(bin_provides).all():
                    self._bin_provides_relation(bin_provides_item)

        except Error as error_msg:
            LOGGER.logger.error(error_msg)

    def file_merge(self, src_package_paths, bin_package_paths):
        '''
            integration of multiple data files
        '''
        _db_file = os.path.join(
            self._sqlite_db.database_file_folder, 'temporary_database')

        if os.path.exists(_db_file):
            os.remove(_db_file)
        # create a temporary sqlite database
        with DBHelper(db_name=_db_file, db_type='sqlite:///') as database:
            tables = ['src_package', 'src_requires',
                      'bin_package', 'bin_requiresment', 'bin_provides']
            database.create_table(tables)

        _src_package_key = 1
        # load all source package files and import the files into it
        for src_file in src_package_paths:
            load_sqlite_data = MergeData(db_file=src_file)

            # Combine data from all source packages

            _src_package_key, src_merge_result = load_sqlite_data.src_file_merge(
                src_package_key=_src_package_key, db_file=_db_file)
            if not src_merge_result:
                raise DataMergeException(
                    'abnormal multi-file database integration')

        # load binary package file
        _bin_package_key = 1
        for bin_file in bin_package_paths:
            load_sqlite_data = MergeData(db_file=bin_file)

            # Combine all binary package data
            _bin_package_key, bin_merge_result = load_sqlite_data.bin_file_merge(
                bin_package_key=_bin_package_key, db_file=_db_file)
            if not bin_merge_result:
                raise DataMergeException(
                    'abnormal multi-file database integration')
        return _db_file

    def __exists_repeat_database(self):
        '''
        functional description:Determine if the same database name exists
        parameter:
        return value:
        exception description:
        modify record:
        '''

        db_names = [name.get('dbname')
                    for name in self.config_file_datas]

        if len(set(db_names)) != len(self.config_file_datas):
            return True

        return False

    def _save_bin_package(self, src_packages):
        '''
            Save binary package data
        '''
        bin_packages = []
        for package_data in src_packages:
            try:
                bin_package_datas = self._bin_package_dicts.pop(
                    package_data.name)
            except KeyError:
                bin_package_datas = None

            if bin_package_datas:
                for bin_package_item in bin_package_datas:
                    bin_package_dict = {
                        'name': bin_package_item.get('name'),
                        'version': bin_package_item.get('version'),
                        'srcIDkey': None
                    }
                    if bin_package_item.get('relation'):
                        bin_package_dict['srcIDkey'] = package_data.id
                    bin_packages.append(bin_package_dict)

            # source package dependency  package
            src_requires_datas = self._src_requires_dicts.get(
                package_data.name)
            if src_requires_datas:
                for src_requires_item in src_requires_datas:
                    requires_name = src_requires_item.get('name')
                    if requires_name:
                        if requires_name not in self.requires.keys():
                            self.requires[requires_name] = []
                        self.requires[requires_name].append({
                            'name': src_requires_item.get('name'),
                            'srcIDkey': package_data.id,
                            'depProIDkey': None,
                            'binIDkey': None
                        })

        # organization independent binary package

        for bin_packs in self._bin_package_dicts.values():
            for bin_pack_item in bin_packs:
                bin_packages.append({
                    'name': bin_pack_item.get('name'),
                    'version': bin_pack_item.get('version'),
                    'srcIDkey': None
                })
        return bin_packages

    def _save_bin_provides(self, bin_packages):
        '''
            Save package data provided by binary
        '''
        bin_provides_list = []
        for bin_pack_entity in bin_packages:

            # Get the pkgKey of the current binary package
            pkg_key = self._bin_package_name.get(bin_pack_entity.name)

            if self._bin_requires_dicts.get(pkg_key):
                for bin_requires_item in self._bin_requires_dicts.get(pkg_key):
                    requires_name = bin_requires_item.get('name')
                    if requires_name:
                        if requires_name not in self.requires.keys():
                            self.requires[requires_name] = []
                        self.requires[requires_name].append({
                            'name': bin_requires_item.get('name'),
                            'binIDkey': bin_pack_entity.id,
                            'depProIDkey': None,
                            'srcIDkey': None
                        })

            if self._bin_provides_dicts.get(pkg_key):
                for bin_provides_item in self._bin_provides_dicts.get(pkg_key):
                    bin_provides_list.append({
                        'name': bin_provides_item.get('name'),
                        'binIDkey': bin_pack_entity.id
                    })
        return bin_provides_list

    def save_data(self, db_name):
        '''
            save related package data
        '''
        with DBHelper(db_name=db_name) as data_base:
            # Add source package data
            data_base.batch_add(
                [src_package_item[1] for src_package_item in self._src_packages.items()], src_pack)

            self.requires = dict()

            # Save dependency data of binary packages and source packages

            data_base.batch_add(self._save_bin_package(
                data_base.session.query(src_pack).all()), bin_pack)

            # Save all packages and dependent packages provided by the binary package

            data_base.batch_add(self._save_bin_provides(
                data_base.session.query(bin_pack).all()), pack_provides)

            all_requires = []
            for provides_item in data_base.session.query(pack_provides).all():
                if provides_item.name in self.requires.keys():
                    for requires_item in self.requires[provides_item.name]:
                        requires_item['depProIDkey'] = provides_item.id
                        all_requires.append(requires_item)

            data_base.batch_add(all_requires, pack_requires)

    @staticmethod
    def __updata_settings_file(**Kwargs):
        '''
            update some configuration files related to the database in the system
            parameter:
                **Kwargs：data related to configuration file nodes
                database_name: Name database
                priority: priority
        '''
        try:
            if not os.path.exists(DATABASE_SUCCESS_FILE):
                pathlib.Path(DATABASE_SUCCESS_FILE).touch()
            with open(DATABASE_SUCCESS_FILE, 'a+', encoding='utf8') as file_context:
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
        '''
        functional description:Delete the configuration file of the database
        parameter:
        return value:
        exception description:
        modify record:
        '''
        try:
            if os.path.exists(DATABASE_SUCCESS_FILE):
                os.remove(DATABASE_SUCCESS_FILE)
        except (IOError, Error) as exception_msg:
            LOGGER.logger.error(exception_msg)
            return False
        else:
            return True

    def delete_db(self, db_name):
        '''
            Delete the database
        '''
        if self.db_type == 'mysql':
            del_result = MysqlDatabaseOperations.drop_database(db_name)
        else:
            if not hasattr(self, '_sqlite_db'):
                self._sqlite_db = SqliteDatabaseOperations(db_name=db_name)
            del_result = self._sqlite_db.drop_database()

        if del_result:
            try:
                file_read = open(DATABASE_SUCCESS_FILE, 'r', encoding='utf-8')
                _databases = yaml.load(
                    file_read.read(), Loader=yaml.FullLoader)
                for database in _databases:
                    if database.get('database_name') == db_name:
                        _databases.remove(database)
                # Delete the successfully imported database configuration node
                with open(DATABASE_SUCCESS_FILE, 'w+', encoding='utf-8') as file_context:
                    yaml.safe_dump(_databases, file_context)
            except (IOError, Error) as del_config_error:
                LOGGER.logger.error(del_config_error)
            finally:
                file_read.close()


class MysqlDatabaseOperations():
    '''
        Related to database operations, creating databases, creating tables
    '''

    def __init__(self, db_name):

        self.db_name = db_name
        self.create_database_sql = ''' CREATE DATABASE if not exists `{db_name}` \
                                    DEFAULT CHARACTER SET utf8mb4; '''.format(db_name=self.db_name)
        self.drop_database_sql = '''drop DATABASE if exists `{db_name}` '''.format(
            db_name=self.db_name)

    def create_database(self):
        '''
            functional description:create a database
        '''

        with DBHelper(db_name='mysql') as data_base:

            try:
                # create database
                data_base.session.execute(self.drop_database_sql)
                data_base.session.execute(self.create_database_sql)
            except SQLAlchemyError as exception_msg:
                LOGGER.logger.error(exception_msg)
                return False
            else:
                # create  tables
                return self.__create_tables()

    @classmethod
    def drop_database(cls, db_name):
        '''
        functional description:Delete the database according to the specified name
        parameter:
        :db_name:The name of the database
        return value:
        exception description:
        modify record:
        '''
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
        '''
            Create the specified data table
        '''
        try:
            with DBHelper(db_name=self.db_name) as database:
                tables = ['src_pack', 'bin_pack', 'pack_provides',
                          'pack_requires']
                database.create_table(tables)

        except SQLAlchemyError as exception_msg:
            LOGGER.logger.error(exception_msg)
            return False
        else:
            return True

    def create_datum_database(self):
        '''
            Create a benchmark database to save the maintainer's information
        '''
        with DBHelper(db_name='mysql') as data_base:
            # create database
            try:
                data_base.session.execute(self.create_database_sql)
            except SQLAlchemyError as exception_msg:
                LOGGER.logger.error(exception_msg)
                return False
            else:
                # create  tables
                return self.__create_datum_tables()

    def __create_datum_tables(self):
        '''
            Create a data table of maintainer information
        '''
        try:
            with DBHelper(db_name=self.db_name) as database:
                tables = ['maintenance_info']
                database.create_table(tables)
        except InternalError as exists_table_err:
            LOGGER.logger.error(exists_table_err)
            return True
        except (SQLAlchemyError, Error) as exception_msg:
            LOGGER.logger.error(exception_msg)
            return False

        else:
            return True


class SqliteDatabaseOperations():
    '''
        sqlite database related operations
    '''

    def __init__(self, db_name, **kwargs):

        self.db_name = db_name
        self._read_config = ReadConfig()
        if getattr(kwargs, 'database_path', None) is None:
            self.database_file_path()
        else:
            self.database_file_folder = kwargs.get('database_path')

    def database_file_path(self):
        '''
            Database file path
        '''
        self.database_file_folder = self._read_config.get_system(
            'data_base_path')
        if not self.database_file_folder:
            self.database_file_folder = DATABASE_FOLDER_PATH

        if not os.path.exists(self.database_file_folder):
            try:
                os.makedirs(self.database_file_folder)
            except IOError as makedirs_error:
                LOGGER.logger.error(makedirs_error)
                self.database_file_folder = None

    def create_sqlite_database(self):
        '''
            create sqlite database and table
        '''
        if self.database_file_folder is None:
            raise FileNotFoundError('Database folder does not exist')

        _db_file = os.path.join(
            self.database_file_folder, self.db_name)

        if os.path.exists(_db_file+'.db'):
            os.remove(_db_file + '.db')

        # create a  sqlite database
        with DBHelper(db_name=_db_file) as database:
            tables = ['src_pack', 'bin_pack',
                      'pack_requires', 'pack_provides']
            try:
                database.create_table(tables)
            except SQLAlchemyError as create_table_err:
                LOGGER.logger.error(create_table_err)
                return None

        return _db_file

    def drop_database(self):
        '''
            Delete the specified sqlite database
        '''
        try:
            db_path = os.path.join(
                self.database_file_folder, self.db_name+'.db')
            if os.path.exists(db_path):
                os.remove(db_path)
        except IOError as exception_msg:
            LOGGER.logger.error(exception_msg)
            return False
        else:
            return True

    def create_datum_database(self):
        '''
            create sqlite database and table
        '''
        if self.database_file_folder is None:
            raise FileNotFoundError('Database folder does not exist')

        _db_file = os.path.join(
            self.database_file_folder, self.db_name)

        if not os.path.exists(_db_file+'.db'):
            # create a  sqlite database
            with DBHelper(db_name=_db_file) as database:
                tables = ['maintenance_info']
                try:
                    database.create_table(tables)
                except SQLAlchemyError as create_table_err:
                    LOGGER.logger.error(create_table_err)
                    return None
        return _db_file
