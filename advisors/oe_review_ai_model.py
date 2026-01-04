#!/usr/bin/env python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2024. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/


class oe_review_ai_model:
    """AI Model configuration for openEuler Review"""

    def __init__(self, type):
        if type == "local":
            self._type = type
            self._base_url = "http://localhost:11434/api"
            self._model_name = "llama3.1:8b"
            self._method = "ollama"
        elif type == "deepseek":
            self._type = "deepseek"
            self._base_url = "https://api.deepseek.com"
            self._model_name = "deepseek-chat"
            self._api_key = ""
            self._method = "openai"
        elif type == "bailian":
            self._type = "bailian"
            self._base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self._model_name = "deepseek-v3"
            self._api_key = ""
            self._method = "openai"
        elif type == "siliconflow":
            self._type = "siliconflow"
            self._base_url = "https://api.siliconflow.cn/v1/chat/completions"
            self._model_name = "deepseek-r1"
            self._api_key = ""
            self._method = "openai"
        elif type == "no":
            self._type = "no"
            self._base_url = ""
            self._model_name = ""
            self._api_key = ""
            self._method = "no"
        else:
            self._type = type

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, new_value):
        self._type = new_value

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, new_value):
        self._base_url = new_value

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, new_value):
        self._model_name = new_value

    @property
    def api_key(self):
        if self._type != "local" and self.type != "no":
            return self._api_key
        else:
            return ""

    @api_key.setter
    def api_key(self, new_value):
        if self._type != "local" and self.type != "no":
            self._api_key = new_value
        else:
            pass # we dont need api_key for local or no

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, new_value):
        self._method = new_value