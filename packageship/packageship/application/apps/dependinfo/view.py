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
from flask import jsonify
from flask_restful import Resource

from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.function.searchdb import db_priority


class DataBaseInfo(Resource):
    """
     Get  the database name of all packages
    """

    def get(self):
        """
        Returns: name_list: database name list
        """
        name_list = db_priority()
        if not name_list:
            return jsonify(
                ResponseCode.response_json(ResponseCode.NOT_FOUND_DATABASE_INFO)
            )
        return jsonify(
            ResponseCode.response_json(ResponseCode.SUCCESS, data=name_list)
        )