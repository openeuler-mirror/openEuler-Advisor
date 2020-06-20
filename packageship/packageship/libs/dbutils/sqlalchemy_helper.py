'''
Simple encapsulation of sqlalchemy orm framework operation database

'''
import os
from packageship.system_config import DATABASE_FOLDER_PATH
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from packageship.libs.exception.ext import Error
from packageship.libs.exception.ext import DbnameNoneException
from packageship.libs.exception.ext import ContentNoneException
from packageship.libs.configutils.readconfig import ReadConfig


class DBHelper():

    # The base class inherited by the data model
    BASE = declarative_base()

    def __init__(self, user_name=None, passwrod=None, ip_address=None, \
                port=None, db_name=None, db_type=None, *args, **kwargs):
        self.user_name = user_name
        self._readconfig = ReadConfig()
        if self.user_name is None:
            self.user_name = self._readconfig.get_database('user_name')

        self.passwrod = passwrod
        if self.passwrod is None:
            self.passwrod = self._readconfig.get_database('password')

        self.ip_address = ip_address

        if self.ip_address is None:
            self.ip_address = self._readconfig.get_database('host')

        self.port = port

        if self.port is None:
            self.port = self._readconfig.get_database('port')

        self.db_name = db_name

        if self.db_name is None:
            self.db_name = self._readconfig.get_database('database')

        self.db_type = db_type

        if self.db_type is None:
            # read the contents of the configuration file
            _db_type = self._readconfig.get_database('dbtype')
            if _db_type is None or _db_type == 'mysql':
                self.db_type = 'mysql+pymysql'
            else:
                self.db_type = 'sqlite:///'
                if 'import_database' not in kwargs.keys():
                    self._db_file_path()
                    self.db_name = os.path.join(
                        self.database_file_path, self.db_name + '.db')
        if self.db_type.startswith('sqlite'):
            if not self.db_name:
                raise DbnameNoneException(
                    'The connected database name is empty')
            self.engine = create_engine(
                self.db_type + self.db_name, encoding='utf-8', convert_unicode=True)
        else:
            if all([self.user_name, self.passwrod, self.ip_address, self.port, self.db_name]):
                # create connection object
                self.engine = create_engine(URL(**{'database': self.db_name,
                                                   'username': self.user_name,
                                                   'password': self.passwrod,
                                                   'host': self.ip_address,
                                                   'port': self.port,
                                                   'drivername': self.db_type}), \
                                                    encoding='utf-8', \
                                                    convert_unicode=True)
            else:
                raise DisconnectionError(
                    'A disconnect is detected on a raw DB-API connection')
        self.session = None

    def _db_file_path(self):
        '''
            load the path stored in the sqlite database
        '''
        self.database_file_path = self._readconfig.get_system(
            'data_base_path')
        if not self.database_file_path:
            self.database_file_path = DATABASE_FOLDER_PATH
        if not os.path.exists(self.database_file_path):
            os.makedirs(self.database_file_path)

    def __enter__(self):
        '''
        functional description:Create a context manager for the database connection
        '''

        Session = sessionmaker()
        if getattr(self, 'engine') is None:
            raise DisconnectionError('Abnormal database connection')
        Session.configure(bind=self.engine)

        self.session = Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        functional description:Release the database connection pool and close the connection
        '''

        self.session.close()

    @classmethod
    def create_all(cls, db_name=None):
        '''
        functional description:Create all database tables
        parameter:
        return value:
        exception description:
        modify record:
        '''

        cls.BASE.metadata.create_all(bind=cls(db_name=db_name).engine)

    def create_table(self, tables):
        '''
            Create a single table
        '''
        meta = MetaData(self.engine)
        for table_name in DBHelper.BASE.metadata.tables.keys():
            from sqlalchemy import Table
            if table_name in tables:
                table = DBHelper.BASE.metadata.tables[table_name]
                table.metadata = meta
                table.create()

    def add(self, entity):
        '''
        functional description:Insert a single data entity
        parameter:
        return value:
            If the addition is successful, return the corresponding entity, otherwise return None
        '''

        if entity is None:
            raise ContentNoneException(
                'The added entity content cannot be empty')

        try:
            self.session.add(entity)

        except SQLAlchemyError as e:
            raise Error(e)
        else:
            self.session.commit()
            return entity

    def batch_add(self, dicts, model):
        '''
        functional description:tables for adding databases in bulk
        parameter:
        :param dicts:Entity dictionary data to be added
        :param model:Solid model class
        '''

        if model is None:
            raise ContentNoneException('solid model must be specified')

        if dicts is None:
            raise ContentNoneException(
                'The inserted data content cannot be empty')

        if not isinstance(dicts, list):
            raise TypeError(
                'The input for bulk insertion must be a dictionary \
                list with the same fields as the current entity')
        try:
            self.session.execute(
                model.__table__.insert(),
                dicts
            )
        except SQLAlchemyError as e:
            raise Error(e)
        else:
            self.session.commit()
