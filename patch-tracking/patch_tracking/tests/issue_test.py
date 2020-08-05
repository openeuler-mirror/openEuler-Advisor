# pylint: disable=R0801
'''
Automated testing of the Issue interface, GET requests
'''
import unittest
import json
from patch_tracking.app import app
from patch_tracking.api.business import create_issue
from patch_tracking.database import reset_db
from patch_tracking.api.constant import ResponseCode


class TestIssue(unittest.TestCase):
    '''
        Automated testing of the Issue interface, GET requests
    '''
    def setUp(self) -> None:
        '''
        Prepare the environment
        :return:
        '''
        self.client = app.test_client()
        reset_db.reset()

    def test_none_data(self):
        '''
        In the absence of data, the GET interface queries all the data
        :return:
        '''
        with app.app_context():

            resp = self.client.get("/issue")

            resp_dict = json.loads(resp.data)

            self.assertIn("code", resp_dict, msg="Error in data format return")
            self.assertEqual(ResponseCode.SUCCESS, resp_dict.get("code"), msg="Error in status code return")

            self.assertIn("msg", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                resp_dict.get("msg"),
                msg="Error in status code return"
            )

            self.assertIn("data", resp_dict, msg="Error in data format return")
            self.assertIsNotNone(resp_dict.get("data"), msg="Error in data information return")
            self.assertEqual(resp_dict.get("data"), [], msg="Error in data information return")

    def test_query_inserted_data(self):
        '''
        The GET interface queries existing data
        :return:
        '''
        with app.app_context():
            data_insert = {"issue": "A", "repo": "A", "branch": "A"}

            create_issue(data_insert)

            resp = self.client.get("/issue?repo=A&branch=A")

            resp_dict = json.loads(resp.data)

            self.assertIn("code", resp_dict, msg="Error in data format return")
            self.assertEqual(ResponseCode.SUCCESS, resp_dict.get("code"), msg="Error in status code return")

            self.assertIn("msg", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                resp_dict.get("msg"),
                msg="Error in status code return"
            )

            self.assertIn("data", resp_dict, msg="Error in data format return")
            self.assertIsNotNone(resp_dict.get("data"), msg="Error in data information return")
            self.assertIn(data_insert, resp_dict.get("data"), msg="Error in data information return")

    def test_find_all_data(self):
        '''
        The GET interface queries all the data
        :return:
        '''
        with app.app_context():
            data_insert_c = {"issue": "C", "repo": "C", "branch": "C"}
            data_insert_d = {"issue": "D", "repo": "D", "branch": "D"}
            create_issue(data_insert_c)
            create_issue(data_insert_d)
            resp = self.client.get("/issue")

            resp_dict = json.loads(resp.data)

            self.assertIn("code", resp_dict, msg="Error in data format return")
            self.assertEqual(ResponseCode.SUCCESS, resp_dict.get("code"), msg="Error in status code return")

            self.assertIn("msg", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                resp_dict.get("msg"),
                msg="Error in status code return"
            )

            self.assertIn("data", resp_dict, msg="Error in data format return")
            self.assertIsNotNone(resp_dict.get("data"), msg="Error in data information return")
            self.assertIn(data_insert_c, resp_dict.get("data"), msg="Error in data information return")
            self.assertIn(data_insert_d, resp_dict.get("data"), msg="Error in data information return")

    def test_find_nonexistent_data(self):
        '''
        The GET interface queries data that does not exist
        :return:
        '''
        with app.app_context():

            resp = self.client.get("/issue?repo=aa&branch=aa")

            resp_dict = json.loads(resp.data)

            self.assertIn("code", resp_dict, msg="Error in data format return")
            self.assertEqual(ResponseCode.SUCCESS, resp_dict.get("code"), msg="Error in status code return")

            self.assertIn("msg", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                resp_dict.get("msg"),
                msg="Error in status code return"
            )

            self.assertIn("data", resp_dict, msg="Error in data format return")
            self.assertIsNotNone(resp_dict.get("data"), msg="Error in data information return")
            self.assertEqual(resp_dict.get("data"), [], msg="Error in data information return")

    def test_get_error_parameters(self):
        '''
        The get interface passes in the wrong parameter
        :return:
        '''
        with app.app_context():
            data_insert = {"issue": "BB", "repo": "BB", "branch": "BB"}

            create_issue(data_insert)

            resp = self.client.get("/issue?oper=BB&chcnsrb=BB")

            resp_dict = json.loads(resp.data)
            self.assertIn("code", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.INPUT_PARAMETERS_ERROR, resp_dict.get("code"), msg="Error in status code return"
            )

            self.assertIn("msg", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.CODE_MSG_MAP.get(ResponseCode.INPUT_PARAMETERS_ERROR),
                resp_dict.get("msg"),
                msg="Error in status code return"
            )

            self.assertIn("data", resp_dict, msg="Error in data format return")
            self.assertEqual(resp_dict.get("data"), None, msg="Error in data information return")

    def test_get_interface_uppercase(self):
        '''
        The get interface uppercase
        :return:
        '''
        with app.app_context():
            data_insert = {"issue": "CCC", "repo": "CCC", "branch": "CCC"}

            create_issue(data_insert)

            resp = self.client.get("/issue?RrPo=CCC&brANch=CCC")

            resp_dict = json.loads(resp.data)

            self.assertIn("code", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.INPUT_PARAMETERS_ERROR, resp_dict.get("code"), msg="Error in status code return"
            )

            self.assertIn("msg", resp_dict, msg="Error in data format return")
            self.assertEqual(
                ResponseCode.CODE_MSG_MAP.get(ResponseCode.INPUT_PARAMETERS_ERROR),
                resp_dict.get("msg"),
                msg="Error in status code return"
            )

            self.assertIn("data", resp_dict, msg="Error in data format return")
            self.assertEqual(resp_dict.get("data"), None, msg="Error in data information return")


if __name__ == '__main__':
    unittest.main()
