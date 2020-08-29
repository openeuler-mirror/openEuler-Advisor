#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
test_get_single_packages
"""
from test.base_code.read_data_base import ReadTestBase
import unittest
from packageship.application.apps.package.function.constants import ResponseCode


class TestGetMaintainers(ReadTestBase):
    """
    Maintainer list acquisition test
    """

    def test_maintainer(self):
        """
            Test the actual data sheet
        """
        response = self.client_request(
            "/lifeCycle/maintainer")
        self.response_json_format(response)
        self.assertEqual(ResponseCode.SUCCESS,
                         response.get("code"),
                         msg="Error in status code return")
        self.assertEqual(['userA', 'userB'], response.get(
            'data'), msg="The data content is incorrect")


if __name__ == '__main__':
    unittest.main()
