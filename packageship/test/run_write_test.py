# -*- coding:utf-8 -*-
"""Test case of writing data"""
from test.test_module.repodatas_test.test_delete_repodatas import test_delete_repodatas_suit
from test.test_module.single_package_tests.test_update_singlepack import test_updata_single_package_suit


def execute_operate():
    """Test case of writing data"""
    test_updata_single_package_suit()
    test_delete_repodatas_suit()


if __name__ == '__main__':
    execute_operate()
