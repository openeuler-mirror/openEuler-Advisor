#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Execute all test cases
"""
import unittest
import datetime
from test.base_code.my_test_runner import MyTestRunner

RUNNER = MyTestRunner(verbosity=1)


def import_data_tests():
    """Initialize related test cases"""

    from test.test_module.init_system_tests.test_importdata import ImportData
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ImportData))

    return RUNNER.run(suite)


def read_data_tests():
    """Test cases with read operations on data"""

    from test.test_module.dependent_query_tests.test_install_depend import TestInstallDepend
    from test.test_module.dependent_query_tests.test_self_depend import TestSelfDepend
    from test.test_module.dependent_query_tests.test_be_depend import TestBeDepend
    from test.test_module.repodatas_test.test_get_repodatas import TestGetRepodatas
    from test.test_module.dependent_query_tests.test_build_depend import TestBuildDepend
    from test.test_module.packages_tests.test_packages import TestPackages
    from test.test_module.single_package_tests.test_get_singlepack import TestGetSinglePack
    suite = unittest.TestSuite()

    classes = [TestInstallDepend, TestSelfDepend, TestBeDepend,
               TestGetRepodatas, TestBuildDepend, TestPackages, TestGetSinglePack]

    for cls in classes:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(cls))
    return RUNNER.run(suite)


def write_data_tests():
    """Test cases with write operations on data"""

    from test.test_module.repodatas_test.test_delete_repodatas import TestDeleteRepodatas
    from test.test_module.single_package_tests.test_update_singlepack import TestUpdatePackage
    suite = unittest.TestSuite()

    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDeleteRepodatas))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestUpdatePackage))

    return RUNNER.run(suite)


def main():
    """Test case execution entry function"""

    start_time = datetime.datetime.now()

    result_4_import = import_data_tests()
    result_4_read = read_data_tests()
    result_4_write = write_data_tests()

    stop_time = datetime.datetime.now()

    print('\nA total of %s test cases were run： \nsuccessful:%s\tfailed:%s\terror:%s\n' % (
        int(result_4_import.testsRun) + int(result_4_read.testsRun) + int(result_4_write.testsRun),
        int(
            result_4_import.success_case_count
        ) + int(result_4_read.success_case_count) + int(result_4_write.success_case_count),
        int(
            result_4_import.failure_case_count
        ) + int(result_4_read.failure_case_count) + int(result_4_write.failure_case_count),
        int(
            result_4_import.err_case_count
        ) + int(result_4_read.err_case_count) + int(result_4_write.err_case_count)
    ))

    print('Total Time: %s' % (stop_time - start_time))


main()
