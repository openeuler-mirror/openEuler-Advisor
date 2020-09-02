import unittest
import datetime
from test.base_code.my_test_runner import MyTestRunner

RUNNER = MyTestRunner()


def import_data_tests():
    """Initialize related test cases"""

    from test.test_module.init_system_tests.test_importdata import ImportData
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ImportData))

    return RUNNER.run(suite)


start_time = datetime.datetime.now()
result_4_import = import_data_tests()
stop_time = datetime.datetime.now()

print('\nA Init Test total of %s test cases were run： \nsuccessful:%s\tfailed:%s\terror:%s\n' % (
    int(result_4_import.testsRun),
    int(result_4_import.success_case_count),
    int(result_4_import.failure_case_count),
    int(result_4_import.err_case_count)
))

print('Init Test Total Time: %s' % (stop_time - start_time))
