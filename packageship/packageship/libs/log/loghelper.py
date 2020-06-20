'''
    Configure log function
'''

import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from packageship.system_config import LOG_FOLDER_PATH
from packageship.libs.configutils.readconfig import ReadConfig


READCONFIG = ReadConfig()


def setup_log(Config=None):

    if Config:

        logging.basicConfig(level=Config.LOG_LEVEL)
    else:
        logging.basicConfig(level='INFO')
    path = READCONFIG.get_system('log_path')
    if path is None:
        path = os.path.join(LOG_FOLDER_PATH, 'loginfo.log')
    if not os.path.exists(path):
        try:
            os.makedirs(os.path.split(path)[0])
        except FileExistsError as file_exists:
            pathlib.Path(path).touch()

    file_log_handler = RotatingFileHandler(
        path, maxBytes=1024 * 1024 * 300, backupCount=10)

    formatter = logging.Formatter(
        '%(levelname)s %(filename)s:%(lineno)d %(message)s')

    file_log_handler.setFormatter(formatter)

    logging.getLogger().addHandler(file_log_handler)


class Log():

    def __init__(self, name=__name__, path=None, level='ERROR'):
        self.__name = name
        self.__path = path
        if self.__path is None:
            self.__path = READCONFIG.get_system('log_path')
            if self.__path is None:
                self.__path = os.path.join(LOG_FOLDER_PATH, 'loginfo.log')
        else:
            self.__path = os.path.join(LOG_FOLDER_PATH, path)

        if not os.path.exists(self.__path):
            try:
                os.makedirs(os.path.split(self.__path)[0])
            except FileExistsError:
                pathlib.Path(self.__path).touch()
        self.__level = level
        self.__logger = logging.getLogger(self.__name)
        self.__logger.setLevel(self.__level)

    def __ini_handler(self):
        # self.__stream_handler = logging.StreamHandler()
        self.__file_handler = logging.FileHandler(
            self.__path, encoding='utf-8')

    def __set_handler(self, level='DEBUG'):
        # self.__stream_handler.setLevel(level)
        self.__file_handler.setLevel(level)
        # self.__logger.addHandler(self.__stream_handler)
        self.__logger.addHandler(self.__file_handler)

    def __set_formatter(self):
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(filename)s-[line:%(lineno)d]'
                                      '-%(levelname)s-[ log details ]: %(message)s',
                                      datefmt='%a, %d %b %Y %H:%M:%S')
        # self.__stream_handler.setFormatter(formatter)
        self.__file_handler.setFormatter(formatter)

    def __close_handler(self):
        # self.__stream_handler.close()
        self.__file_handler.close()

    @property
    def logger(self):

        self.__ini_handler()
        self.__set_handler()
        self.__set_formatter()
        self.__close_handler()
        return self.__logger
