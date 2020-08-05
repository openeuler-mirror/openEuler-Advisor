'''
    Response contain and code ID
'''
import json


class ResponseCode:
    """
        Description: response code to web
        changeLog:
    """

    SUCCESS = "2001"
    INPUT_PARAMETERS_ERROR = "4001"
    TRACKING_NOT_FOUND = "4002"
    ISSUE_NOT_FOUND = "4003"

    GITHUB_ADDRESS_ERROR = "5001"
    GITEE_ADDRESS_ERROR = "5002"
    GITHUB_CONNECTION_ERROR = "5003"
    GITEE_CONNECTION_ERROR = "5004"

    INSERT_DATA_ERROR = "6004"
    DELETE_DB_ERROR = "6001"
    CONFIGFILE_PATH_EMPTY = "6002"
    DIS_CONNECTION_DB = "6003"

    CODE_MSG_MAP = {
        SUCCESS: "Successful Operation!",
        INPUT_PARAMETERS_ERROR: "Please enter the correct parameters",
        TRACKING_NOT_FOUND: "The tracking you are looking for does not exist",
        ISSUE_NOT_FOUND: "The issue you are looking for does not exist",
        GITHUB_ADDRESS_ERROR: "The Github address is wrong",
        GITEE_ADDRESS_ERROR: "The Gitee address is wrong",
        GITHUB_CONNECTION_ERROR: "Unable to connect to the github",
        GITEE_CONNECTION_ERROR: "Unable to connect to the gitee",
        DELETE_DB_ERROR: "Failed to delete database",
        CONFIGFILE_PATH_EMPTY: "Initialization profile does not exist or cannot be found",
        DIS_CONNECTION_DB: "Unable to connect to the database, check the database configuration"
    }

    @classmethod
    def ret_message(cls, code, data=None):
        """
        generate response dictionary
        """
        return json.dumps({"code": code, "msg": cls.CODE_MSG_MAP[code], "data": data})

    def __str__(self):
        return 'ResponseCode'
