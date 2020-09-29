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
from packageship.libs.log import Log
from .graphcache import self_build, bedepend, build_depend, install_depend


LEVEL_RADIUS = 30
NODE_SIZE = 25
PACKAGE_NAME = 0
LOGGER = Log(__name__)


class SelfBuildDep:
    """
        Description: Self-compilation dependent data query analysis

        Attributes:
            graph:Diagram of an underlying operation instance
            query_parameter:Parameters for a dependency query
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

    def validate(self):
        """Verify the validity of the data"""
        depend = SelfDependSchema().validate(self.query_parameter)
        if depend:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Self-compile dependent relational queries

            Args:
                query_parameter:Parameters for a dependency query
        """
        db_list = query_parameter['db_list']
        packagename = query_parameter['packagename']
        selfbuild = int(query_parameter['selfbuild'])
        withsubpack = int(query_parameter['withsubpack'])
        packtype = query_parameter['packtype']
        _response_code, binary_dicts, source_dicts, not_fd_components = \
            SelfDepend(db_list).query_depend(packagename,
                                             selfbuild,
                                             withsubpack,
                                             packtype)
        return {
            "code": _response_code,
            "binary_dicts": binary_dicts,
            "source_dicts": source_dicts,
            "not_found_components": list(not_fd_components)
        }

    def __call__(self):
        def _query_depend():
            query_result = self_build(self.query_parameter)
            return query_result['binary_dicts']
        return self.graph.get_depend_relation_data(self, _query_depend)


class InstallDep:
    """
        Installation dependent data query analysis

        Attributes:
            graph:Diagram of an underlying operation instance
            query_parameter:Parameters for a dependency query
    """

    def __init__(self, graph):
        self.graph = graph
        self.query_parameter = {
            'binaryName': self.graph.packagename,
            'db_list': self.graph.dbname
        }

    def validate(self):
        """Verify the validity of the data"""
        depend = InstallDependSchema().validate(self.query_parameter)
        if depend:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Install dependent relational queries

            Args:
                query_parameter:Parameters for a dependency query
        """
        db_list = query_parameter['db_list']
        binary_name = query_parameter['binaryName']
        _response_code, install_dict, not_found_components = \
            InstallDepend(db_list).query_install_depend([binary_name])
        return {
            "code": _response_code,
            "install_dict": install_dict,
            'not_found_components': list(not_found_components)
        }

    def __call__(self):
        def _query_depend():
            query_result = install_depend(self.query_parameter)
            return query_result['install_dict']
        return self.graph.get_depend_relation_data(self, _query_depend)


class BuildDep:
    """
        Compile dependent data query analysis

        Attributes:
            graph:Diagram of an underlying operation instance
            query_parameter:Parameters for a dependency query
    """

    def __init__(self, graph):
        self.graph = graph
        self.query_parameter = {
            'sourceName': self.graph.packagename,
            'db_list': self.graph.dbname
        }

    def validate(self):
        """Verify the validity of the data"""
        depend = BuildDependSchema().validate(self.query_parameter)
        if depend:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Compile dependent relational queries

            Args:
                query_parameter:Parameters for a dependency query
        """
        source_name = query_parameter['sourceName']
        db_list = query_parameter['db_list']
        build_ins = BuildDepend([source_name], db_list)
        _res_code, builddep_dict, _, not_found_components = build_ins.build_depend_main()
        return {
            "code": _res_code,
            'build_dict': builddep_dict,
            'not_found_components': list(not_found_components)
        }

    def __call__(self):
        def _query_depend():
            query_result = build_depend(self.query_parameter)
            return query_result['build_dict']
        return self.graph.get_depend_relation_data(self, _query_depend)


class BeDependOn:
    """
        Dependent relational queries

        Attributes:
            graph:Diagram of an underlying operation instance
            query_parameter:Parameters for a dependency query
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

    def validate(self):
        """Verify the validity of the data"""
        bedependon = BeDependSchema().validate(self.query_parameter)
        if bedependon:
            return False
        return True

    @staticmethod
    def query_depend_relation(query_parameter):
        """
            Dependent relational queries

            Args:
                query_parameter:Parameters for a dependency query
        """
        packagename = query_parameter['packagename']
        db_name = query_parameter['dbname']
        withsubpack = query_parameter['withsubpack']
        bedepnd_ins = BeDepend(packagename, db_name, withsubpack)
        be_depend_dict = bedepnd_ins.main()
        _code = ResponseCode.PACK_NAME_NOT_FOUND
        if be_depend_dict:
            _code = ResponseCode.SUCCESS
        return {
            "code": _code,
            "bedepend": be_depend_dict
        }

    def __call__(self):

        def _query_depend():
            query_result = bedepend(self.query_parameter)
            return query_result['bedepend']
        return self.graph.get_depend_relation_data(self, _query_depend)


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
        self.dbname = None
        self.__dict__.update(**kwargs)
        depend_graph = self.depend.get(self.query_type)
        if depend_graph is None:
            raise RuntimeError(
                'The query parameter type is wrong, and normal',
                ' dependent data analysis cannot be completed')
        self.graph = depend_graph(self)
        self._color = ['#E02020', '#FA6400', '#F78500', '#6DD400', '#44D7B6',
                       '#32C5FF', '#0091FF', '#6236FF', '#B620E0', '#6D7278']
        self.nodes = dict()
        self.edges = list()
        self.depend_package = dict()
        self.package_datas = {
            'uplevel': dict(),
            'downlevel': dict()
        }
        self.up_depend_node = list()
        self.down_depend_nodes = list()
        self._quadrant = [1, -1]

    def __getattr__(self, value):
        if value not in self.__dict__:
            return None
        return self.__dict__[value]

    @property
    def color(self):
        """rgb random color value acquisition"""
        return self._color[random.randint(0, 9)]

    @property
    def quadrant(self):
        """Get the coordinate quadrant at random"""
        return self._quadrant[random.randint(0, 1)]

    @property
    def coordinate(self):
        """
            Dynamically calculate the random coordinates of each package in the current level

            Returns:
                The coordinate value of the dynamically calculated dependent package
                example : (x,y)
        """
        _x, _y = random.uniform(0, LEVEL_RADIUS) * self.quadrant, random.uniform(
            0, LEVEL_RADIUS) * self.quadrant
        return _x, _y

    @property
    def node_size(self):
        """Dynamically calculate the size of each node """
        node_size = random.uniform(1, NODE_SIZE)
        return node_size

    def _database_priority(self):
        """Verify the validity of the query database"""

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

            Args:
                kwargs: Create each key-Val key-value pair for the dictionary
        """
        if isinstance(kwargs, dict):
            return kwargs
        return dict()

    def _combination_nodes(self, package_name, root=True):
        """
            Regroup node values
            Args:
                package_name:Dependent package name
                root:he coordinate value of the root node
        """
        _size = self.node_size
        if root:
            _x, _y = 0, 0
            _size = 30
        else:
            _x, _y = self.coordinate
        self.nodes[package_name] = BaseGraph.create_dict(
            color=self.color,
            label=package_name,
            y=_y,
            x=_x,
            id=package_name,
            size=_size)

    def _combination_edges(self, source_package_name, target_package_name):
        """
            Depend on the data combination of the edges node in the graph
            Args:
                source_package_name:Source node
                target_package_name:Target node
        """
        self.edges.append(BaseGraph.create_dict(
            sourceID=source_package_name,
            targetID=target_package_name,
        ))

    def _up_level_depend(self):
        """
            Data analysis of the previous layer
        """
        _up_depend_nodes = []
        for node_name in self.up_depend_node:
            if node_name not in self.package_datas['uplevel'].keys():
                continue
            depend_data = self.package_datas['uplevel'][node_name]
            for depend_item in depend_data:
                _up_depend_nodes.append(depend_item)
                self._combination_nodes(
                    depend_item, root=False)
                self._combination_edges(
                    node_name, depend_item)

        self.up_depend_node = list(set(_up_depend_nodes))

    def _down_level_depend(self):
        """
            Specify the next level of dependencies of dependent nodes
        """
        _down_depend_nodes = []
        for node_name in self.down_depend_nodes:
            if node_name not in self.package_datas['downlevel'].keys():
                continue
            depend_data = self.package_datas['downlevel'][node_name]
            for depend_item in depend_data:
                _down_depend_nodes.append(depend_item)
                self._combination_nodes(
                    depend_item, root=False)
                self._combination_edges(
                    depend_item, node_name)

        self.down_depend_nodes = list(set(_down_depend_nodes))

    def _graph_data(self):
        """
            Resolve the data in the dependency graph
        """
        def depend_package():
            if self.packagetype == "binary":
                self.up_depend_node.append(self.node_name)
                self.down_depend_nodes.append(self.node_name)
            self._combination_nodes(self.node_name)
            for _level in range(1, 3):
                self._up_level_depend()
                self._down_level_depend()
        depend_package()

        self.depend_package = {
            'nodes': [node for key, node in self.nodes.items()],
            'edges': self.edges
        }

    def _relation_recombine(self, package_datas):
        """
        The data in the dependency query is recombined
        into representations of the upper and lower dependencies
        of the current node

        Args:
           package_datas:Package dependency data

        """
        for package_name, package_depend in package_datas.items():
            if not package_depend or not isinstance(package_depend, list):
                continue
            if self.packagetype == 'source' and package_depend[PACKAGE_NAME] == self.node_name:
                self.up_depend_node.append(package_name)
                self.down_depend_nodes.append(package_name)

            for depend_item in package_depend[-1]:
                if depend_item[PACKAGE_NAME] == 'root':
                    continue
                if not self.package_datas['uplevel'].__contains__(package_name):
                    self.package_datas['uplevel'][package_name] = list()
                if not self.package_datas['downlevel'].__contains__(depend_item[PACKAGE_NAME]):
                    self.package_datas['downlevel'][depend_item[PACKAGE_NAME]] = list(
                    )
                self.package_datas['uplevel'][package_name].append(
                    depend_item[PACKAGE_NAME])
                self.package_datas['downlevel'][depend_item[PACKAGE_NAME]].append(
                    package_name)

    def get_depend_relation_data(self, depend, func):
        """
            Get data for different dependencies

            Args:
                depend:Each of the dependent instance objects
                       SelfBuildDep()、BuildDep()、InstallDep()、BeDependOn()
                func:Methods to query dependencies
        """

        if not depend.validate():
            return (ResponseCode.PARAM_ERROR, ResponseCode.CODE_MSG_MAP[ResponseCode.PARAM_ERROR])
        database_error = self._database_priority()
        if database_error:
            return database_error
        _package_datas = func()

        if _package_datas:
            self._relation_recombine(_package_datas)
            try:
                self._graph_data()
            except KeyError as error:
                LOGGER.logger.error(error)
                return (ResponseCode.SERVICE_ERROR, ResponseCode.CODE_MSG_MAP[ResponseCode.SERVICE_ERROR])
        return (ResponseCode.SUCCESS, ResponseCode.CODE_MSG_MAP[ResponseCode.SUCCESS])

    def parse_depend_graph(self):
        """Analyze the data that the graph depends on"""
        response_status, _msg = self.graph()
        if response_status != ResponseCode.SUCCESS:
            return (response_status, _msg, None)

        return (response_status, _msg, self.depend_package)
