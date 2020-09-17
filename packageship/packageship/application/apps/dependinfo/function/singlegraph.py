#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
Data analysis of dependency graph
"""
import random
from retrying import retry
from packageship.application.apps.package.function.searchdb import db_priority
from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.serialize import BeDependSchema
from packageship.application.apps.package.serialize import BuildDependSchema
from packageship.application.apps.package.serialize import InstallDependSchema
from packageship.application.apps.package.serialize import SelfDependSchema
from packageship.application.apps.package.function.self_depend import SelfDepend
from packageship.application.apps.package.function.install_depend import InstallDepend
from packageship.application.apps.package.function.build_depend import BuildDepend
from packageship.application.apps.package.function.be_depend import BeDepend
from .graphcache import self_build, bedepend, build_depend, install_depend


LEVEL_RADIUS = 30
NODE_SIZE = 60
PACKAGE_NAME = 0


class SelfBuildDep:
    """
        Self-compilation dependent data query analysis
    """

    def __init__(self, graph):
        self.graph = graph
        self.query_parameter = {
            'packagename': self.graph.packagename,
            'db_list': self.graph.dbname,
            'packtype': self.graph.packagetype,
            'selfbuild': self.graph.selfbuild,
            'withsubpack': self.graph.withsubpack
        }

    def _validate(self):
        depend = SelfDependSchema().validate(self.query_parameter)
        if depend:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Query dependency data
        """
        _response_code, binary_dicts, source_dicts, not_fd_components = \
            SelfDepend(query_parameter['db_list']).query_depend(query_parameter['packagename'],
                                                                int(
                                                                    query_parameter['selfbuild']),
                                                                int(
                                                                    query_parameter['withsubpack']),
                                                                query_parameter['packtype'])
        return {
            "binary_dicts": binary_dicts,
            "source_dicts": source_dicts,
            "not_found_components": list(not_fd_components)
        }

    def __call__(self):
        if not self._validate():
            return ResponseCode.PARAM_ERROR
        database_error = self.graph.database_priority()
        if database_error:
            return database_error

        @retry(wait_random_min=50, wait_random_max=500)
        def _query_depend():
            query_result = self_build(self.query_parameter)
            if query_result == 'LOADING':
                raise Exception()
            self.graph.package_datas = query_result['binary_dicts']

        _query_depend()
        if self.graph.package_datas:
            self.graph.graph_data()
        return ResponseCode.SUCCESS


class InstallDep:
    """
        Installation dependent data query analysis
    """

    def __init__(self, graph):
        self.graph = graph
        self.query_parameter = {
            'binaryName': self.graph.packagename,
            'db_list': self.graph.dbname
        }

    def _validate(self):
        depend = InstallDependSchema().validate(self.query_parameter)
        if depend:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Query dependency data
        """
        _response_code, install_dict, not_found_components = \
            InstallDepend(query_parameter['db_list']
                          ).query_install_depend([query_parameter['binaryName']])
        return {
            "install_dict": install_dict,
            'not_found_components': list(not_found_components)
        }

    def __call__(self):
        if not self._validate():
            return ResponseCode.PARAM_ERROR
        database_error = self.graph.database_priority()
        if database_error:
            return database_error

        @retry(wait_random_min=50, wait_random_max=500)
        def _query_depend():
            query_result = install_depend(self.query_parameter)
            if query_result == 'LOADING':
                raise Exception()
            self.graph.package_datas = query_result['install_dict']

        _query_depend()
        if self.graph.package_datas:
            self.graph.graph_data()
        return ResponseCode.SUCCESS


class BuildDep:
    """
        Compile dependent data query analysis
    """

    def __init__(self, graph):
        self.graph = graph
        self.query_parameter = {
            'sourceName': self.graph.packagename,
            'db_list': self.graph.dbname
        }

    def _validate(self):
        depend = BuildDependSchema().validate(self.query_parameter)
        if depend:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Query dependency data
        """
        build_ins = BuildDepend(
            [query_parameter['sourceName']], query_parameter['db_list'])
        _res_code, builddep_dict, _, not_found_components = build_ins.build_depend_main()
        return {
            'build_dict': builddep_dict,
            'not_found_components': list(not_found_components)
        }

    def __call__(self):
        if not self._validate():
            return ResponseCode.PARAM_ERROR
        database_error = self.graph.database_priority()
        if database_error:
            return database_error

        @retry(wait_random_min=50, wait_random_max=500)
        def _query_depend():
            query_result = build_depend(self.query_parameter)
            if query_result == 'LOADING':
                raise Exception()
            self.graph.package_datas = query_result['build_dict']

        _query_depend()
        if self.graph.package_datas:
            self.graph.graph_data()
        return ResponseCode.SUCCESS


class BeDependOn:
    """
        Dependent query
    """

    def __init__(self, graph):
        self.graph = graph
        dbname = None
        if self.graph.dbname and isinstance(self.graph.dbname, (list, tuple)):
            dbname = self.graph.dbname[0]
        self.query_parameter = {
            'packagename': self.graph.packagename,
            'dbname': dbname,
            'withsubpack': self.graph.withsubpack
        }

    def _validate(self):
        """Verify the validity of the data"""
        bedependon = BeDependSchema().validate(self.query_parameter)
        if bedependon:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Query dependency data
        """
        bedepnd_ins = BeDepend(
            query_parameter['packagename'],
            query_parameter['dbname'],
            query_parameter['withsubpack'])
        be_depend_dict = bedepnd_ins.main()
        return be_depend_dict

    def __call__(self):
        if not self._validate():
            return ResponseCode.PARAM_ERROR
        database_error = self.graph.database_priority()
        if database_error:
            return database_error

        @retry(wait_random_min=50, wait_random_max=500)
        def _query_depend():
            query_result = bedepend(self.query_parameter)
            if query_result == 'LOADING':
                raise Exception()
            self.graph.package_datas = query_result

        _query_depend()
        if self.graph.package_datas:
            self.graph.graph_data()
        return ResponseCode.SUCCESS


class BaseGraph:
    """
    Basic operation of dependency graph
    """
    depend = {
        'selfbuild': SelfBuildDep,
        'installdep': InstallDep,
        'builddep': BuildDep,
        'bedepend': BeDependOn
    }

    def __init__(self, query_type, **kwargs):
        self.query_type = query_type
        self.__dict__.update(**kwargs)
        depend_graph = self.depend.get(self.query_type)
        if depend_graph is None:
            raise RuntimeError(
                'The query parameter type is wrong, and normal',
                ' dependent data analysis cannot be completed')
        self.graph = depend_graph(self)
        self._color = ['#E02020', '#FA6400', '#F78500', '#6DD400',
                       '#44D7B6', '#32C5FF', '#0091FF', '#6236FF', '#B620E0', '#6D7278']
        self.nodes = dict()
        self.edges = list()
        self.depend_package = dict()
        self.package_datas = {}
        self.up_depend_node = None
        self.down_depend_nodes = None

    def __getattr__(self, value):
        if value not in self.__dict__:
            return None
        return self.__dict__[value]

    @property
    def color(self):
        """rgb random color value acquisition"""
        return self._color[random.randint(0, len(self._color)-1)]

    @staticmethod
    def dynamic_coordinate(level, upper_layer=True):
        """
            Dynamically calculate the random coordinates of each package in the current level

            Args:
                level: The level of the package
                upper_layer:Query the upper level of the package
            Returns:
                The coordinate value of the dynamically calculated dependent package
                example : (x,y)
        """
        min_value, max_value = (level - 1) * LEVEL_RADIUS, level * LEVEL_RADIUS
        _x, _y = random.uniform(min_value, max_value), random.uniform(
            min_value, max_value)
        if not upper_layer:
            _x, _y = _x * -1, _y * -1
        return _x, _y

    @staticmethod
    def dynamin_node_size(level):
        """
            Dynamically calculate the size of each node
        """
        min_value, max_value = int(
            NODE_SIZE / (level + 1)), int(NODE_SIZE / level)
        node_size = random.randint(
            min_value, max_value) * (1 - level / 6 * 1.0)
        return node_size

    def database_priority(self):
        """Priority list of databases"""

        databases = db_priority()
        if not databases:
            return ResponseCode.FILE_NOT_FIND_ERROR
        self.dbname = self.dbname if self.dbname else databases

        if any(filter(lambda db_name: db_name not in databases, self.dbname)):
            return ResponseCode.DB_NAME_ERROR
        return None

    @staticmethod
    def create_dict(**kwargs):
        """
            Create dictionary data
        """
        if isinstance(kwargs, dict):
            return kwargs
        return dict()

    def combination_nodes(self, level_depend, package_name, upper_layer=True, root=True):
        """
            Regroup node values
            Args:
                level_depend:Level of dependency
                package_name:Dependent package name
                upper_layer:The direction of dependency, upper-level
                            dependency or lower-level dependency
        """
        if root:
            _x, _y = 0, 0
        else:
            _x, _y = BaseGraph.dynamic_coordinate(level_depend, upper_layer)
        _size = BaseGraph.dynamin_node_size(level_depend)
        self.nodes[package_name] = BaseGraph.create_dict(
            color=self.color,
            label=package_name,
            y=_y,
            x=_x,
            id=package_name,
            size=_size)

    def combination_edges(self, source_package_name, target_package_name):
        """
            Depend on the data combination of the edges node in the graph
            Args:
                source_package_name:Source node
                level_depend:Level of dependency
                target_package_name:Target node
        """
        self.edges.append(BaseGraph.create_dict(
            sourceID=source_package_name,
            targetID=target_package_name,
        ))

    def up_level_depend(self, level_depend):
        """
            Data analysis of the previous layer
            Args:
               level_depend:Level of dependency
        """
        _up_depend_nodes = []
        for node_name in self.up_depend_node:
            depend_data = self.package_datas[node_name][-1]
            if depend_data:
                for depend_item in depend_data:
                    _up_depend_nodes.append(depend_item[PACKAGE_NAME])
                    self.combination_nodes(
                        level_depend, depend_item[PACKAGE_NAME], root=False)
                    self.combination_edges(
                        node_name, depend_item[PACKAGE_NAME])
        self.up_depend_node = list(set(_up_depend_nodes))

    def down_level_depend(self, level_depend):
        """
            Specify the next level of dependencies of dependent nodes
            Args:
                level_depend:Level of dependency
        """
        _down_depend_nodes = []
        for package_name, package_depend in self.package_datas.items():
            for depend_item in package_depend[-1]:
                if depend_item[PACKAGE_NAME] in self.down_depend_nodes:
                    _down_depend_nodes.append(package_name)
                    self.combination_nodes(
                        level_depend, package_name, False, root=False)
                    self.combination_edges(
                        depend_item[PACKAGE_NAME], package_name)
        self.down_depend_nodes = list(set(_down_depend_nodes))

    def graph_data(self):
        """
            Resolve the data in the dependency graph
        """
        def depend_package():
            self.combination_nodes(1, self.node_name, root=False)
            for level in range(1, 3):
                self.up_level_depend(level)
                self.down_level_depend(level)

        def source_depend_relation():
            for package_name, package_depend in self.package_datas.items():
                if package_depend[PACKAGE_NAME] == self.node_name:
                    self.up_depend_node.append(package_name)
                    self.down_depend_nodes.append(package_name)

        if self.packagetype == 'source':
            self.up_depend_node, self.down_depend_nodes = list(), list()
            source_depend_relation()

        if self.packagetype == "binary":
            self.up_depend_node = [self.node_name]
            self.down_depend_nodes = [self.node_name]
        depend_package()

        self.depend_package = {
            'nodes': [node for key, node in self.nodes.items()],
            'edges': self.edges
        }

    def parse_depend_graph(self):
        """Analyze the data that the graph depends on"""
        response_status = self.graph()
        if response_status != ResponseCode.SUCCESS:
            return (response_status, None)

        return (response_status, self.depend_package)
