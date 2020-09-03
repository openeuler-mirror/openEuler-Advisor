#!/usr/bin/python3
"""
Description: Querying for install dependencies
             Querying packages install depend for those package can be installed
class: InstallDepend, DictionaryOperations
"""
from packageship.libs.log import Log
from .searchdb import SearchDB
from .constants import ResponseCode
from .constants import ListNode

LOGGER = Log(__name__)


class InstallDepend():
    """
    Description: query install depend of package
    Attributes：
        db_list: A list of Database name to show the priority
        __search_list: Contain the binary packages searched in the next loop
        binary_dict: Contain all the binary packages info and operation
        __search_db: A object of database which would be connected
        not_found_components: Contain the package not found components
    changeLog:
    """
    #pylint: disable = too-few-public-methods
    def __init__(self, db_list):
        """
        Initialization class
        """
        self.binary_dict = DictionaryOperations()
        self.__search_list = []

        self.db_list = db_list
        self.__search_db = SearchDB(db_list)
        self.not_found_components = set()

    def query_install_depend(self, binary_list, history_dicts=None):
        """
        Description: init result dict and determint the loop end point
        Args:
            binary_list: A list of binary rpm package name
            history_dicts: record the searching install depend history,
                              defualt is None
        Returns:
             binary_dict.dictionary:
                    {binary_name: [
                        src,
                        dbname,
                        version,
                        [
                            parent_node_package_name
                            'install'
                        ]
                    ]}
            not_found_components:Set of package not found components
        Raises:
        """
        if not self.__search_db.db_object_dict:
            return ResponseCode.DIS_CONNECTION_DB, None, set()
        if not binary_list:
            return ResponseCode.INPUT_NONE, None, set()
        for binary in binary_list:
            if binary:
                self.__search_list.append(binary)
            else:
                LOGGER.logger.warning("There is a  NONE in input value:" + str(binary_list))
        while self.__search_list:
            self.__query_single_install_dep(history_dicts)
        return ResponseCode.SUCCESS, self.binary_dict.dictionary, self.not_found_components

    def __query_single_install_dep(self, history_dicts):
        """
         Description: query a package install depend and append to result
        Args:
             history_dicts: A list of binary rpm package name
        Returns:
            response_code: response code
        Raises:
        """
        result_list, not_found_components = map(set, self.__search_db.get_install_depend(self.__search_list))
        self.not_found_components.update(not_found_components)
        for search in self.__search_list:
            if search not in self.binary_dict.dictionary:
                self.binary_dict.init_key(key=search, parent_node=[])
        self.__search_list.clear()
        if result_list:
            for result, dbname in result_list:
                if not self.binary_dict.dictionary[result.search_name][ListNode.PARENT_LIST]:
                    self.binary_dict.init_key(key=result.search_name,
                                              src=result.search_src_name,
                                              version=result.search_version,
                                              dbname=dbname)
                else:
                    self.binary_dict.update_value(key=result.search_name,
                                                  src=result.search_src_name,
                                                  version=result.search_version,
                                                  dbname=dbname)

                if result.depend_name:
                    if result.depend_name in self.binary_dict.dictionary:
                        self.binary_dict.update_value(key=result.depend_name,
                                                      parent_node=[result.search_name, 'install'])
                    elif history_dicts is not None and result.depend_name in history_dicts:
                        self.binary_dict.init_key(
                            key=result.depend_name,
                            src=history_dicts[result.depend_name][ListNode.SOURCE_NAME],
                            version=history_dicts[result.depend_name][ListNode.VERSION],
                            dbname=None,
                            parent_node=[[result.search_name, 'install']]
                            )
                    else:
                        self.binary_dict.init_key(key=result.depend_name,
                                                  parent_node=[[result.search_name, 'install']])
                        self.__search_list.append(result.depend_name)


class DictionaryOperations():
    """
    Description: Related to dictionary operations, creating dictionary, append dictionary
    Attributes：
        dictionary: Contain all the binary packages info after searching
    changeLog:
    """

    def __init__(self):
        """
        init class
        """
        self.dictionary = dict()

    def init_key(self, key, src=None, version=None, dbname=None, parent_node=None):
        """
        Description: Creating dictionary
        Args:
            key: binary_name
            src: source_name
            version: version
            dbname: databases name
            parent_node: parent_node
        Returns:
            dictionary[key]: [src, version, dbname, parent_node]
        """
        if dbname:
            self.dictionary[key] = [src, version, dbname, [['root', None]]]
        else:
            self.dictionary[key] = [src, version, dbname, parent_node]

    def update_value(self, key, src=None, version=None, dbname=None, parent_node=None):
        """
        Description: append dictionary
        Args:
            key: binary_name
            src: source_name
            version: version
            dbname: database name
            parent_node: parent_node
        Returns:
        Raises:
        """
        if src:
            self.dictionary[key][ListNode.SOURCE_NAME] = src
        if version:
            self.dictionary[key][ListNode.VERSION] = version
        if dbname:
            self.dictionary[key][ListNode.DBNAME] = dbname
        if parent_node:
            self.dictionary[key][ListNode.PARENT_LIST].append(parent_node)
