#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
System configuration file and default configuration file integration
"""
import os
import configparser

from packageship.libs.exception import Error
from . import global_config


USER_SETTINGS_FILE_PATH = 'SETTINGS_FILE_PATH'


class PreloadingSettings():
    """
    The system default configuration file and the configuration
    file changed by the user are lazily loaded.
    """
    _setting_container = None

    def _preloading(self):
        """
        Load the default configuration in the system and the related configuration
        of the user, and overwrite the default configuration items of the system
        with the user's configuration data
        """
        settings_file = os.environ.get(USER_SETTINGS_FILE_PATH)
        if not settings_file:
            raise Error(
                "The system does not specify the user configuration"
                "that needs to be loaded:" % USER_SETTINGS_FILE_PATH)

        self._setting_container = Configs(settings_file)

    def __getattr__(self, name):
        """
            Return the value of a setting and cache it in self.__dict__
        """
        if self._setting_container is None:
            self._preloading()
        value = getattr(self._setting_container, name, None)
        self.__dict__[name] = value
        return value

    def __setattr__(self, name, value):
        """
            Set the configured value and re-copy the value cached in __dict__
        """
        if name is None:
            raise KeyError("The set configuration key value cannot be empty")
        if name == '_setting_container':
            self.__dict__.clear()
            self.__dict__["_setting_container"] = value
        else:
            self.__dict__.pop(name, None)
        if self._setting_container is None:
            self._preloading()
        setattr(self._setting_container, name, value)

    def __delattr__(self, name):
        """
            Delete a setting and clear it from cache if needed
        """
        if name is None:
            raise KeyError("The set configuration key value cannot be empty")

        if self._setting_container is None:
            self._preloading()
        delattr(self._setting_container, name)
        self.__dict__.pop(name, None)

    @property
    def config_ready(self):
        """
            Return True if the settings have already been configured
        """
        return self._setting_container is not None


class Configs():
    """
        The system's default configuration items and the user's
        configuration items are integrated
    """

    def __init__(self, settings_file):
        for config in dir(global_config):
            if not config.startswith('_'):
                setattr(self, config, getattr(global_config, config))

        # Load user's configuration
        self._conf_parser = configparser.ConfigParser()
        self._conf_parser.read(settings_file)

        for section in self._conf_parser.sections():
            for option in self._conf_parser.items(section):
                try:
                    _config_value = option[1]
                    _key = option[0]
                except IndexError:
                    pass
                else:
                    if not _config_value:
                        continue
                    if _config_value.isdigit():
                        _config_value = int(_config_value)
                    elif _config_value.lower() in ('true', 'false'):
                        _config_value = bool(_config_value)
                    setattr(self, _key.upper(), _config_value)


configuration = PreloadingSettings()
