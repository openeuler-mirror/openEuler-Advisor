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
Use redis cache to install dependencies, compile dependencies
be dependent, and self-compile dependencies
"""
import threading
import hashlib
import json
from importlib import import_module
from functools import partial
from redis import Redis, ConnectionPool


REDIS_CONN = Redis(connection_pool=ConnectionPool(
    host='192.168.205.128', port=6379, max_connections=10, decode_responses=True))
lock = threading.Lock()


def hash_key(encrypt_obj):
    """
        After sorting the values of the dictionary type, calculate the md5 encrypted hash value
    """
    if isinstance(encrypt_obj, dict):
        encrypt_obj = sorted(encrypt_obj)
    md5 = hashlib.md5()
    md5.update(str(encrypt_obj).encode('utf-8'))
    return md5.hexdigest()


def import_string(module_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = module_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" %
                          module_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        ) from err


def _query_depend(query_parameter, depend_relation_str):
    """
        Query package dependencies
    """
    depend_relation_key = hash_key(query_parameter)
    if REDIS_CONN.exists(depend_relation_key):
        depend_relation = REDIS_CONN.get(depend_relation_key)
        if depend_relation:
            depend_relation = json.loads(depend_relation, encoding='utf-8')
        return depend_relation
    # Use thread lock to safely write data in redis
    lock.acquire()
    if not REDIS_CONN.exists(depend_relation_key + '_flag'):
        REDIS_CONN.set(depend_relation_key + '_flag', 'True')
    else:
        REDIS_CONN.set(depend_relation_key + '_flag', 'False')
    REDIS_CONN.expire(depend_relation_key + '_flag', 600)
    flag = REDIS_CONN.get(depend_relation_key + '_flag')
    lock.release()
    if flag != 'True':
        return "LOADING"
    # query depend relation
    try:
        depend_relation = import_string(depend_relation_str)
    except ImportError:
        pass
    else:
        _depend_result = depend_relation.query_depend_relation(query_parameter)
        REDIS_CONN.set(depend_relation_key, json.dumps(_depend_result))
        return _depend_result
    finally:
        REDIS_CONN.delete(depend_relation_key + '_flag')


self_build = partial(
    _query_depend,
    depend_relation_str="packageship.application.apps.dependinfo.function.singlegraph.SelfBuildDep")
install_depend = partial(
    _query_depend,
    depend_relation_str="packageship.application.apps.dependinfo.function.singlegraph.InstallDep")
build_depend = partial(
    _query_depend,
    depend_relation_str="packageship.application.apps.dependinfo.function.singlegraph.BuildDep")
bedepend = partial(
    _query_depend,
    depend_relation_str="packageship.application.apps.dependinfo.function.singlegraph.BeDependOn")
