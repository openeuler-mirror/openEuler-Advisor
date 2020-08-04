#!/usr/bin/python3
"""
Description: Simple encapsulation of sqlalchemy orm framework operation database
Class: DBHelper
"""
import os
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
from packageship import system_config


class DBHelper():
    """
    Description: Database connection, operation public class
    Attributes:
        user_name: Username
        password: Password
        ip_address: Ip address
        port: Port
        db_name: Database name
        db_type: Database type
        session: Session
    """
    # The base class inherited by the data model
    BASE = declarative_base()

    def __init__(self, user_name=None, password=None, ip_address=None,  # pylint: disable=R0913
                 port=None, db_name=None, db_type=None, **kwargs):
        """
        Description: Class instance initialization

        """
        self.user_name = user_name
        self._readconfig = ReadConfig()
        if self.user_name is None:
            self.user_name = self._readconfig.get_database('user_name')

        self.password = password
        if self.password is None:
            self.password = self._readconfig.get_database('password')

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
        self._create_engine()
        self.session = None

    def _create_engine(self):
        """
        Description: Create a database connection object
        Args:

        Returns:
        Raises:
            DisconnectionError: A disconnect is detected on a raw DB-API connection.

        """
        if self.db_type.startswith('sqlite'):
            if not self.db_name:
                raise DbnameNoneException(
                    'The connected database name is empty')
            self.engine = create_engine(
                self.db_type + self.db_name, encoding='utf-8', convert_unicode=True,
                connect_args={'check_same_thread': False})
        else:
            if all([self.user_name, self.password, self.ip_address, self.port, self.db_name]):
                # create connection object
                self.engine = create_engine(URL(**{'database': self.db_name,
                                                   'username': self.user_name,
                                                   'password': self.password,
                                                   'host': self.ip_address,
                                                   'port': self.port,
                                                   'drivername': self.db_type}),
                                            encoding='utf-8',
                                            convert_unicode=True)
            else:
                raise DisconnectionError(
                    'A disconnect is detected on a raw DB-API connection')

    def _db_file_path(self):
        """
        Description: load the path stored in the sqlite database
        Args:

        Returns:
        Raises:

        """
        self.database_file_path = self._readconfig.get_system(
            'data_base_path')
        if not self.database_file_path:
            self.database_file_path = system_config.DATABASE_FOLDER_PATH
        if not os.path.exists(self.database_file_path):
            os.makedirs(self.database_file_path)

    def __enter__(self):
        """
        Description: functional description:Create a context manager for the database connection
        Args:

        Returns:
            Class instance
        Raises:

        """

        session = sessionmaker()
        if not hasattr(self, 'engine'):
            raise DisconnectionError('Abnormal database connection')
        session.configure(bind=self.engine)

        self.session = session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Description: functional description:Release the database connection pool
                     and close the connection
        Args:

        Returns:
            exc_type: Abnormal type
            exc_val: Abnormal value
            exc_tb: Abnormal table
        Raises:

        """
        self.session.close()

    @classmethod
    def create_all(cls, db_name=None):
        """
        Description: functional description:Create all database tables
        Args:
            db_name: Database name
        Returns:

        Raises:

        """

        cls.BASE.metadata.create_all(bind=cls(db_name=db_name).engine)

    def create_table(self, tables):
        """
        Description: Create a single table
        Args:
            tables: Table
        Returns:

        Raises:
        """
        meta = MetaData(self.engine)
        for table_name in DBHelper.BASE.metadata.tables.keys():
            if table_name in tables:
                table = DBHelper.BASE.metadata.tables[table_name]
                table.metadata = meta
                table.create()

    def add(self, entity):
        """
        Description: Insert a single data entity
        Args:
            entity: Data entity
        Return:
            If the addition is successful, return the corresponding entity, otherwise return None
        Raises:
            ContentNoneException: An exception occurred while content is none
            SQLAlchemyError: An exception occurred while creating the database
        """

        if entity is None:
            raise ContentNoneException(
                'The added entity content cannot be empty')

        try:
            self.session.add(entity)

        except SQLAlchemyError as sql_error:
            self.session.rollback()
            raise Error(sql_error)
        else:
            self.session.commit()
            return entity

    def batch_add(self, dicts, model):
        """
        Description:tables for adding databases in bulk
        Args:
            dicts:Entity dictionary data to be added
            model:Solid model class
        Returns:

        Raises:
            TypeError: An exception occurred while incoming type does not meet expectations
            SQLAlchemyError: An exception occurred while creating the database
        """

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
        except SQLAlchemyError as sql_error:
            self.session.rollback()
            raise Error(sql_error)
        else:
            self.session.commit()
