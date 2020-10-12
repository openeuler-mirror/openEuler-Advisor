#!/usr/bin/python3
"""
Description: Querying for self dependencies
    Querying packages install and build depend for those package can be
    build and install
class: SelfDepend, DictionaryOperations
"""

import copy
from packageship.libs.log import Log
from packageship.application.apps.package.function.searchdb import SearchDB
from packageship.application.apps.package.function.constants import ResponseCode, ListNode
from packageship.application.apps.package.function.install_depend import InstallDepend \
    as install_depend
from packageship.application.apps.package.function.build_depend import BuildDepend as build_depend

LOGGER = Log(__name__)


class SelfDepend():
    """
    Description:
        Querying for self dependencies
        Querying packages install and build depend for those package can be
        build and install
    Attributes:
        db_list: list of database names
        binary_dict: Contain all the binary packages info and operation
        source_dicts: Contain all the source packages info and operation
        result_tmp: restore the return result dict
        search_install_list: Contain the binary packages searched install dep in the next loop
        search_build_list: Contain the source packages searched build dep in the next loop
        search_subpack_list: Contain the source packages searched subpack in the next loop
        withsubpack: withsubpack
        search_db: A object of database which would be connected
        not_found_components: Contain the package not found components
    """

    # pylint: disable = R0902
    def __init__(self, db_list):
        """
        init class
        """
        self.binary_dict = DictionaryOperations()
        self.source_dicts = DictionaryOperations()
        self.result_tmp = dict()
        self.search_install_list = []
        self.search_build_list = []
        self.search_subpack_list = []
        self.withsubpack = 0
        self.db_list = db_list
        self.search_db = SearchDB(db_list)
        self.not_found_components = set()

    def query_depend(self, packname, selfbuild, withsubpack, packtype='binary'):
        """
        Description: init result dict and determint the loop end point
        Args:
             packname: Package name
             selfbuild: selfbuild
             withsubpack: withsubpack
             packtype: package type
        Returns:
             binary_dict.dictionary: Contain all the binary packages info after searching
             source_dicts.dictionary: Contain all the source packages info after searching
             not_found_components :Set of package not found components
        Raises:
        """
        if not self.search_db.db_object_dict:
            return ResponseCode.DIS_CONNECTION_DB, None, None, set()
        if not packname:
            return ResponseCode.INPUT_NONE

        self.withsubpack = withsubpack
        response_code = self.init_dict(packname, packtype)
        if response_code != ResponseCode.SUCCESS:
            return (response_code, self.binary_dict.dictionary,
                    self.source_dicts.dictionary, self.not_found_components)

        for key, _ in self.binary_dict.dictionary.items():
            self.search_install_list.append(key)
        for key, _ in self.source_dicts.dictionary.items():
            self.search_build_list.append(key)
            if self.withsubpack == 1:
                self.search_subpack_list.append(key)

        while self.search_build_list or self.search_install_list or self.search_subpack_list:
            if self.search_install_list:
                self.query_install()
            if self.withsubpack == 1 and self.search_subpack_list:
                self.with_subpack()
            if self.search_build_list:
                self.query_build(selfbuild)
        return (response_code, self.binary_dict.dictionary,
                self.source_dicts.dictionary, self.not_found_components)

    def init_dict(self, packname, packtype):
        """
        Description: init result dict
        Args:
             packname: package name
             packtype: package type
        Returns:
            response_code
        Raises:
        """
        if packtype == 'source':
            response_code, subpack_list = self.search_db.get_sub_pack([packname])
            if not subpack_list:
                return ResponseCode.PACK_NAME_NOT_FOUND

            for subpack_tuple, dbname in subpack_list:
                self.source_dicts.append_src(packname, dbname, subpack_tuple.search_version)
                if dbname == 'NOT FOUND':
                    continue

                if subpack_tuple.subpack_name and subpack_tuple.subpack_name \
                        not in self.binary_dict.dictionary:
                    self.binary_dict.append_bin(key=subpack_tuple.subpack_name,
                                                src=packname,
                                                version=subpack_tuple.search_version,
                                                dbname=dbname)

        else:
            response_code, dbname, source_name, version = \
                self.search_db.get_src_name(packname)
            if response_code != ResponseCode.SUCCESS:
                return response_code
            self.source_dicts.append_src(source_name, dbname, version)
            self.binary_dict.append_bin(key=packname,
                                        src=source_name,
                                        version=version,
                                        dbname=dbname)
        return response_code

    def query_install(self):
        """
        Description: query install depend
        Args:
        Returns:
        Raises:
        """
        self.result_tmp.clear()
        _, self.result_tmp, not_fd_com = \
            install_depend(self.db_list).query_install_depend(self.search_install_list,
                                                              history_dicts=self.binary_dict.dictionary)
        self.not_found_components.update(not_fd_com)
        self.search_install_list.clear()
        for key, values in self.result_tmp.items():
            if key in self.binary_dict.dictionary:
                if ['root', None] in values[ListNode.PARENT_LIST]:
                    index = values[ListNode.PARENT_LIST].index(['root', None])
                    del values[ListNode.PARENT_LIST][index]
                self.binary_dict.update_value(key=key, parent_list=values[ListNode.PARENT_LIST])
            else:
                if not key:
                    continue
                self.binary_dict.dictionary[key] = copy.deepcopy(values)
                source_name = values[ListNode.SOURCE_NAME]
                if not source_name:
                    LOGGER.logger.warning("source name is None")
                if source_name and source_name not in self.source_dicts.dictionary:
                    db_, src_version_ = self.search_db.get_version_and_db(source_name)
                    self.source_dicts.append_src(key=source_name,
                                                 dbname=db_ if db_ else values[ListNode.DBNAME],
                                                 version=src_version_
                                                 if src_version_ else values[ListNode.VERSION])
                    self.search_build_list.append(source_name)
                    if self.withsubpack == 1:
                        self.search_subpack_list.append(source_name)

    def with_subpack(self):
        """
        Description: query subpackage
        Args:
        Returns:
        Raises:
        """
        if None in self.search_subpack_list:
            LOGGER.logger.warning("There is a  NONE in input value: %s",
                                  str(self.search_subpack_list))
            self.search_subpack_list.remove(None)
        _, result_list = self.search_db.get_sub_pack(self.search_subpack_list)
        for subpack_tuple, dbname in result_list:
            if dbname == 'NOT FOUND':
                continue

            if subpack_tuple.subpack_name and subpack_tuple.subpack_name \
                    not in self.binary_dict.dictionary:
                self.binary_dict.append_bin(key=subpack_tuple.subpack_name,
                                            src=subpack_tuple.search_name,
                                            version=subpack_tuple.sub_pack_version,
                                            dbname=dbname,
                                            parent_node=[subpack_tuple.search_name, 'Subpack'])
                self.search_install_list.append(subpack_tuple.subpack_name)
        self.search_subpack_list.clear()

    def query_build(self, selfbuild):
        """
        Description: query build depend
        Args:
            selfbuild: selfbuild
        Returns:
        Raises:
        """
        self.result_tmp.clear()
        if selfbuild == 0:
            self.query_builddep()
        else:
            self.query_selfbuild()

    def query_builddep(self):
        """
        Description: for selfbuild == 0, query selfbuild depend
        Args:
        Returns:
        Raises:
        """
        _, self.result_tmp, _, not_fd_com = build_depend(
            self.search_build_list,
            self.db_list,
            self_build=0,
            history_dict=self.binary_dict.dictionary
        ).build_depend_main()
        self.not_found_components.update(not_fd_com)
        self.search_build_list.clear()
        for key, values in self.result_tmp.items():
            if not key:
                LOGGER.logger.warning("key is NONE for value = %s", str(values))
                continue
            if key not in self.binary_dict.dictionary and values[0] != 'source':
                self.binary_dict.dictionary[key] = copy.deepcopy(values)
                source_name = values[ListNode.SOURCE_NAME]
                if not source_name:
                    LOGGER.logger.warning("source name is None")
                if source_name and source_name not in self.source_dicts.dictionary:
                    db_, src_version_ = self.search_db.get_version_and_db(source_name)
                    self.source_dicts.append_src(key=source_name,
                                                 dbname=db_ if db_ else values[ListNode.DBNAME],
                                                 version=src_version_
                                                 if src_version_ else values[ListNode.VERSION])
                    if self.withsubpack == 1:
                        self.search_subpack_list.append(source_name)
                    elif key in self.binary_dict.dictionary:
                        self.binary_dict.update_value(key=key,
                                                      parent_list=values[ListNode.PARENT_LIST])

    def query_selfbuild(self):
        """
        Description: for selfbuild == 1, query selfbuild depend
        Args:
        Returns:
        """
        _, self.result_tmp, source_dicts_tmp, not_fd_com = build_depend(
            self.search_build_list,
            self.db_list,
            self_build=1,
            history_dict=self.source_dicts.dictionary
        ).build_depend_main()
        self.not_found_components.update(not_fd_com)
        for key, values in self.result_tmp.items():
            if not key:
                LOGGER.logger.warning("key is NONE for value = %s", str(values))
                continue
            if key in self.binary_dict.dictionary:
                self.binary_dict.update_value(key=key, parent_list=values[ListNode.PARENT_LIST])
            else:
                self.binary_dict.dictionary[key] = copy.deepcopy(values)
                self.search_install_list.append(key)
        for key, values in source_dicts_tmp.items():
            if not key:
                LOGGER.logger.warning("key is NONE for value = %s", str(values))
                continue
            if key not in self.source_dicts.dictionary:
                self.source_dicts.dictionary[key] = copy.deepcopy(values)
                if self.withsubpack == 1:
                    self.search_subpack_list.append(key)
        self.search_build_list.clear()


class DictionaryOperations():
    """
    Description: Related to dictionary operations, creating dictionary, append dictionary
    Attributes:
        dictionary: dict
    """

    def __init__(self):
        """
        init class
        """
        self.dictionary = dict()

    def append_src(self, key, dbname, version):
        """
        Description: Appending source dictionary
        Args:
            key: bianry name
            dbname: database name
            version: version
        Returns:
        Raises:
        """
        self.dictionary[key] = [dbname, version]

    # pylint: disable=R0913
    def append_bin(self, key, src=None, version=None, dbname=None, parent_node=None):
        """
        Description: Appending binary dictionary
        Args:
            key: binary name
            src: source name
            version: version
            dbname: database name
            parent_node: parent node
        Returns:
        Raises:
        """
        if not parent_node:
            self.dictionary[key] = [src, version, dbname, [['root', None]]]
        else:
            self.dictionary[key] = [src, version, dbname, [parent_node]]

    def update_value(self, key, parent_list=None):
        """
        Args:
            key: binary name
            parent_list: parent list
        Returns:
        Raises:
        """
        if parent_list:
            for parent in parent_list:
                if parent not in self.dictionary[key][ListNode.PARENT_LIST]:
                    self.dictionary[key][ListNode.PARENT_LIST].append(parent)
