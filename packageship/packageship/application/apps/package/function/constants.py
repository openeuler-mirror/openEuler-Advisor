#!/usr/bin/python3
"""
Description: Response contain and code ID
class: ListNode, ResponseCode
"""


class ListNode():
    """
    Description: Dethe structure of dict:
    {package_name: [source_name,
                dbname,
                [[parent_node_1, depend_type],[parent_node_2, depend_type],...]],
                check_tag]
    }
    changeLog:
    """

    SOURCE_NAME = 0
    VERSION = 1
    DBNAME = 2
    PARENT_LIST = 3
    # FOR PARENT LIST:
    PARENT_NODE = 0
    DEPEND_TYPE = 1

# response code


class ResponseCode():
    """
    Description: response code to web
    changeLog:
    """
    # Four digits are common status codes
    SUCCESS = "2001"
    PARAM_ERROR = "4001"
    DB_NAME_ERROR = "4002"
    PACK_NAME_NOT_FOUND = "4003"
    CONNECT_DB_ERROR = "4004"
    INPUT_NONE = "4005"
    FILE_NOT_FOUND = "4006"
    SPECIFIED_FILE_NOT_EXIST = "4007"
    UPDATA_OR_ADD_DATA_FAILED = "4008"
    TABLE_NAME_NOT_EXIST = "4009"
    UPDATA_DATA_FAILED = "4010"
    # Database operation module error status code
    DELETE_DB_ERROR = "40051"
    SERVICE_ERROR = "50000"
    CONFIGFILE_PATH_EMPTY = "50001"
    FAILED_CREATE_DATABASE_TABLE = "50002"
    TYPE_ERROR = "50003"
    DATA_MERGE_ERROR = "50004"
    FILE_NOT_FIND_ERROR = "50005"
    DIS_CONNECTION_DB = "50006"
    NO_PACKAGES_TABLE = "60001"
    DATABASE_NOT_FOUND = "60002"
    TABLE_NAME_NOT_EXIST_IN_DATABASE = "60003"
    YAML_FILE_ERROR = " 70001"
    EMPTY_FOLDER = "70002"

    CODE_MSG_MAP = {
        SUCCESS: "Successful Operation!",
        PARAM_ERROR: "Parameter error, please check the parameter and query again.",
        DB_NAME_ERROR: "Database does not exist! Please check the database name",
        PACK_NAME_NOT_FOUND: "Sorry! The querying package does not exist in the databases",
        CONNECT_DB_ERROR: "Failed to Connect the database! "
                          "Please check the database connection",
        INPUT_NONE: "The input is None, please check the input value.",
        FILE_NOT_FOUND: "Database import success file does not exist",
        DELETE_DB_ERROR: "Failed to delete database",
        CONFIGFILE_PATH_EMPTY: "Initialization profile does not exist or cannot be found",
        FAILED_CREATE_DATABASE_TABLE: "Failed to create database or table",
        TYPE_ERROR: "The source code and binary path types in the initialization file are abnormal",
        DATA_MERGE_ERROR: "abnormal multi-file database integration",
        FILE_NOT_FIND_ERROR: "system initialization configuration file does not exist",
        DIS_CONNECTION_DB: "Unable to connect to the database, check the database configuration",
        SERVICE_ERROR: "An exception occurred in the system, please try again later",
        SPECIFIED_FILE_NOT_EXIST: "The specified file does not exist",
        NO_PACKAGES_TABLE: "There is no packages table in the database",
        UPDATA_OR_ADD_DATA_FAILED: "Failed to update or add data",
        DATABASE_NOT_FOUND: "There is no such database in the system",
        TABLE_NAME_NOT_EXIST: "There is no such table in the database",
        UPDATA_DATA_FAILED: "Failed to update data",
        TABLE_NAME_NOT_EXIST_IN_DATABASE: "the table name dose not match the existed database",
        YAML_FILE_ERROR: "Data error in yaml file",
        EMPTY_FOLDER: "This is an empty folder, no yaml file"
    }

    @classmethod
    def response_json(cls, code, data=None, msg=None):
        """
        Description: classmethod
        """
        try:
            _msg = cls.CODE_MSG_MAP[code]
        except KeyError:
            _msg = msg
        return {
            "code": code,
            "msg": _msg,
            "data": data
        }

    def __str__(self):
        return 'ResponseCode'
