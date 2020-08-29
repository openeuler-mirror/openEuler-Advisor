import unittest
import datetime
from test.base_code.my_test_runner import MyTestRunner

RUNNER = MyTestRunner()


def read_data_tests():
    """Test cases with read operations on data"""
    from test.test_module.dependent_query_tests.test_install_depend import TestInstallDepend
    from test.test_module.dependent_query_tests.test_self_depend import TestSelfDepend
    from test.test_module.dependent_query_tests.test_be_depend import TestBeDepend
    from test.test_module.repodatas_test.test_get_repodatas import TestGetRepodatas
    from test.test_module.dependent_query_tests.test_build_depend import TestBuildDepend
    from test.test_module.packages_tests.test_packages import TestPackages
    from test.test_module.single_package_tests.test_get_singlepack import TestGetSinglePack
    from test.test_module.lifecycle.test_maintainer import TestGetMaintainers
    from test.test_module.lifecycle.test_downloadexcel import TestDownloadExcelFile
    from test.test_module.lifecycle.test_get_issues import TestGetIssue

    suite = unittest.TestSuite()

    classes = [TestInstallDepend, TestSelfDepend, TestBeDepend,
               TestGetRepodatas, TestBuildDepend, TestPackages,
               TestGetSinglePack, TestGetMaintainers, TestDownloadExcelFile,
               TestGetIssue]
    for cls in classes:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(cls))
    return RUNNER.run(suite)


start_time = datetime.datetime.now()
result_4_read = read_data_tests()
stop_time = datetime.datetime.now()

print('\nA Read Test total of %s test cases were run： \nsuccessful:%s\tfailed:%s\terror:%s\n' % (
    int(result_4_read.testsRun),
    int(result_4_read.success_case_count),
    int(result_4_read.failure_case_count),
    int(result_4_read.err_case_count)
))

print('Read Test Total Time: %s' % (stop_time - start_time))
