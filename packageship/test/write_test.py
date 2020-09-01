#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Execute all test cases
"""
import unittest
import datetime
from test.base_code.my_test_runner import MyTestRunner

RUNNER = MyTestRunner()


def write_data_tests():
    """Test cases with write operations on data"""

    from test.test_module.repodatas_test.test_delete_repodatas import TestDeleteRepodatas
    from test.test_module.single_package_tests.test_update_singlepack import TestBatchUpdatePackage
    from test.test_module.lifecycle.test_issue_catch import TestIssueCatch
    suite = unittest.TestSuite()

    classes = [
        # TestDeleteRepodatas,
        # TestBatchUpdatePackage,
        TestIssueCatch
    ]
    for cls in classes:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(cls))
    return RUNNER.run(suite)


start_time = datetime.datetime.now()

result_4_write = write_data_tests()

stop_time = datetime.datetime.now()

print('\nA Write Test total of %s test cases were run： \nsuccessful:%s\tfailed:%s\terror:%s\n' % (
    int(result_4_write.testsRun),
    int(result_4_write.success_case_count),
    int(result_4_write.failure_case_count),
    int(result_4_write.err_case_count)
))

print('Write Test Total Time: %s' % (stop_time - start_time))
