# -*- coding:utf-8 -*-

def execute_operate():
    # put import_data_test first
    from test.test_module.init_system_tests.test_importdata import test_import_data_suit
    test_import_data_suit()


    # Import test cases and calls related to query database
    from test.test_module.dependent_query_tests.test_build_depend import test_build_depend_suit
    from test.test_module.packages_tests.test_packages import test_packages_suit
    from test.test_module.dependent_query_tests.test_be_depend import test_be_depend_suit
    test_build_depend_suit()
    test_packages_suit()
    test_be_depend_suit()
    # Import test cases and calls related to the operation database
    # like update database


if __name__ == '__main__':
    execute_operate()
