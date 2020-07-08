#!/usr/bin/python3
"""
Description: Integration of multiple sqlite file data, including reading
             sqlite database and inserting data
Class: MergeData
"""
from sqlalchemy.exc import SQLAlchemyError
from packageship.application.models.temporarydb import src_package
from packageship.application.models.temporarydb import src_requires
from packageship.application.models.temporarydb import bin_package
from packageship.application.models.temporarydb import bin_requiresment
from packageship.application.models.temporarydb import bin_provides
from packageship.application.models.package import maintenance_info
from packageship.libs.dbutils import DBHelper
from packageship.libs.log import Log

LOGGER = Log(__name__)


class MergeData():
    """
    Description: Load data from sqlite database
    Attributes:
        db_file: Database file
        db_type: Connected database type
        datum_database: Base database name
    """

    def __init__(self, db_file):
        """
        Description: Class instance initialization
        Args:
            db_file: Database file
        """
        self.db_file = db_file
        self.db_type = 'sqlite:///'
        self.datum_database = 'maintenance.information'
        self.src_requires_dicts = None
        self.src_package_datas = None
        self.bin_provides_dicts = None
        self.bin_package_datas = None
        self.mainter_infos = None

    @staticmethod
    def __columns(cursor):
        """
        Description: functional description:Returns all the column names
                     queried by the current cursor
        Args:
            cursor: Cursor

        Returns:
            The first columns
        Raises:

        """
        return [col[0] for col in cursor.description]

    def get_package_data(self):
        """
        Description: get binary package or source package data
        Args:

        Returns:
            All source package data queried
        Raises:
            SQLAlchemyError: An error occurred while executing the sql statement
        """
        try:
            with DBHelper(db_name=self.db_file, db_type=self.db_type, import_database=True) \
                    as database:
                src_packages_data = database.session.execute(
                    "select pkgKey,name,version,rpm_license,url,rpm_sourcerpm from packages")
                columns = MergeData.__columns(
                    src_packages_data.cursor)
                return [dict(zip(columns, row)) for row in src_packages_data.fetchall()]
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            return None

    def get_requires_data(self):
        """
        Description: get dependent package data of binary package or source package
        Args:

        Returns:
            All dependent data queried
        Raises:
            SQLAlchemyError: An error occurred while executing the sql statement
        """
        try:
            with DBHelper(db_name=self.db_file, db_type=self.db_type, import_database=True) \
                    as database:
                requires = database.session.execute(
                    "select pkgKey,name from requires")
                columns = MergeData.__columns(requires.cursor)
                return [dict(zip(columns, row)) for row in requires.fetchall()]
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            return None

    def get_provides(self):
        """
        Description: get the dependency package provided by the binary package
        Args:

        Returns:
            Query the component data provided by all binary packages
        Raises:
            SQLAlchemyError: An error occurred while executing the sql statement
        """
        try:
            with DBHelper(db_name=self.db_file, db_type=self.db_type, import_database=True) \
                    as database:
                requires = database.session.execute(
                    "select pkgKey,name from provides")
                columns = MergeData.__columns(requires.cursor)
                return [dict(zip(columns, row)) for row in requires.fetchall()]
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            return None

    def get_maintenance_info(self):
        """
        Description: Obtain the information of the maintainer
        Args:

        Returns:
            Maintainer related information
        Raises:
            SQLAlchemyError: An error occurred while executing the sql statement
        """
        try:
            if not hasattr(self, 'mainter_infos'):
                self.mainter_infos = dict()
            with DBHelper(db_name=self.datum_database) as database:
                for info in database.session.query(maintenance_info).all():
                    if info.name not in self.mainter_infos.keys():
                        self.mainter_infos[info.name] = []
                    self.mainter_infos[info.name].append({
                        'version': info.version,
                        'maintaniner': info.maintaniner
                    })
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)

    def src_file_merge(self, src_package_key, db_file):
        """
        Description: Source code related data integration
        Args:
            src_package_key: The relevant key value of the source package
            db_file: Database file
        Returns:
            Key value after successful data combination
            (0, False) or (src_package_key, True)
        Raises:
            SQLAlchemyError: An error occurred while executing the sql statement
        """
        self.get_maintenance_info()

        self.__compose_src_package()

        self.__compose_src_rquires()

        # Combination of relationships between source packages and dependent packages
        src_requires_data = []
        for src_package_item in self.src_package_datas:
            src_package_key += 1
            requires = self.src_requires_dicts.get(
                src_package_item.get('pkgKey'))
            if requires:
                for src_requires_item in requires:
                    src_requires_item['pkgKey'] = src_package_key
                    src_requires_data.append(src_requires_item)
            src_package_item['pkgKey'] = src_package_key

        try:
            with DBHelper(db_name=db_file, db_type=self.db_type) as data_base:
                data_base.batch_add(self.src_package_datas, src_package)
                data_base.batch_add(src_requires_data, src_requires)
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            return (0, False)
        else:
            return (src_package_key, True)

    def __compose_src_package(self):
        """
        Description: Combine source package data
        Args:

        Returns:

        Raises:

        """
        if getattr(self, 'src_package_datas', None) is None:
            self.src_package_datas = []

        for src_package_item in self.get_package_data():
            src_package_name = src_package_item.get('name')
            if src_package_name:
                # Find the maintainer information of the current data
                maintenance_infos = self.mainter_infos.get(src_package_name)
                maintenance = []
                version = src_package_item.get('version')
                if self.mainter_infos.get(src_package_name):
                    for maintenance_item in maintenance_infos:
                        if maintenance_item.get('version') == version:
                            maintenance.append(maintenance_item)

                self.src_package_datas.append(
                    {
                        "name": src_package_item.get('name'),
                        "version": version,
                        "rpm_license": src_package_item.get('rpm_license'),
                        "url": src_package_item.get('url'),
                        "pkgKey": src_package_item.get('pkgKey'),
                        'maintaniner':
                            maintenance[0].get('maintaniner') if maintenance and len(
                                maintenance) > 0 else None
                    }
                )

    def __compose_src_rquires(self):
        """
        Description: Combine source package dependent package data
        Args:

        Returns:

        Raises:

        """
        if getattr(self, 'src_requires_dicts', None) is None:
            self.src_requires_dicts = dict()

        for src_requires_item in self.get_requires_data():
            pkg_key = src_requires_item.get('pkgKey')
            if pkg_key:
                if pkg_key not in self.src_requires_dicts.keys():
                    self.src_requires_dicts[pkg_key] = []
                self.src_requires_dicts[pkg_key].append(
                    {
                        'name': src_requires_item.get('name'),
                        'pkgKey': pkg_key
                    }
                )

    def __compose_bin_package(self):
        """
        Description: Combine binary package data
        Args:

        Returns:

        Raises:
            AttributeError
        """
        if getattr(self, 'bin_package_datas', None) is None:
            self.bin_package_datas = []

        for bin_package_item in self.get_package_data():
            try:
                src_package_name = bin_package_item.get('rpm_sourcerpm').split(
                    '-' + bin_package_item.get('version'))[0]
            except AttributeError as exception_msg:
                src_package_name = None
                LOGGER.logger.warning(exception_msg)
            else:
                self.bin_package_datas.append(
                    {
                        "name": bin_package_item.get('name'),
                        "version": bin_package_item.get('version'),
                        "license": bin_package_item.get('rpm_license'),
                        "sourceURL": bin_package_item.get('url'),
                        "src_pack_name": src_package_name,
                        "pkgKey": bin_package_item.get('pkgKey')
                    }
                )

    def __compose_bin_requires(self):
        """
        Description: Combining binary dependent package data
        Args:

        Returns:

        Raises:
        """
        if getattr(self, 'bin_requires_dicts', None) is None:
            self.bin_requires_dicts = dict()

        for bin_requires_item in self.get_requires_data():
            pkg_key = bin_requires_item.get('pkgKey')
            if pkg_key:
                if pkg_key not in self.bin_requires_dicts.keys():
                    self.bin_requires_dicts[pkg_key] = []
                self.bin_requires_dicts[pkg_key].append({
                    'name': bin_requires_item.get('name'),
                    'pkgKey': 0
                })

    def __compose_bin_provides(self):
        """
        Description: Combine binary package data
        Args:

        Returns:

        Raises:

        """
        if getattr(self, 'bin_provides_dicts', None) is None:
            self.bin_provides_dicts = dict()

        for bin_provides_item in self.get_provides():
            pkg_key = bin_provides_item.get('pkgKey')
            if pkg_key:
                if pkg_key not in self.bin_provides_dicts.keys():
                    self.bin_provides_dicts[pkg_key] = []
                self.bin_provides_dicts[pkg_key].append({
                    'name': bin_provides_item.get('name'),
                    'pkgKey': 0
                })

    def bin_file_merge(self, bin_package_key, db_file):
        """
        Description: Binary package related data integration
        Args:
            bin_package_key: Primary key of binary package
            db_file: Database file
        Returns:
            Key value after successful data combination
            (0, False) or (bin_package_key, True)
        Raises:
            SQLAlchemyError: An error occurred while executing the sql statement
        """
        self.__compose_bin_package()
        # binary package dependent package integration

        self.__compose_bin_requires()

        self.__compose_bin_provides()

        # integrate the id data of the binary package
        bin_requires_datas = []
        bin_provides_datas = []
        for bin_package_item in self.bin_package_datas:
            bin_package_key += 1
            # dependent packages
            requires = self.bin_requires_dicts.get(
                bin_package_item.get('pkgKey'))
            if requires:
                for bin_requires_item in requires:
                    bin_requires_item['pkgKey'] = bin_package_key
                    bin_requires_datas.append(bin_requires_item)

            provides = self.bin_provides_dicts.get(
                bin_package_item.get('pkgKey'))
            if provides:
                for bin_provides_item in provides:
                    bin_provides_item['pkgKey'] = bin_package_key
                    bin_provides_datas.append(bin_provides_item)
            bin_package_item['pkgKey'] = bin_package_key
        # save binary package related data
        try:
            with DBHelper(db_name=db_file, db_type=self.db_type) as data_base:
                data_base.batch_add(self.bin_package_datas, bin_package)
                data_base.batch_add(bin_requires_datas, bin_requiresment)
                data_base.batch_add(bin_provides_datas, bin_provides)
        except SQLAlchemyError as sql_error:
            LOGGER.logger.error(sql_error)
            return (0, False)
        else:
            return (bin_package_key, True)
