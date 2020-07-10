#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
InitConf
"""
import os
from configparser import ConfigParser
from packageship import system_config
import yaml


class InitConf:
    """
    InitConf
    """

    def __init__(self):
        base_path = os.path.join(os.path.dirname(system_config.BASE_PATH),
                                 "test",
                                 "common_files")
        config = ConfigParser()
        config.read(system_config.SYS_CONFIG_PATH)

        conf_path = os.path.join(base_path, "conf.yaml")

        config.set("SYSTEM", "init_conf_path", conf_path)
        config.write(open(system_config.SYS_CONFIG_PATH, "w"))

        with open(conf_path, 'r', encoding='utf-8') as f:
            origin_yaml = yaml.load(f.read(), Loader=yaml.FullLoader)

            for index, obj in enumerate(origin_yaml, 1):
                src_path = os.path.join(base_path, "db_origin",
                                        "data_{}_src.sqlite".format(str(index)))
                bin_path = os.path.join(base_path, "db_origin",
                                        "data_{}_bin.sqlite".format(str(index)))
                obj["src_db_file"] = [src_path]
                obj["bin_db_file"] = [bin_path]
            with open(conf_path, 'w', encoding='utf-8') as w_f:
                yaml.dump(origin_yaml, w_f)


# A simple method of single case model
# Prevent multiple file modifications

init_config = InitConf()
