'''
    System exception information
'''


class Error(Exception):
    """
        Base class for ConfigParser exceptions
    """

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class ContentNoneException(Error):
    '''
        Content is empty exception
    '''

    def __init__(self, message):
        Error.__init__(self, 'No content: %r' % (message,))


class DbnameNoneException(ContentNoneException):
    '''
        Exception with empty database name
    '''

    def __init__(self, message):
        ContentNoneException.__init__(self, '%r' % (message,))


class DatabaseRepeatException(Error):
    '''
        There are duplicate exceptions in the database
    '''

    def __init__(self, message):
        Error.__init__(self, 'Database repeat: %r' % (message,))


class DataMergeException(Error):
    '''
        abnormal integration data
    '''

    def __init__(self, message):
        Error.__init__(self, 'DataMerge exception: %r' % (message,))
