#!/usr/bin/python3
"""
Description:  A set for all query databases function
class: SearchDB
functions: db_priority
"""
from collections import namedtuple, Counter

import yaml
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy.sql import literal_column
from sqlalchemy import exists

from packageship.libs.dbutils import DBHelper
from packageship.libs.log import Log
from packageship.application.models.package import BinPack
from packageship.application.models.package import SrcPack
from packageship.application.models.package import DatabaseInfo
from packageship.application.apps.package.function.constants import ResponseCode

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

    # Related methods of install
    # pylint: disable=R0914
    def get_install_depend(self, binary_list, pk_value=None):
        """
        Description: get a package install depend from database:
                     binary_name -> binary_id -> requires_set -> requires_id_set -> provides_set
                     -> install_depend_binary_id_key_list -> install_depend_binary_name_list
        Args:
             binary_list: a list of binary package name
             pk_value:List of pkgKey found
        Returns:
             list:install depend list
             set:package not found components,
             pk_val:The pkgkey corresponding to the required components
        Raises:
        """
        pk_val = pk_value if pk_value else []
        result_list = []
        provides_not_found = dict()

        if not self.db_object_dict:
            LOGGER.logger.warning("Unable to connect to the database,"
                                  "check the database configuration")
            return result_list, set(), pk_val

        if None in binary_list:
            binary_list.remove(None)
        search_set = set(binary_list)

        if not search_set:
            LOGGER.logger.warning("The input is None, please check the input value.")
            return result_list, set(), pk_val

        return_tuple = namedtuple('return_tuple', [
            'depend_name',
            'depend_version',
            'depend_src_name',
            'search_name',
            'search_src_name',
            'search_version'
        ])

        for db_name, data_base in self.db_object_dict.items():
            try:
                req_set = self._get_requires(search_set, data_base, _tp='install')

                if not req_set:
                    continue

                (depend_set,
                 req_pk_dict,
                 pk_v,
                 not_fd_com) = self._get_provides_req_info(req_set,
                                                           data_base,
                                                           pk_val)
                pk_val += pk_v
                res_list, get_list = self._comb_install_list(depend_set,
                                                             req_pk_dict,
                                                             not_fd_com,
                                                             return_tuple,
                                                             db_name,
                                                             provides_not_found,
                                                             req_set)

                result_list += res_list

                search_set.symmetric_difference_update(set(get_list))

                if not search_set:
                    result_list.extend(
                        self._get_install_pro_in_other_database(provides_not_found,
                                                                db_name)
                    )
                    return result_list, set(provides_not_found.keys()), pk_val

            except AttributeError as error_msg:
                LOGGER.logger.error(error_msg)
            except SQLAlchemyError as error_msg:
                LOGGER.logger.error(error_msg)
        if search_set:
            result_list.extend(
                self._get_install_pro_in_other_database(provides_not_found)
            )

            for binary_name in search_set:
                result_list.append((return_tuple(None, None, None,
                                                 binary_name, None, None), 'NOT FOUND'))
        return result_list, set(provides_not_found.keys()), pk_val

    # pylint: disable=R0913
    @staticmethod
    def _comb_install_list(depend_set,
                           req_pk_dict,
                           not_fd_com,
                           return_tuple,
                           db_name,
                           provides_not_found,
                           req_set):
        """
        Description: Query the corresponding installation dependency list
                    through the components of the requirements
        Args:
             depend_set: List binary package information corresponding to the components
             req_pk_dict:Mapping of components and binary pkgKey
             not_fd_com: List of pkgKey found,
             return_tuple: Named tuple format for saving information
             db_name:current database name
             provides_not_found:Component mapping not found in the current database
             req_set:Package information and corresponding component information
        Returns:
             ret_list:install depend list
             get_list:Packages that have found results
        Raises:
        """
        get_list = []
        ret_list = []
        depend_info_tuple = namedtuple('depend_info', [
            'depend_name',
            'depend_version',
            'depend_src_name'
        ])
        depend_info_dict = {
            info.pk: depend_info_tuple(info.depend_name,
                                       info.depend_version,
                                       info.depend_src_name)
            for info in depend_set
        }

        for req_name, search_name, search_src_name, search_version in req_set:
            get_list.append(search_name)

            if not req_name:
                obj = return_tuple(
                    None,
                    None,
                    None,
                    search_name,
                    search_src_name,
                    search_version,
                )
                ret_list.append((obj, db_name))

            elif req_name in req_pk_dict:
                depend_info_t = depend_info_dict.get(req_pk_dict[req_name])
                obj = return_tuple(
                    depend_info_t.depend_name,
                    depend_info_t.depend_version,
                    depend_info_t.depend_src_name,
                    search_name,
                    search_src_name,
                    search_version,
                )
                ret_list.append((obj, db_name))

            else:
                if req_name in not_fd_com:
                    if req_name not in provides_not_found:
                        provides_not_found[req_name] = [[search_name, search_src_name,
                                                         search_version, db_name]]
                    else:
                        provides_not_found[req_name].append([search_name, search_src_name,
                                                             search_version, db_name])

        return ret_list, get_list

    def _get_install_pro_in_other_database(self, not_found_binary, _db_name=None):
        """
        Description: Binary package name data not found in
        the current database, go to other databases to try
        Args:
            not_found_binary: not_found_build These data cannot be found in the current database
            _db_name:current database name
        Returns:
           result_list :[return_tuple1,return_tuple2] package information
        Raises:
        """
        if not not_found_binary:
            return []

        return_tuple = namedtuple('return_tuple', [
            'depend_name',
            'depend_version',
            'depend_src_name',
            'search_name',
            'search_src_name',
            'search_version'
        ])

        result_list = []
        search_set = {k for k, _ in not_found_binary.items()}

        for db_name, data_base in self.db_object_dict.items():
            if db_name == _db_name:
                continue

            parm_tuple = namedtuple("in_tuple", 'req_name')
            in_tuple_list = [parm_tuple(k) for k, _ in not_found_binary.items()]

            depend_set, req_pk_dict, *_ = self._get_provides_req_info(
                in_tuple_list,
                data_base
            )

            depend_info_tuple = namedtuple('depend_info', [
                'depend_name',
                'depend_version',
                'depend_src_name'
            ])
            depend_info_dict = {
                info.pk: depend_info_tuple(info.depend_name,
                                           info.depend_version,
                                           info.depend_src_name)
                for info in depend_set
            }
            result_list += self._comb_install_info(search_set,
                                                   req_pk_dict,
                                                   depend_info_dict,
                                                   not_found_binary,
                                                   return_tuple,
                                                   db_name)
            if not not_found_binary:
                return result_list

        if not_found_binary:
            for _, values in not_found_binary.items():
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

    @staticmethod
    def _comb_install_info(search_set,
                           req_pk_dict,
                           depend_info_dict,
                           not_found_binary,
                           return_tuple,
                           db_name):
        """
        Description: Binary package name data not found in
        the current database, go to other databases to try
        Args:
            search_set: The name of the component to be queried
            req_pk_dict:Mapping of components and binary pkgKey
            depend_info_dict:The mapping of binary pkgKey and binary information
            not_found_binary:not_found_build These data cannot be found in the current database
            return_tuple:Named tuple format for saving information
            db_name:current database name
        Returns:
           ret_list :[return_tuple1,return_tuple2] package information
        Raises:
        """
        ret_list = []
        for req_name in search_set:
            if req_name in req_pk_dict:
                pk_ = req_pk_dict[req_name]
                if pk_ in depend_info_dict:
                    for binary_info in not_found_binary[req_name]:
                        obj = return_tuple(
                            depend_info_dict[pk_].depend_name,
                            depend_info_dict[pk_].depend_version,
                            depend_info_dict[pk_].depend_src_name,
                            binary_info[0],
                            binary_info[1],
                            binary_info[2]
                        )
                        ret_list.append((obj, db_name))
                    del not_found_binary[req_name]
        return ret_list

    # Related methods of build
    def get_build_depend(self, source_name_li, pk_value=None):
        """
        Description: get a package build depend from database
        Args:
            source_name_li: search package's name list
            pk_value:List of pkgKey found
        Returns:
             all source pkg build depend list
             structure :[(search_name,source_name,bin_name,bin_version,db_name,search_version),
                            (search_name,source_name,bin_name,bin_version,db_name,search_version),]
             set: package not found components name set
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
        pk_val = pk_value if pk_value else []
        s_name_set = set(source_name_li)
        if not s_name_set:
            return ResponseCode.PARAM_ERROR, list(), set(), pk_val

        provides_not_found = dict()
        build_list = []

        for db_name, data_base in self.db_object_dict.items():

            try:
                req_set = self._get_requires(s_name_set, data_base, _tp='build')

                if not req_set:
                    continue

                (depend_set,
                 req_pk_dict,
                 pk_v,
                 not_fd_req) = self._get_provides_req_info(req_set, data_base)

                pk_val += pk_v
                ret_list, get_list = self._comb_build_list(depend_set,
                                                           req_pk_dict,
                                                           not_fd_req,
                                                           return_tuple,
                                                           db_name,
                                                           provides_not_found,
                                                           req_set)
                build_list += ret_list
                s_name_set.symmetric_difference_update(set(get_list))
                if not s_name_set:
                    build_list.extend(
                        self._get_binary_in_other_database(provides_not_found, _db_name=db_name)
                    )
                    return ResponseCode.SUCCESS, build_list, set(provides_not_found.keys()), pk_val

            except AttributeError as attr_err:
                current_app.logger.error(attr_err)
            except SQLAlchemyError as sql_err:
                current_app.logger.error(sql_err)

        if s_name_set:
            build_list.extend(
                self._get_binary_in_other_database(provides_not_found)
            )
            for source in s_name_set:
                LOGGER.logger.warning(
                    "CANNOT FOUND THE SOURCE %s in all database", source)

        return ResponseCode.SUCCESS, build_list, set(provides_not_found.keys()), pk_val

    @staticmethod
    def _comb_build_list(depend_set,
                         req_pk_dict,
                         not_fd_com,
                         return_tuple,
                         db_name,
                         provides_not_found,
                         req_set):
        """
        Description: Query the corresponding build dependency list
                    through the components of the requirements
        Args:
             depend_set: List binary package information corresponding to the components
             req_pk_dict:Mapping of components and binary pkgKey
             not_fd_com: List of pkgKey found,
             return_tuple: Named tuple format for saving information
             db_name:current database name
             provides_not_found:Component mapping not found in the current database
             req_set:Package information and corresponding component information
        Returns:
             ret_list:install depend list
             get_list:Packages that have found results
        Raises:
        """
        get_list = []
        ret_list = []
        depend_info_tuple = namedtuple('depend_info', [
            'depend_name',
            'depend_version',
            'depend_src_name'
        ])
        depend_info_dict = {
            info.pk: depend_info_tuple(info.depend_name,
                                       info.depend_version,
                                       info.depend_src_name)
            for info in depend_set
        }

        for req_name, search_name, search_version in req_set:

            get_list.append(search_name)

            if not req_name:
                obj = return_tuple(
                    search_name,
                    None,
                    None,
                    None,
                    db_name,
                    search_version,
                )
                ret_list.append(obj)

            elif req_name in req_pk_dict:
                depend_info_t = depend_info_dict.get(req_pk_dict[req_name])
                obj = return_tuple(
                    search_name,
                    depend_info_t.depend_src_name,
                    depend_info_t.depend_name,
                    depend_info_t.depend_version,
                    db_name,
                    search_version
                )
                ret_list.append(obj)

            else:
                if req_name in not_fd_com:
                    if req_name not in provides_not_found:
                        provides_not_found[req_name] = [
                            [search_name,
                             search_version,
                             db_name]
                        ]
                    else:
                        provides_not_found[req_name].append([search_name,
                                                             search_version,
                                                             db_name])

        return ret_list, get_list

    def _get_binary_in_other_database(self, not_found_binary, _db_name=None):
        """
        Description: Binary package name data not found in
        the current database, go to other databases to try
        Args:
            not_found_binary: not_found_build These data cannot be found in the current database
            _db_name:current database name
        Returns:
            result_list :[return_tuple1,return_tuple2] package information
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

        result_list = []
        search_set = {k for k, _ in not_found_binary.items()}

        for db_name, data_base in self.db_object_dict.items():

            if db_name == _db_name:
                continue

            in_tuple = namedtuple("in_tuple", 'req_name')
            in_tuple_list = [in_tuple(k) for k, _ in not_found_binary.items()]

            depend_set, req_pk_dict, *_ = self._get_provides_req_info(
                in_tuple_list,
                data_base
            )

            depend_info_tuple = namedtuple('depend_info', [
                'depend_name',
                'depend_version',
                'depend_src_name'
            ])
            depend_info_dict = {
                info.pk: depend_info_tuple(info.depend_name,
                                           info.depend_version,
                                           info.depend_src_name)
                for info in depend_set
            }

            result_list += self._comb_build_info(search_set,
                                                 req_pk_dict,
                                                 depend_info_dict,
                                                 not_found_binary,
                                                 return_tuple,
                                                 db_name)
            if not not_found_binary:
                return result_list

        if not_found_binary:
            for _, values in not_found_binary.items():
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

    @staticmethod
    def _comb_build_info(search_set,
                         req_pk_dict,
                         depend_info_dict,
                         not_found_binary,
                         return_tuple,
                         db_name):
        """
        Description: Binary package name data not found in
        the current database, go to other databases to try
        Args:
            search_set: The name of the component to be queried
            req_pk_dict:Mapping of components and binary pkgKey
            depend_info_dict:The mapping of binary pkgKey and binary information
            not_found_binary:not_found_build These data cannot be found in the current database
            return_tuple:Named tuple format for saving information,
            db_name:current data base name
        Returns:
           ret_list :[return_tuple1,return_tuple2] package information
        Raises:
        """
        ret_list = []
        for req_name in search_set:
            if req_name in req_pk_dict:
                pk_ = req_pk_dict[req_name]
                if pk_ in depend_info_dict:
                    for binary_info in not_found_binary[req_name]:
                        obj = return_tuple(
                            binary_info[0],
                            depend_info_dict[pk_].depend_src_name,
                            depend_info_dict[pk_].depend_name,
                            depend_info_dict[pk_].depend_version,
                            db_name,
                            binary_info[1]
                        )
                        ret_list.append(obj)
                    del not_found_binary[req_name]
        return ret_list

    # Common methods for install and build
    @staticmethod
    def _get_requires(search_set, data_base, _tp=None):
        """
        Description: Query the dependent components of the current package
        Args:
            search_set: The package name to be queried
            data_base:current database object
            _tp:type options build or install
        Returns:
            req_set:List Package information and corresponding component information
        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        if _tp == 'build':
            sql_com = text("""
               SELECT DISTINCT
                    src_requires.NAME AS req_name,
                    src.NAME AS search_name,
                    src.version AS search_version 
               FROM
                    ( SELECT pkgKey, NAME, version, src_name FROM src_pack WHERE {} ) src
                    LEFT JOIN src_requires ON src.pkgKey = src_requires.pkgKey;
                    """.format(literal_column('name').in_(search_set)))
        elif _tp == 'install':
            sql_com = text("""
                SELECT DISTINCT
                    bin_requires.NAME AS req_name,
                    bin.NAME AS search_name,
                    s1.name as search_src_name,
                    bin.version AS search_version 
                FROM
                    ( SELECT pkgKey, NAME, version, rpm_sourcerpm FROM bin_pack WHERE {} ) bin
                    LEFT JOIN src_pack s1 ON bin.rpm_sourcerpm = s1.src_name
                    LEFT JOIN bin_requires ON bin.pkgKey = bin_requires.pkgKey;
                            """.format(literal_column('name').in_(search_set)))
        else:
            return []

        req_set = []
        try:
            req_set = data_base.session. \
                execute(sql_com, {'name_{}'.format(i): v
                                  for i, v in enumerate(search_set, 1)}).fetchall()
        except AttributeError as error_msg:
            LOGGER.logger.error(error_msg)
        except SQLAlchemyError as error_msg:
            LOGGER.logger.error(error_msg)
        return req_set

    def _get_provides_req_info(self, req_info, data_base, pk_value=None):
        """
        Description: Get the name of the binary package
                    that provides the dependent component,
                    Filter redundant queries
                    when the same binary package is provided to multiple components
        Args:
            req_info: List of sqlalchemy objects with component names.
            data_base: The database currently being queried
            pk_value:Binary pkgKey that has been found
        Returns:
             depend_set: List of related dependent sqlalchemy objects
             req_pk_dict: Mapping dictionary of component name and pkgKey
             pk_val:update Binary pkgKey that has been found
             not_fd_req: Components not found
        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        pk_val = pk_value if pk_value else []
        depend_set = []
        req_pk_dict = {}
        not_fd_req = set()
        try:
            req_names = {req_.req_name
                         for req_ in req_info
                         if req_.req_name is not None}
            req_name_in = literal_column('name').in_(req_names)

            sql_com_pro = text("""
                            SELECT DISTINCT 
                                NAME as req_name,
                                pkgKey 
                            FROM
                                ( SELECT name, pkgKey FROM bin_provides 
                                UNION ALL 
                                SELECT name, pkgKey FROM bin_files ) 
                            WHERE
                                {};
                            """.format(req_name_in))

            pkg_key_set = data_base.session.execute(
                sql_com_pro, {
                    'name_{}'.format(i): v
                    for i, v in enumerate(req_names, 1)
                }
            ).fetchall()

            req_pk_dict = dict()
            pk_v = list()

            for req_name, pk_ in pkg_key_set:
                if not req_name:
                    continue
                pk_v.append(pk_)
                if req_name not in req_pk_dict:
                    req_pk_dict[req_name] = [pk_]
                else:
                    req_pk_dict[req_name].append(pk_)

            pk_val += pk_v

            pk_count_dic = Counter(pk_val)

            for key, values in req_pk_dict.items():
                count_values = list(map(
                    lambda x: pk_count_dic[x] if x in pk_count_dic else 0, values
                ))
                max_index = count_values.index(max(count_values))
                req_pk_dict[key] = values[max_index]

            not_fd_req = req_names - set(req_pk_dict.keys())
            depend_set = self._get_depend_info(req_pk_dict, data_base)

        except SQLAlchemyError as sql_err:
            LOGGER.logger.error(sql_err)
        except AttributeError as error_msg:
            LOGGER.logger.error(error_msg)

        return depend_set, req_pk_dict, pk_val, not_fd_req

    @staticmethod
    def _get_depend_info(req_pk_dict, data_base):
        """
        Description: Obtain binary related information through binary pkgKey
        Args:
            req_pk_dict: Mapping dictionary of component name and pkgKey
            data_base: The database currently being queried
        Returns:
             depend_set: List of related dependent sqlalchemy objects
        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        depend_set = []
        try:
            bin_src_pkg_key = req_pk_dict.values()
            pk_in = literal_column('pkgKey').in_(bin_src_pkg_key)
            sql_bin_src = text("""
                    SELECT DISTINCT 
                        bin.pkgKey as pk,
                        bin.name AS depend_name,
                        bin.version AS depend_version,
                        src_pack.name AS depend_src_name 
                    FROM
                        ( SELECT name, pkgKey,version, rpm_sourcerpm FROM bin_pack WHERE {} ) bin
                        LEFT JOIN src_pack ON src_pack.src_name = bin.rpm_sourcerpm;
                    """.format(pk_in))

            depend_set = data_base.session.execute(
                sql_bin_src, {
                    'pkgKey_{}'.format(i): v
                    for i, v in enumerate(bin_src_pkg_key, 1)
                }
            ).fetchall()

        except SQLAlchemyError as sql_err:
            LOGGER.logger.error(sql_err)
        except AttributeError as error_msg:
            LOGGER.logger.error(error_msg)

        return depend_set

    # Other methods
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

    def get_version_and_db(self, src_name):
        """

        Args:
            src_name:the source package name
        Returns:
            this source package version and  db_name
        """
        try:
            for db_name, data_base in self.db_object_dict.items():
                res = data_base.session.query(SrcPack.version).filter_by(name=src_name).first()
                if res:
                    return db_name, res.version
        except AttributeError as attr_err:
            current_app.logger.error(attr_err)
        except SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)

        return None, None

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
            sql_str = """
             SELECT DISTINCT
                 src_pack.name AS source_name,
                 src_pack.version AS source_version 
             FROM
                 bin_pack,
                 src_pack 
             WHERE
                 src_pack.src_name = bin_pack.rpm_sourcerpm 
                 AND bin_pack.name = :binary_name;
             """
            try:
                bin_obj = data_base.session.execute(text(sql_str),
                                                    {"binary_name": binary_name}
                                                    ).fetchone()
                source_name = bin_obj.source_name
                source_version = bin_obj.source_version
                if source_name is not None:
                    return ResponseCode.SUCCESS, db_name, \
                           source_name, source_version
            except AttributeError as error_msg:
                LOGGER.logger.error(error_msg)
            except SQLAlchemyError as error_msg:
                LOGGER.logger.error(error_msg)
                return ResponseCode.DIS_CONNECTION_DB, None, None, None
        return ResponseCode.PACK_NAME_NOT_FOUND, None, None, None

    def get_sub_pack(self, source_name_list):
        """
        Description: get a subpack list based on source name list:
                     source_name ->source_name_id -> binary_name
        Args:
             source_name_list: search package's name, database preority list
        Returns:
             response code
             result_list: subpack tuple
        Raises:
            AttributeError: The object does not have this property
            SQLAlchemyError: sqlalchemy error
        """
        if not self.db_object_dict:
            return ResponseCode.DIS_CONNECTION_DB, None
        search_set = {source_name for source_name in source_name_list if source_name}
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
                         bin_pack.version AS sub_pack_version,
                         src.name AS search_name,
                         src.version AS search_version
                     FROM
                         (SELECT name,version,src_name FROM src_pack WHERE {}) src
                         LEFT JOIN bin_pack on src.src_name = bin_pack.rpm_sourcerpm
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
            'return_tuple', 'subpack_name sub_pack_version search_version search_name')
        for search_name in search_set:
            result_list.append(
                (return_tuple(None, None, None, search_name), 'NOT FOUND'))
        return ResponseCode.SUCCESS, result_list


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
        with DBHelper(db_name='lifecycle') as data_name:
            name_list = data_name.session.query(
                DatabaseInfo.name).order_by(DatabaseInfo.priority).all()
            return [name[0] for name in name_list]
    except SQLAlchemyError as error:
        current_app.logger.error(error)
        return None
