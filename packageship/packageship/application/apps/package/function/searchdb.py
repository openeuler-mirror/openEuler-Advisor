"""
    A set for all query databases function
"""
from collections import namedtuple

import yaml
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy.sql import literal_column

from packageship.libs.dbutils import DBHelper
from packageship.libs.log import Log
from packageship.application.models.package import bin_pack
from packageship.libs.exception import ContentNoneException, Error
from packageship.system_config import DATABASE_FILE_INFO
from .constants import ResponseCode

LOGGER = Log(__name__)


class SearchDB():
    """
    Description: query in database
    changeLog:
    """
    def __new__(cls, *args, **kwargs):
        # pylint: disable=w0613
        if not hasattr(cls, "_instance"):
            cls._instance = super(SearchDB, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_list):
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
        :param binary_lsit: a list of binary package name
        :return install depend list
        changeLog:
        """
        result_list = []
        get_list = []
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
        for db_name, data_base in self.db_object_dict.items():
            try:
                name_in = literal_column('name').in_(search_set)
                sql_com = text("""
                SELECT DISTINCT
                bin_pack.NAME AS depend_name,
                bin_pack.version AS depend_version,
                s2.NAME AS depend_src_name,
                bin.NAME AS search_name,
                s1.`name` AS search_src_name,
                s1.version AS search_version
                FROM
                ( SELECT id, NAME,srcIDkey FROM bin_pack WHERE {} ) bin
                LEFT JOIN pack_requires ON bin.id = pack_requires.binIDkey
                LEFT JOIN pack_provides ON pack_provides.id = pack_requires.depProIDkey
                LEFT JOIN bin_pack ON bin_pack.id = pack_provides.binIDkey
                LEFT JOIN src_pack s1 ON s1.id = bin.srcIDkey
                LEFT JOIN src_pack s2 ON s2.id = bin_pack.srcIDkey;""".format(name_in))
                install_set = data_base.session. \
                    execute(sql_com, {'name_{}'.format(i): v
                                      for i, v in enumerate(search_set, 1)}).fetchall()
                if install_set:
                    # find search_name in db_name
                    # depend_name's db_name will be found in next loop
                    for result in install_set:
                        result_list.append((result, db_name))
                        get_list.append(result.search_name)
                    get_set = set(get_list)
                    get_list.clear()
                    search_set.symmetric_difference_update(get_set)
                    if not search_set:
                        return result_list
                else:
                    continue
            except AttributeError as error_msg:
                LOGGER.logger.error(error_msg)
            except SQLAlchemyError as error_msg:
                LOGGER.logger.error(error_msg)
        return_tuple = namedtuple('return_tuple',
                                  'depend_name depend_version depend_src_name \
                                      search_name search_src_name search_version')
        for binary_name in search_set:
            result_list.append((return_tuple(None, None, None,
                                             binary_name, None, None), 'NOT FOUND'))
        return result_list

    def get_src_name(self, binary_name):
        """
        Description: get a package source name from database:
                     bianry_name ->binary_source_name -> source_name
        input: search package's name, database preority list
        return: database name, source name
        changeLog:
        """
        for db_name, data_base in self.db_object_dict.items():
            try:
                bin_obj = data_base.session.query(bin_pack).filter_by(
                    name=binary_name
                ).first()
                source_name = bin_obj.src_pack.name
                source_version = bin_obj.src_pack.version
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
        input: search package's name, database preority list
        return: subpack tuple
        changeLog:
        """
        if not self.db_object_dict:
            return ResponseCode.DIS_CONNECTION_DB, None

        if None in source_name_list:
            source_name_list.remove(None)
        search_set = set(source_name_list)
        result_list = []
        get_list = []
        if not search_set:
            return ResponseCode.INPUT_NONE, None
        for db_name, data_base in self.db_object_dict.items():
            try:
                name_in = literal_column('name').in_(search_set)
                sql_com = text('''SELECT
                                t1.NAME as subpack_name,
                                t2.version as search_version,
                                t2.NAME as search_name
                                FROM bin_pack t1, src_pack t2 
                                WHERE
                                t2.id = t1.srcIDkey 
                                AND t2.{}
                                '''.format(name_in))
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
            LOGGER.logger.warning("Can't not find " +
                                  search_name + " subpack in all database")
            result_list.append(
                (return_tuple(None, None, search_name), 'NOT_FOUND'))
        return ResponseCode.SUCCESS, result_list

    def get_binary_in_other_database(self, not_found_binary, db_):
        """
        Binary package name data not found in the current database, go to other databases to try
        @:param:not_found_build These data cannot be found in the current database
        @:param:db:current database name
        return:a list :[(search_name,source_name,bin_name,
                            bin_version,db_name,search_version,req_name),
                        (search_name,source_name,bin_name,
                            bin_version,db_name,search_version,req_name),]
        changeLog:new method to look for data in other databases
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
            "req_name"
        ])
        src_req_map = {req_: src for src, req_ in not_found_binary}

        local_search_set = {req_ for _, req_ in not_found_binary}

        local_dict = {k: v for k, v in self.db_object_dict.items() if k != db_}
        res = []

        for db_name, data_base in local_dict.items():
            try:
                sql_string = text("""
                     SELECT
                         t3.NAME AS source_name,
                         t1.NAME AS bin_name,
                         t1.version,
                         t3.version as search_version,
                         t2.NAME AS req_name
                     FROM
                         bin_pack t1,
                         pack_provides t2,
                         src_pack t3
                     WHERE
                         t2.{}
                         AND t1.id = t2.binIDkey
                         AND t1.srcIDkey = t3.id;
                 """.format(literal_column('name').in_(local_search_set)))
                build_set_2 = data_base.session. \
                    execute(sql_string, {'name_{}'.format(i): v
                                         for i, v in enumerate(local_search_set, 1)}).fetchall()
                if not build_set_2:
                    continue

                res.extend([return_tuple(
                    src_req_map.get(bin_pack.req_name),
                    bin_pack.source_name,
                    bin_pack.bin_name,
                    bin_pack.version,
                    db_name,
                    bin_pack.search_version,
                    bin_pack.req_name
                ) for bin_pack in build_set_2 if bin_pack.bin_name])

                for obj in res:
                    local_search_set.remove(obj.req_name)

            except AttributeError as attr_error:
                current_app.logger.error(attr_error)
            except SQLAlchemyError as sql_error:
                current_app.logger.error(sql_error)
        return res

    def get_build_depend(self, source_name_li):
        """
        Description: get a package build depend from database
        input:
        @:param: search package's name list
        return: all source pkg build depend list
                structure :[(search_name,source_name,bin_name,bin_version,db_name,search_version),
                            (search_name,source_name,bin_name,bin_version,db_name,search_version),]

        changeLog: Modify SQL logic and modify return content by:zhangtao
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
            return ResponseCode.PARAM_ERROR, None

        not_found_binary = set()
        build_list = []

        for db_name, data_base in self.db_object_dict.items():
            try:
                sql_com = text("""SELECT DISTINCT
                     src.NAME AS search_name,
                     src.version AS search_version,
                     s2.NAME AS source_name,
                     pack_provides.binIDkey AS bin_id,
                     pack_requires.NAME AS req_name,
                     bin_pack.version AS version,
                     bin_pack.NAME AS bin_name
                 FROM
                      ( SELECT id, NAME,version FROM src_pack WHERE {} ) src
                      LEFT JOIN pack_requires ON src.id = pack_requires.srcIDkey
                      LEFT JOIN pack_provides ON pack_provides.id = pack_requires.depProIDkey
                      LEFT JOIN bin_pack ON bin_pack.id = pack_provides.binIDkey
                      LEFT JOIN src_pack s1 ON s1.id = pack_requires.srcIDkey
                      LEFT JOIN src_pack s2 ON bin_pack.srcIDkey = s2.id;
                """.format(literal_column("name").in_(s_name_set)))

                build_set = data_base.session. \
                    execute(sql_com, {'name_{}'.format(i): v
                                      for i, v in enumerate(s_name_set, 1)}).fetchall()

                if not build_set:
                    continue

                # When processing source package without compilation dependency
                to_remove_obj_index = []
                for index, b_pack in enumerate(build_set):
                    if not b_pack.source_name and not b_pack.req_name:
                        obj = return_tuple(
                            b_pack.search_name,
                            b_pack.source_name,
                            b_pack.bin_name,
                            b_pack.version,
                            db_name,
                            b_pack.search_version
                        )

                        build_list.append(obj)
                        to_remove_obj_index.append(index)

                for i in reversed(to_remove_obj_index):
                    build_set.pop(i)

                if not build_set:
                    continue

                build_list.extend([
                    return_tuple(
                        bin_pack.search_name,
                        bin_pack.source_name,
                        bin_pack.bin_name,
                        bin_pack.version,
                        db_name,
                        bin_pack.search_version
                    ) for bin_pack in build_set if bin_pack.bin_id and bin_pack.bin_name
                ])
                # Component name can't find its binary package name
                not_found_binary.update([(bin_pack.search_name, bin_pack.req_name)
                                         for bin_pack in build_set if not bin_pack.bin_id])

                s_name_set -= {bin_pack.search_name for bin_pack in build_set
                               if bin_pack.bin_id}

                if not not_found_binary and not s_name_set:
                    return ResponseCode.SUCCESS, build_list

                for obj in self.get_binary_in_other_database(not_found_binary, db_name):
                    build_list.append(obj)

                not_found_binary.clear()

            except AttributeError as attr_error:
                current_app.logger.error(attr_error)
            except SQLAlchemyError as sql_error:
                current_app.logger.error(sql_error)
                return ResponseCode.DIS_CONNECTION_DB, None
        return ResponseCode.SUCCESS, build_list


def db_priority():
    """
    return dbprioty
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
