"""
Find compilation dependency of source package
"""
from packageship.application.apps.package.function.searchdb import SearchDB
from packageship.application.apps.package.function.install_depend import InstallDepend
from packageship.application.apps.package.function.constants import ResponseCode, ListNode


class BuildDepend:
    """
    Find compilation dependency of source package
    """

    def __init__(self, pkg_name_list, db_list, self_build=0, history_dict=None):
        self.pkg_name_list = pkg_name_list
        self._self_build = self_build

        self.db_list = db_list
        self.search_db = SearchDB(db_list)

        self.result_dict = dict()
        self.source_dict = dict()

        self.history_dicts = history_dict if history_dict else {}

    def build_depend_main(self):
        """
        Entry function
        :return: ResponseCode,result_dict,source_dict
        """
        if not self.search_db.db_object_dict:
            return ResponseCode.DIS_CONNECTION_DB, None, None

        if self._self_build == 0:
            code = self.build_depend(self.pkg_name_list)
            if None in self.result_dict:
                del self.result_dict[None]
            return code, self.result_dict, None

        if self._self_build == 1:
            self.self_build(self.pkg_name_list)
            if None in self.result_dict:
                del self.result_dict[None]
            # There are two reasons for the current status code to return SUCCESS
            # 1, Other branches return three return values.
            #    Here, a place holder is needed to prevent unpacking errors during call
            # 2, This function is an auxiliary function of other modules.
            #    The status code is not the final display status code
            return ResponseCode.SUCCESS, self.result_dict, self.source_dict

        return ResponseCode.PARAM_ERROR, None, None

    def build_depend(self, pkg_list):
        """
        @:param pkg_list:You need to find the dependent source package name
        :return ResponseCode
        """
        res_status, build_list = self.search_db.get_build_depend(pkg_list)

        if not build_list:
            return res_status if res_status == \
                                 ResponseCode.DIS_CONNECTION_DB else \
                ResponseCode.PACK_NAME_NOT_FOUND
        # create root node and get next search list
        search_list = self._create_node_and_get_search_list(build_list, pkg_list)

        code, res_dict = \
            InstallDepend(self.db_list).query_install_depend(search_list,
                                                             self.history_dicts)
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
        To create root node in self.result_dict and
            return the name of the source package to be found next time
        @:param build_list:List of binary package names
        @:param pkg_list: List of binary package names
        :return the name of the source package to be found next time
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
                        obj.db_name,
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
        Using recursion to find compilation dependencies
        :param pkg_name_li: Source package name list
        :return:
        """
        if not pkg_name_li:
            return

        next_src_set = set()
        _, bin_info_lis = self.search_db.get_build_depend(pkg_name_li)

        if not bin_info_lis:
            return

            # generate data content
        for obj in bin_info_lis:

            if not obj.bin_name:
                continue
            # for first loop, init the source_dict
            if not self.source_dict:
                for src_name in pkg_name_li:
                    self.source_dict[src_name] = [obj.db_name, obj.search_version]
            if obj.bin_name not in self.result_dict:
                self.result_dict[obj.bin_name] = [
                    obj.source_name if obj.source_name else None,
                    obj.version if obj.version else None,
                    obj.db_name if obj.db_name else "NOT_FOUND",
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
                self.source_dict[obj.source_name] = [obj.db_name,
                                                     obj.version]
                next_src_set.add(obj.source_name)

        self.self_build(next_src_set)

        return
