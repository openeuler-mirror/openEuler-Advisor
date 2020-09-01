#!/usr/bin/python3
import unittest


class TestBase(unittest.TestCase):
    """
        unittest unit test basic class
    """

    def response_json_format(self, response):
        """
            Json data judgment of corresponding content
        """
        self.assertIn("code", response, msg="Error in data format return")
        self.assertIn("msg", response, msg="Error in data format return")
        self.assertIn("data", response, msg="Error in data format return")
