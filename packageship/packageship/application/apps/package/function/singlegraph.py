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
from ..serialize import BeDependSchema, BuildDependSchema, InstallDependSchema, SelfDependSchema


LEVEL = 2
LEVEL_RADIUS = 120
NODE_SIZE = 10


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

    def __call__(self):
        pass


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

    def __call__(self):
        pass


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

    def __call__(self):
        pass


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
        bedepend = BeDependSchema().validate(self.query_parameter)
        if bedepend:
            return False
        return True

    def __call__(self):
        pass


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

    def parse_depend_graph(self):
        """Analyze the data that the graph depends on"""
        self.graph()
