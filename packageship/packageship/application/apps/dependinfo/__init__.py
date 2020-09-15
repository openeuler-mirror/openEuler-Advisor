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
from flask.blueprints import Blueprint
from flask_restful import Api
from packageship import application
from .url import urls

dependinfo = Blueprint('dependinfo', __name__)

# init restapi
api = Api()

for view, url, operation in urls:
    if application.OPERATION and application.OPERATION in operation.keys():
        api.add_resource(view, url)


__all__ = ['dependinfo', 'api']
