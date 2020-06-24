'''
    Basic configuration of flask framework
'''
import random
from packageship.libs.configutils.readconfig import ReadConfig


class Config():
    '''
        Configuration items in a formal environment
    '''
    SECRET_KEY = None

    DEBUG = False

    LOG_LEVEL = 'INFO'

    def __init__(self):

        self._read_config = ReadConfig()

        self.set_config_val()

    @classmethod
    def _random_secret_key(cls, random_len=32):
        '''
            Generate random strings
        '''
        cls.SECRET_KEY = ''.join(
            [random.choice('abcdefghijklmnopqrstuvwxyz!@#$%^&*()') for index in range(random_len)])

    @classmethod
    def _set_debug(cls, debug):
        '''
            Set the debugging mode
        '''
        if debug == 'true':
            cls.DEBUG = True

    @classmethod
    def _set_log_level(cls, log_level):
        '''
            Set the log level
        '''
        cls.LOG_LEVEL = log_level

    def set_config_val(self):
        '''
            Set the value of the configuration item
        '''
        Config._random_secret_key()

        debug = self._read_config.get_system('debug')

        if debug:
            Config._set_debug(debug)

        log_level = self._read_config.get_config('LOG', 'log_level')

        if log_level:
            Config._set_log_level(log_level)
