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
The root path of the project
"""
import os
import sys

if "SETTINGS_FILE_PATH" not in os.environ:
    os.environ["SETTINGS_FILE_PATH"] = '/etc/pkgship/package.ini'


# The root directory where the system is running
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
else:
    BASE_PATH = os.path.abspath(os.path.dirname(__file__))
