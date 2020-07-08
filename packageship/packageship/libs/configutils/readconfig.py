#!/usr/bin/python3
'''
    Read the base class of the configuration file in the system
    which mainly includes obtaining specific node values
    and obtaining arbitrary node values
'''
import configparser
from configparser import NoSectionError
from configparser import NoOptionError
from packageship.system_config import SYS_CONFIG_PATH


class ReadConfig:
    '''
        Read the configuration file base class in the system
    '''

    def __init__(self):
        self.conf = configparser.ConfigParser()
        self.conf.read(SYS_CONFIG_PATH)

    def get_system(self, param):
        '''
            Get any data value under the system configuration node
        '''
        if param:
            try:
                return self.conf.get("SYSTEM", param)
            except NoSectionError:
                return None
            except NoOptionError:
                return None
        return None

    def get_database(self, param):
        '''
            Get any data value under the database configuration node
        '''
        if param:
            try:
                return self.conf.get("DATABASE", param)
            except NoSectionError:
                return None
            except NoOptionError:
                return None
        return None

    def get_config(self, node, param):
        '''
            Get configuration data under any node
        '''
        if all([node, param]):
            try:
                return self.conf.get(node, param)
            except NoSectionError:
                return None
            except NoOptionError:
                return None
        return None
