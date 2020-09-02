#!/usr/bin/python3
"""
Description:  A set for all query databases function
class: SearchDB
functions: db_priority
"""
from collections import namedtuple

import yaml
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy.sql import literal_column
from sqlalchemy import exists

from packageship.libs.dbutils import DBHelper
from packageship.libs.log import Log
from packageship.application.models.package import BinPack
from packageship.libs.exception import ContentNoneException, Error
from packageship.system_config import DATABASE_FILE_INFO
from .constants import ResponseCode

LOGGER = Log(__name__)


class SearchDB():
    """
    Description: query in database
    Attributes:
        db_list: Database list
        db_object_dict:A dictionary for storing database connection objects
    changeLog:
    """

    def __new__(cls, *args, **kwargs):
        # pylint: disable=w0613
        if not hasattr(cls, "_instance"):
            cls._instance = super(SearchDB, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_list):
        """
        init class
        """
        self.db_object_dict = dict()
        for db_name in db_list:
            try:
                with DBHelper(db_name=db_name) as data_base:
                    self.db_object_dict[db_name] = data_base
            except DisconnectionError as connection_error:
                current_app.logger.error(connection_error)

    def get_install_depend(self, binary_list):
        """
        Description: get a package install depend from database:
                     binary_name -> binary_id -> requires_set -> requires_id_set -> provides_set
                     -> install_depend_binary_id_key_list -> install_depend_binary_name_list
        Args:
             binary_list: a list of binary package name
        Returns:
             install depend list
        Raises:
        """
        result_list = []
        get_list = []
        provides_not_found = dict()
        if not self.db_object_dict:
            LOGGER.logger.warning("Unable to connect to the database, \
                check the database configuration")
            return result_list
        if None in binary_list:
            binary_list.remove(None)
        search_set = set(binary_list)
        if not search_set:
            LOGGER.logger.warning(
                "The input is None, please check the input value.")
            return result_list
        return_tuple = namedtuple('return_tuple',
                                  'depend_name depend_version depend_src_name \
                                      search_name search_src_name search_version')
        for db_name, data_base in self.db_object_dict.items():
            try:
                name_in = literal_column('name').in_(search_set)
                sql_com = text("""
                SELECT DISTINCT
                    bin_pack.NAME AS depend_name,
                    bin_pack.version AS depend_version,
                    bin_pack.src_name AS depend_src_name,
                    bin_requires.NAME AS req_name,
                    bin.NAME AS search_name,
                    bin.src_name AS search_src_name,
                    bin.version AS search_version 
                FROM
                    ( SELECT pkgKey,NAME,version,src_name FROM bin_pack WHERE {} ) bin
                    LEFT JOIN bin_requires ON bin.pkgKey = bin_requires.pkgKey
                    LEFT JOIN bin_provides ON bin_provides.name = bin_requires.name
                    LEFT JOIN bin_pack ON bin_pack.pkgKey = bin_provides.pkgKey;
                """.format(name_in))
                install_set = data_base.session. \
                    execute(sql_com, {'name_{}'.format(i): v
                                      for i, v in enumerate(search_set, 1)}).fetchall()
                if install_set:
                    # find search_name in db_name
                    # depend_name's db_name will be found in next loop
                    for result in install_set:
                        get_list.append(result.search_name)
                        if not result.depend_name and result.req_name:
                            if result.req_name in provides_not_found:
                                provides_not_found[result.req_name].append(
                                    [result.search_name, result.search_src_name, result.search_version, db_name])
                            else:
                                provides_not_found[result.req_name] = [
                                    [result.search_name, result.search_src_name, result.search_version, db_name]]
                        else:
                            obj = return_tuple(
                                result.depend_name,
                                result.depend_src_name,
                                result.depend_version,
                                result.search_name,
                                result.search_src_name,
                                result.search_version,
                            )
                            result_list.append((obj, db_name))
                    get_set = set(get_list)
                    get_list.clear()
                    search_set.symmetric_difference_update(get_set)
                    if not search_set:
                        install_result = self._get_install_pro_in_other_database(
                            provides_not_found)
                        result_list.extend(install_result)
                        return result_list, set(provides_not_found.keys())
                else:
                    continue
            except AttributeError as error_msg:
                LOGGER.logger.error(error_msg)
            except SQLAlchemyError as error_msg:
                LOGGER.logger.error(error_msg)
        install_result = self._get_install_pro_in_other_database(
            provides_not_found)
        result_list.extend(install_result)
        for binary_name in search_set:
            result_list.append((return_tuple(None, None, None,
                                             binary_name, None, None), 'NOT FOUND'))
        return result_list, set(provides_not_found.keys())

    def get_src_name(self, binary_name):
        """
        Description: get a package source name from database:
                     bianry_name ->binary_source_name -> source_name
        Args:
            binary_name: search package's name, database preority list
        Returns:
             db_name: database name
             source_name: source name
             source_version: source version
        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        for db_name, data_base in self.db_object_dict.items():
            try:
                bin_obj = data_base.session.query(BinPack).filter_by(
                    name=binary_name
                ).first()
                source_name = bin_obj.src_name
                source_version = bin_obj.version
                if source_name is not None:
                    return ResponseCode.SUCCESS, db_name, \
                        source_name, source_version
            except AttributeError as error_msg:
                LOGGER.logger.error(error_msg)
            except SQLAlchemyError as error_msg:
                LOGGER.logger.error(error_msg)
                return ResponseCode.DIS_CONNECTION_DB, None
        return ResponseCode.PACK_NAME_NOT_FOUND, None, None, None

    def get_sub_pack(self, source_name_list):
        """
        Description: get a subpack list based on source name list:
                     source_name ->source_name_id -> binary_name
        Args:
             source_name_list: search package's name, database preority list
        Returns:
             result_list: subpack tuple
        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        if not self.db_object_dict:
            return ResponseCode.DIS_CONNECTION_DB, None
        search_set = set([
            source_name for source_name in source_name_list if source_name])
        result_list = []
        get_list = []
        if not search_set:
            return ResponseCode.INPUT_NONE, None
        for db_name, data_base in self.db_object_dict.items():
            try:
                name_in = literal_column('name').in_(search_set)
                sql_com = text('''
                            SELECT
                                bin_pack.name AS subpack_name,
                                src.name AS search_name,
                                src.version AS search_version
                            FROM
                                (SELECT name,version FROM src_pack WHERE {}) src
                                LEFT JOIN bin_pack on src.name = bin_pack.src_name'''.format(name_in))
                subpack_tuple = data_base.session. \
                    execute(sql_com, {'name_{}'.format(i): v
                                      for i, v in enumerate(search_set, 1)}).fetchall()
                if subpack_tuple:
                    for result in subpack_tuple:
                        result_list.append((result, db_name))
                        get_list.append(result.search_name)
                    search_set.symmetric_difference_update(set(get_list))
                    get_list.clear()
                    if not search_set:
                        return ResponseCode.SUCCESS, result_list
                else:
                    continue
            except AttributeError as attr_error:
                current_app.logger.error(attr_error)
            except SQLAlchemyError as sql_error:
                current_app.logger.error(sql_error)
        return_tuple = namedtuple(
            'return_tuple', 'subpack_name search_version search_name')
        for search_name in search_set:
            # LOGGER.logger.warning("Can't not find " +
            #                       search_name + " subpack in all database")
            result_list.append(
                (return_tuple(None, None, search_name), 'NOT_FOUND'))
        return ResponseCode.SUCCESS, result_list

    def _get_binary_in_other_database(self, not_found_binary):
        """
        Description: Binary package name data not found in
        the current database, go to other databases to try
        Args:
            not_found_binary: not_found_build These data cannot be found in the current database
            db_:current database name
        Returns:
            a list :[(search_name,source_name,bin_name,
                            bin_version,db_name,search_version,req_name),
                        (search_name,source_name,bin_name,
                            bin_version,db_name,search_version,req_name),]
        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        if not not_found_binary:
            return []

        return_tuple = namedtuple("return_tuple", [
            "search_name",
            "source_name",
            "bin_name",
            "version",
            "db_name",
            "search_version",
        ])
        search_list = []
        result_list = []
        for db_name, data_base in self.db_object_dict.items():
            for key, _ in not_found_binary.items():
                search_list.append(key)

            search_set = set(search_list)
            search_list.clear()
            try:
                sql_string = text("""
                        SELECT DISTINCT
                        t1.src_name AS source_name,
                        t1.NAME AS bin_name,
                        t1.version,
                        t2.NAME AS req_name 
                    FROM
                        bin_pack t1,
                        bin_provides t2
                    WHERE
                        t2.{}
                        AND t1.pkgKey = t2.pkgKey;
                    """.format(literal_column('name').in_(search_set)))
                bin_set = data_base.session. \
                    execute(sql_string, {'name_{}'.format(i): v
                                         for i, v in enumerate(search_set, 1)}).fetchall()
                if bin_set:
                    for result in bin_set:
                        if result.req_name not in not_found_binary:
                            LOGGER.logger.warning(
                                result.req_name + " contains in two rpm packages!!!")
                        else:
                            for source_info in not_found_binary[result.req_name]:
                                obj = return_tuple(
                                    source_info[0],
                                    result.source_name,
                                    result.bin_name,
                                    result.version,
                                    db_name,
                                    source_info[1]
                                )
                                result_list.append(obj)
                            del not_found_binary[result.req_name]
                    if not not_found_binary:
                        return result_list
            except AttributeError as attr_err:
                current_app.logger.error(attr_err)
            except SQLAlchemyError as sql_err:
                current_app.logger.error(sql_err)

        if not_found_binary:
            for key, values in not_found_binary.items():
                # LOGGER.logger.warning(
                #     "CANNOT FOUND THE component" + key + " in all database")
                for info in values:
                    obj = return_tuple(
                        info[0],
                        None,
                        None,
                        None,
                        'NOT FOUND',
                        info[2]
                    )
                    result_list.append(obj)
        return result_list

    def _get_install_pro_in_other_database(self, not_found_binary):
        if not not_found_binary:
            return []
        return_tuple = namedtuple('return_tuple',
                                  'depend_name depend_version depend_src_name \
                                      search_name search_src_name search_version')
        search_list = []
        result_list = []
        for db_name, data_base in self.db_object_dict.items():
            for key, values in not_found_binary.items():
                search_list.append(key)
            search_set = set(search_list)
            search_list.clear()
            sql_string = text("""
                    SELECT DISTINCT
                    t1.src_name AS source_name,
                    t1.NAME AS bin_name,
                    t1.version,
                    t2.NAME AS req_name 
                FROM
                    bin_pack t1,
                    bin_provides t2
                WHERE
                    t2.{}
                    AND t1.pkgKey = t2.pkgKey;
                """.format(literal_column('name').in_(search_set)))
            bin_set = data_base.session. \
                execute(sql_string, {'name_{}'.format(i): v
                                     for i, v in enumerate(search_set, 1)}).fetchall()
            if bin_set:
                for result in bin_set:
                    if result.req_name not in not_found_binary:
                        LOGGER.logger.warning(
                            result.req_name + " contains in two rpm packages!!!")
                    else:
                        for binary_info in not_found_binary[result.req_name]:
                            obj = return_tuple(
                                result.bin_name,
                                result.version,
                                result.source_name,
                                binary_info[0],
                                binary_info[1],
                                binary_info[2]
                            )
                            result_list.append((obj, binary_info[3]))
                        del not_found_binary[result.req_name]
                if not not_found_binary:
                    return result_list
        if not_found_binary:
            # for key, values in not_found_binary.items():
            # LOGGER.logger.warning("CANNOT FOUND THE component" + key + " in all database")
            for key, values in not_found_binary.items():
                for info in values:
                    obj = return_tuple(
                        None,
                        None,
                        None,
                        info[0],
                        info[1],
                        info[2]
                    )
                    result_list.append((obj, info[3]))
        return result_list

    def get_build_depend(self, source_name_li):
        """
        Description: get a package build depend from database
        Args:
            source_name_li: search package's name list
        Returns:
             all source pkg build depend list
             structure :[(search_name,source_name,bin_name,bin_version,db_name,search_version),
                            (search_name,source_name,bin_name,bin_version,db_name,search_version),]

        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        # pylint: disable=R0914
        return_tuple = namedtuple("return_tuple", [
            "search_name",
            "source_name",
            "bin_name",
            "version",
            "db_name",
            "search_version"
        ])

        s_name_set = set(source_name_li)
        if not s_name_set:
            return ResponseCode.PARAM_ERROR, set()

        provides_not_found = dict()
        build_list = []

        for db_name, data_base in self.db_object_dict.items():

            build_set = []
            try:
                temp_list = list(s_name_set)
                for input_name_li in [temp_list[i:i + 900] for i in range(0, len(temp_list), 900)]:
                    sql_com = text("""
                        SELECT DISTINCT
                        src.NAME AS search_name,
                        src.version AS search_version,
                        bin_pack.src_name AS source_name,
                        bin_provides.pkgKey AS bin_id,
                        src_requires.NAME AS req_name,
                        bin_pack.version AS version,
                        bin_pack.NAME AS bin_name
                    FROM
                        ( SELECT pkgKey, NAME, version FROM src_pack WHERE {} ) src
                        LEFT JOIN src_requires ON src.pkgKey = src_requires.pkgKey
                        LEFT JOIN bin_provides ON bin_provides.NAME = src_requires.NAME
                        LEFT JOIN bin_pack ON bin_pack.pkgKey = bin_provides.pkgKey;
                    """.format(literal_column("name").in_(input_name_li)))
                    res = data_base.session.execute(
                        sql_com,
                        {'name_{}'.format(i): v
                         for i, v in enumerate(input_name_li, 1)}
                    ).fetchall()

                    build_set.extend(res)
            except AttributeError as attr_err:
                current_app.logger.error(attr_err)
            except SQLAlchemyError as sql_err:
                current_app.logger.error(sql_err)

            if not build_set:
                continue

            # When processing source package without compilation dependency
            get_list = []
            for result in build_set:
                get_list.append(result.search_name)
                if not result.bin_name and result.req_name:
                    if result.req_name in provides_not_found:
                        provides_not_found[result.req_name].append(
                            [result.search_name, result.search_version, db_name]
                        )
                    else:
                        provides_not_found[result.req_name] = [
                            [result.search_name, result.search_version, db_name]
                        ]
                else:
                    obj = return_tuple(
                        result.search_name,
                        result.source_name,
                        result.bin_name,
                        result.version,
                        db_name,
                        result.search_version
                    )
                    build_list.append(obj)

            get_set = set(get_list)
            get_list.clear()
            s_name_set.symmetric_difference_update(get_set)
            if not s_name_set:
                build_result = self._get_binary_in_other_database(
                    provides_not_found)
                build_list.extend(build_result)
                return ResponseCode.SUCCESS, build_list, set(provides_not_found.keys())

        if s_name_set:
            build_result = self._get_binary_in_other_database(
                provides_not_found)
            build_list.extend(build_result)
            for source in s_name_set:
                LOGGER.logger.warning(
                    "CANNOT FOUND THE source " + source + " in all database")
        return ResponseCode.SUCCESS, build_list, set(provides_not_found.keys())

    def binary_search_database_for_first_time(self, binary_name):
        """
         Args:
             binary_name: a binary package name

         Returns:
             The name of the first database
             in which the binary package appears according to priority
             If it does not exist or exception occurred , return 'NOT FOUND'

         """
        try:
            for db_name, data_base in self.db_object_dict.items():
                if data_base.session.query(
                        exists().where(BinPack.name == binary_name)
                ).scalar():
                    return db_name
        except AttributeError as attr_err:
            current_app.logger.error(attr_err)
        except SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)

        return 'NOT FOUND'


def db_priority():
    """
    Description: Read yaml file, return database name, according to priority
    Args:
    Returns:
        db_list: database name list
    Raises:
        FileNotFoundError: file cannot be found
        Error: abnormal error
    """
    try:
        with open(DATABASE_FILE_INFO, 'r', encoding='utf-8') as file_context:

            init_database_date = yaml.load(
                file_context.read(), Loader=yaml.FullLoader)
            if init_database_date is None:
                raise ContentNoneException(
                    "The content of the database initialization configuration file cannot be empty")
            init_database_date.sort(key=lambda x: x['priority'], reverse=False)
            db_list = [item.get('database_name')
                       for item in init_database_date]
            return db_list
    except (FileNotFoundError, Error) as file_not_found:
        current_app.logger.error(file_not_found)
        return None
