#!/usr/bin/python3
"""
Description: Find compilation dependency of source package
class: BuildDepend
"""
from packageship.application.apps.package.function.searchdb import SearchDB
from packageship.application.apps.package.function.install_depend import InstallDepend
from packageship.application.apps.package.function.constants import ResponseCode, ListNode


class BuildDepend():
    """
    Description: Find compilation dependency of source package
    Attributes:
        pkg_name_list: List of package names
        db_list: List of database names
        self_build: Compile dependency conditions
        history_dict: Query history dict
        search_db:Query an instance of a database class
        result_dict:A dictionary to store the data that needs to be echoed
        source_dict:A dictionary to store the searched source code package name
    """

    def __init__(self, pkg_name_list, db_list, self_build=0, history_dict=None):
        """
        init class
        """
        self.pkg_name_list = pkg_name_list
        self._self_build = self_build

        self.db_list = db_list
        self.search_db = SearchDB(db_list)

        self.result_dict = dict()
        self.source_dict = dict()

        self.history_dicts = history_dict if history_dict else {}
        self.not_found_components = set()

    def build_depend_main(self):
        """
        Description: Entry function
        Args:
        Returns:
            ResponseCode: response code
            result_dict: Dictionary of query results
            source_dict: Dictionary of source code package
        Raises:
        """
        if not self.search_db.db_object_dict:
            return ResponseCode.DIS_CONNECTION_DB, None, None, set()

        if self._self_build == 0:
            code = self.build_depend(self.pkg_name_list)
            if None in self.result_dict:
                del self.result_dict[None]
            return code, self.result_dict, None, self.not_found_components

        if self._self_build == 1:
            self.self_build(self.pkg_name_list)
            if None in self.result_dict:
                del self.result_dict[None]
            # There are two reasons for the current status code to return SUCCESS
            # 1, Other branches return three return values.
            #    Here, a place holder is needed to prevent unpacking errors during call
            # 2, This function is an auxiliary function of other modules.
            #    The status code is not the final display status code
            return ResponseCode.SUCCESS, self.result_dict, self.source_dict, self.not_found_components

        return ResponseCode.PARAM_ERROR, None, None,set()

    def build_depend(self, pkg_list):
        """
        Description: Compile dependency query
        Args:
             pkg_list:You need to find the dependent source package name
        Returns:
             ResponseCode: response code
        Raises:
        """
        res_status, build_list, not_fd_build = self.search_db.get_build_depend(pkg_list)
        self.not_found_components.update(not_fd_build)
        if not build_list:
            return res_status if res_status == ResponseCode.DIS_CONNECTION_DB else \
                ResponseCode.PACK_NAME_NOT_FOUND

        # create root node and get next search list
        search_list = self._create_node_and_get_search_list(build_list, pkg_list)

        code, res_dict, not_fd_install = \
            InstallDepend(self.db_list).query_install_depend(search_list,
                                                             self.history_dicts)
        self.not_found_components.update(not_fd_install)
        if not res_dict:
            return code

        for k, values in res_dict.items():
            if k in self.result_dict:
                if ['root', None] in values[ListNode.PARENT_LIST]:
                    index = values[ListNode.PARENT_LIST].index(['root', None])
                    del values[ListNode.PARENT_LIST][index]

                self.result_dict[k][ListNode.PARENT_LIST].extend(values[ListNode.PARENT_LIST])
            else:
                self.result_dict[k] = values

        return ResponseCode.SUCCESS

    def _create_node_and_get_search_list(self, build_list, pkg_list):
        """
        Description: To create root node in self.result_dict and
            return the name of the source package to be found next time
        Args:
            build_list:List of binary package names
            pkg_list: List of binary package names
        Returns:
             the name of the source package to be found next time
        Raises:
        """
        search_set = set()
        search_list = []
        for obj in build_list:
            if not obj.search_name:
                continue

            if obj.search_name + "_src" not in self.result_dict:
                self.result_dict[obj.search_name + "_src"] = [
                    'source',
                    obj.search_version,
                    obj.db_name,
                    [
                        ['root', None]
                    ]
                ]
                search_set.add(obj.search_name)

            if not obj.bin_name:
                continue

            if obj.bin_name in self.history_dicts:
                self.result_dict[obj.bin_name] = [
                    self.history_dicts[obj.bin_name][ListNode.SOURCE_NAME],
                    self.history_dicts[obj.bin_name][ListNode.VERSION],
                    self.history_dicts[obj.bin_name][ListNode.DBNAME],
                    [
                        [obj.search_name, 'build']
                    ]
                ]
            else:
                if obj.bin_name in search_list:
                    self.result_dict[obj.bin_name][ListNode.PARENT_LIST].append([
                        obj.search_name, 'build'
                    ])
                else:
                    self.result_dict[obj.bin_name] = [
                        obj.source_name,
                        obj.version,
                        self.search_db.binary_search_database_for_first_time(obj.bin_name),
                        [
                            [obj.search_name, 'build']
                        ]
                    ]
                    search_list.append(obj.bin_name)

        if search_set and len(search_set) != len(pkg_list):
            temp_set = set(pkg_list) - search_set
            for name in temp_set:
                self.result_dict[name + "_src"] = [
                    None,
                    None,
                    'NOT_FOUND',
                    [
                        ['root', None]
                    ]
                ]
        return search_list

    def self_build(self, pkg_name_li):
        """
        Description: Using recursion to find compilation dependencies
        Args:
            pkg_name_li: Source package name list
        Returns:
        Raises:
        """
        if not pkg_name_li:
            return

        next_src_set = set()
        _, bin_info_lis, not_fd_com = self.search_db.get_build_depend(pkg_name_li)
        self.not_found_components.update(not_fd_com)
        if not bin_info_lis:
            return

            # generate data content
        search_name_set = set()
        for obj in bin_info_lis:

            search_name_set.add(obj.search_name)
            if obj.search_name not in self.source_dict:
                self.source_dict[obj.search_name] = [obj.db_name, obj.search_version]

            if not obj.bin_name:
                continue

            if obj.bin_name not in self.result_dict:
                self.result_dict[obj.bin_name] = [
                    obj.source_name if obj.source_name else None,
                    obj.version if obj.version else None,
                    self.search_db.binary_search_database_for_first_time(obj.bin_name),
                    [
                        [obj.search_name, "build"]
                    ]
                ]
            else:
                node = [obj.search_name, "build"]
                node_list = self.result_dict[obj.bin_name][-1]
                if node not in node_list:
                    node_list.append(node)

            if obj.source_name and \
                    obj.source_name not in self.source_dict and \
                    obj.source_name not in self.history_dicts:
                next_src_set.add(obj.source_name)

        not_found_pkg = set(pkg_name_li) - search_name_set
        for pkg_name in not_found_pkg:
            if pkg_name not in self.source_dict:
                self.source_dict[pkg_name] = ['NOT FOUND', 'NOT FOUND']
        not_found_pkg.clear()
        self.self_build(next_src_set)

        return
