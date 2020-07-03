# -*- coding:utf-8 -*-
"""
Test case of reading data
"""
from test.test_module.dependent_query_tests.test_build_depend import test_build_depend_suit
from test.test_module.packages_tests.test_packages import test_packages_suit
from test.test_module.single_package_tests.test_get_singlepack import test_get_single_package_suit
from test.test_module.repodatas_test.test_get_repodatas import test_get_repodatas_suit
from test.test_module.dependent_query_tests.test_be_depend import test_be_depend_suit


def execute_read():
    """Test case of reading data"""
    test_build_depend_suit()
    test_packages_suit()
    test_get_single_package_suit()
    test_get_repodatas_suit()
    test_be_depend_suit()


if __name__ == '__main__':
    execute_read()
