#!/usr/bin/true
"""
download tar package with url
"""
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: wangchuangGG
# Create: 2020-06-27
# Description: provide a tool to download tar package with url
# ******************************************************************************/

import os
import sys
import io
import pycurl

def do_curl(url, dest=None):
    """
    Perform a curl operation for url.
    If perform failure or write to dest failure,
    the program exiting with an error.
    """
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.FAILONERROR, True)
    c.setopt(c.CONNECTTIMEOUT, 10)
    c.setopt(c.TIMEOUT, 600)
    c.setopt(c.LOW_SPEED_LIMIT, 1)
    c.setopt(c.LOW_SPEED_TIME, 10)
    buf = io.BytesIO()
    c.setopt(c.WRITEDATA, buf)
    try:
        c.perform()
    except pycurl.error as e:
        print("Unable to fetch {}: {} or tarball path is wrong".format(url, e))
        sys.exit(1)
    finally:
        c.close()

    if dest:
        try:
            with open(dest, 'wb') as fp:
                fp.write(buf.getvalue())
        except IOError as e:
            if os.path.exists(dest):
                os.unlink(dest)
            print("Unable to write to {}: {}".format(dest, e))
            sys.exit(1)

