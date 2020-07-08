'''
Logging related
'''
import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from packageship.system_config import LOG_FOLDER_PATH
from packageship.libs.configutils.readconfig import ReadConfig

READCONFIG = ReadConfig()


def setup_log(config=None):
    '''
        Log logging in the context of flask
    '''
    if config:
        logging.basicConfig(level=config.LOG_LEVEL)
    else:
        _level = READCONFIG.get_config('LOG', 'log_level')
        if _level is None:
            _level = 'INFO'
        logging.basicConfig(level=_level)
    path = READCONFIG.get_config('LOG', 'log_path')
    if path is None:
        log_name = READCONFIG.get_config('LOG', 'log_name')
        if log_name is None:
            log_name = 'log_info.log'
        path = os.path.join(LOG_FOLDER_PATH, log_name)
    if not os.path.exists(path):
        try:
            os.makedirs(os.path.split(path)[0])
        except FileExistsError:
            pathlib.Path(path).touch()

    file_log_handler = RotatingFileHandler(
        path, maxBytes=1024 * 1024 * 300, backupCount=10)

    formatter = logging.Formatter(
        '%(levelname)s %(filename)s:%(lineno)d %(message)s')

    file_log_handler.setFormatter(formatter)

    logging.getLogger().addHandler(file_log_handler)


class Log():
    '''
        General log operations
    '''

    def __init__(self, name=__name__, path=None):
        self.__name = name
        self.__path = path
        self.__file_handler = None
        if self.__path is None:
            self.__path = READCONFIG.get_system('log_path')
            log_name = READCONFIG.get_config('LOG', 'log_name')
            if log_name is None:
                log_name = 'log_info.log'
            if self.__path is None:
                self.__path = os.path.join(LOG_FOLDER_PATH, log_name)
        else:
            self.__path = os.path.join(LOG_FOLDER_PATH, path)

        if not os.path.exists(self.__path):
            try:
                os.makedirs(os.path.split(self.__path)[0])
            except FileExistsError:
                pathlib.Path(self.__path).touch()
        self.__level = READCONFIG.get_config('LOG', 'log_level')
        if self.__level is None:
            self.__level = 'INFO'
        self.__logger = logging.getLogger(self.__name)
        self.__logger.setLevel(self.__level)

    def __ini_handler(self):
        # self.__stream_handler = logging.StreamHandler()
        self.__file_handler = logging.FileHandler(
            self.__path, encoding='utf-8')

    def __set_handler(self):
        # self.__stream_handler.setLevel(level)
        self.__file_handler.setLevel(self.__level)
        # self.__logger.addHandler(self.__stream_handler)
        self.__logger.addHandler(self.__file_handler)

    def __set_formatter(self):
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(filename)s-[line:%(lineno)d]'
                                      '-%(levelname)s-[ log details ]: %(message)s',
                                      datefmt='%a, %d %b %Y %H:%M:%S')
        # self.__stream_handler.setFormatter(formatter)
        self.__file_handler.setFormatter(formatter)

    def close_handler(self):
        '''
            Turn off log processing
        '''
        # self.__stream_handler.close()
        self.__file_handler.close()

    @property
    def logger(self):
        '''
            Get logs
        '''
        self.__ini_handler()
        self.__set_handler()
        self.__set_formatter()
        self.close_handler()
        return self.__logger
