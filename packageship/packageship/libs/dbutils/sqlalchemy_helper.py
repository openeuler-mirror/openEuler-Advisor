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
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from packageship.libs.exception.ext import Error
from packageship.libs.exception.ext import DbnameNoneException
from packageship.libs.exception.ext import ContentNoneException
from packageship.libs.conf import configuration


class BaseHelper():
    """
    Description: Base class for data manipulation
    """

    def __init__(self):
        self.engine = None


class MysqlHelper(BaseHelper):
    """
    Description: mysql database connection related operations
    Attributes:
        user_name: Database connection username
        password: Database connection password
        host: Remote server address
        port: Port
        database: Operational database name
        connection_type: Database connection type
    """

    def __init__(self, user_name=None, password=None, host=None,  # pylint: disable=unused-argument
                 port=None, database=None, **kwargs):
        super(MysqlHelper, self).__init__()
        self.user_name = user_name or configuration.USER_NAME
        self.password = password or configuration.PASSWORD
        self.host = host or configuration.HOST
        self.port = port or configuration.PORT
        self.database = database or configuration.DATABASE
        self.connection_type = 'mysql+pymysql'

    def create_database_engine(self):
        """
        Description: Create a database connection object
        Args:

        Returns:
        Raises:
            DisconnectionError: A disconnect is detected on a raw DB-API connection.

        """
        if not all([self.user_name, self.password, self.host, self.port, self.database]):
            raise DisconnectionError(
                'A disconnect is detected on a raw DB-API connection')
        # create connection object
        self.engine = create_engine(URL(**{'database': self.database,
                                           'username': self.user_name,
                                           'password': self.password,
                                           'host': self.host,
                                           'port': self.port,
                                           'drivername': self.connection_type}),
                                    encoding='utf-8',
                                    convert_unicode=True)


class SqliteHlper(BaseHelper):
    """
    Description: sqlite database connection related operations
    Attributes:
        connection_type: Database connection type
        database: Operational database name
    """

    def __init__(self, database, **kwargs):
        super(SqliteHlper, self).__init__()
        self.connection_type = 'sqlite:///'
        if 'complete_route_db' in kwargs.keys():
            self.database = database
        else:
            self.database = self._database_file_path(database)

    def _database_file_path(self, database):
        """
        Description: load the path stored in the sqlite database
        Args:

        Returns:
        Raises:

        """
        _database_folder_path = configuration.DATABASE_FOLDER_PATH
        try:
            if not os.path.exists(_database_folder_path):
                os.makedirs(_database_folder_path)
        except IOError:
            pass
        return os.path.join(_database_folder_path, database + '.db')

    def create_database_engine(self):
        """
        Description: Create a database connection object
        Args:

        Returns:
        Raises:
            DisconnectionError: A disconnect is detected on a raw DB-API connection

        """
        if not self.database:
            raise DbnameNoneException(
                'The connected database name is empty')
        self.engine = create_engine(
            self.connection_type + self.database, encoding='utf-8', convert_unicode=True,
            connect_args={'check_same_thread': False})


class DBHelper(BaseHelper):
    """
    Description: Database connection, operation public class
    Attributes:
        user_name: Username
        password: Password
        host: Remote server address
        port: Port
        db_name: Database name
        connection_type: Database type
        session: Session
    """
    # The base class inherited by the data model
    BASE = declarative_base()
    ENGINE_CONTAINER = dict()

    def __init__(self, user_name=None, password=None, host=None,  # pylint: disable=R0913
                 port=None, db_name=None, connection_type=None, **kwargs):
        """
        Description: Class instance initialization

        """
        super(DBHelper, self).__init__()
        self._database_engine = {
            'mysql': MysqlHelper,
            'sqlite': SqliteHlper
        }
        if connection_type is None:
            connection_type = configuration.DATABASE_ENGINE_TYPE
        self._engine_pool = connection_type + '_' + db_name
        _database_engine = self._database_engine.get(connection_type)
        if _database_engine is None:
            raise DisconnectionError(
                'Database engine connection failed'
                'Not currently supported %s database' % connection_type)
        _engine = self.ENGINE_CONTAINER.get(self._engine_pool)
        if _engine:
            self.engine = _engine
        else:
            _engine = _database_engine(user_name=user_name, password=password,
                                       host=host, port=port, database=db_name, **kwargs)
            _engine.create_database_engine()
            self.engine = _engine.engine
            self.ENGINE_CONTAINER[self._engine_pool] = self.engine
        self.session = None

    def create_engine(self):
        """
            Create related database engine connections
        """
        session = sessionmaker()
        try:
            session.configure(bind=self.engine)
        except DisconnectionError:
            self.ENGINE_CONTAINER.pop(self._engine_pool)
        else:
            self.session = session()
        return self

    def __enter__(self):
        """
        Description: functional description:Create a context manager for the database connection
        Args:

        Returns:
            Class instance
        Raises:

        """

        database_engine = self.create_engine()
        return database_engine

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
        if isinstance(exc_type, (AttributeError)):
            raise SQLAlchemyError(exc_val)
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
            if isinstance(sql_error, OperationalError):
                raise OperationalError
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

        if not dicts:
            raise ContentNoneException(
                'The inserted data content cannot be empty')

        if not isinstance(dicts, list):
            raise TypeError(
                "The input for bulk insertion must be a dictionary"
                "list with the same fields as the current entity")
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
