#!/usr/bin/python3
"""
Description:System exception information
Class:Error,ContentNoneException,DbnameNoneException,
    DatabaseRepeatException,DataMergeException
"""

class Error(Exception):

    """
    Description: Read the configuration file base class in the system
    Attributes:
        message:Exception information
    """
    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class ContentNoneException(Error):
    """
    Description: Content is empty exception
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, 'No content: %r' % (message,))


class DbnameNoneException(ContentNoneException):
    """
    Description: Exception with empty database name
    Attributes:
    """

    def __init__(self, message):
        ContentNoneException.__init__(self, '%r' % (message,))


class DatabaseRepeatException(Error):
    """
    Description: There are duplicate exceptions in the database
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, 'Database repeat: %r' % (message,))


class DataMergeException(Error):
    """
    Description: abnormal integration data
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, 'DataMerge exception: %r' % (message,))
