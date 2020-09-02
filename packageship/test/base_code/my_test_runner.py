#!/usr/bin/python3
"""
Inherited from unittest.TestResult，
The simple statistical function is realized.
"""
import sys
import unittest


class MyTestResult(unittest.TestResult):
    """
        Inherited from unittest.TestResult，
        The simple statistical function is realized.
    """

    def __init__(self, verbosity=0):
        super(MyTestResult, self).__init__()
        self.success_case_count = 0
        self.err_case_count = 0
        self.failure_case_count = 0
        self.verbosity = verbosity

    def addSuccess(self, test):
        """When the use case is executed successfully"""
        self.success_case_count += 1
        super(MyTestResult, self).addSuccess(test)
        sys.stderr.write('Success  ')
        sys.stderr.write(str(test))
        sys.stderr.write('\n')

    def addError(self, test, err):
        """When a code error causes a use case to fail"""
        self.err_case_count += 1
        super(MyTestResult, self).addError(test, err)
        sys.stderr.write('Error ')
        sys.stderr.write(str(test)+'\n')
        _,err_info = self.errors[-1]
        sys.stderr.write(err_info)
        sys.stderr.write('\n')

    def addFailure(self, test, err):
        """When the assertion is false"""
        self.failure_case_count += 1
        super(MyTestResult, self).addFailure(test, err)
        sys.stderr.write('Failure  ')
        sys.stderr.write(str(test) + '\n')
        _, err_info = self.failures[-1]
        sys.stderr.write(err_info)
        sys.stderr.write('\n')


class MyTestRunner():
    """
    Run All TestCases
    """

    def run(self, test):
        """run MyTestResult and return result"""
        result = MyTestResult()
        test(result)
        return result
