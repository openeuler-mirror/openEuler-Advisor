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
Global environment variable value when the system is running
"""

import os

# Configuration file path for data initialization
INIT_CONF_PATH = os.path.join('/', 'etc', 'pkgship', 'conf.yaml')

# If the path of the imported database is not specified in the configuration file, the
# configuration in the system is used by default
DATABASE_FOLDER_PATH = os.path.join('/', 'var', 'run', 'pkgship_dbs')

# The database engine supported in the system is sqlite database by default
DATABASE_ENGINE_TYPE = 'sqlite'

# Port managed by the administrator, with write permission
WRITE_PORT = 8080

# Ordinary user query port, only the right to query data, no permission to write data
QUERY_PORT = 8090

# IP address path with write permission
WRITE_HOST = '127.0.0.1'

# IP address path with permission to query data
QUERY_HOST = '127.0.0.1'

# The address of the remote service, the command line can directly
# call the remote service to complete the data request
REMOTE_HOST = 'https://api.openeuler.org/pkgmanage'

# If the directory of log storage is not configured,
# it will be stored in the following directory specified by the system by default
LOG_PATH = os.path.join('/', 'var', 'log', 'pkgship')

# Logging level
# The log level option value can only be as follows
# INFO DEBUG WARNING ERROR CRITICAL
LOG_LEVEL = 'INFO'

# logging name
LOG_NAME = 'log_info.log'

# The number of dynamically created logs
# after the log file size reaches the upper limit. The default is 10 dynamically created logs
BACKUP_COUNT = 10

# The size of each log file, in bytes, the default size of a single log file is 300M
MAX_BYTES = 314572800

# Execution frequency and switch of timing tasks
# Whether to execute the switch for batch update of information such
# as the maintainer during initialization. When set to True, the maintainer
# and other information will be updated when the scheduled task starts
# to execute. When it is set to False, it will be updated when the scheduled
# task is executed. , Does not update information such as maintainers and maintenance levels

OPEN = True

# The time point at which the timing task is executed in a cycle.
# Every day is a cycle, and the time value can only be any integer period between 0 and 23
HOUR = 3

# Recurring timing task starts to execute the task at the current time point.
# The value range of this configuration item is an integer between 0 and 59
MINUTE = 0

# Configuration during the life cycle for tag information, issue and other information acquisition
# The yaml address of each package is stored in the remote address, which can be
# a remote warehouse address or the address of a static resource service
WAREHOUSE_REMOTE = 'https://gitee.com/openeuler/openEuler-Advisor/raw/master/upstream-info/'

# When performing timing tasks, you can open multi-threaded execution, and you can set
# the number of threads in the thread pool according to the configuration of the server

POOL_WORKERS = 10

# The main body of the warehouse, the owner of the warehouse
# When this value is not set, the system will default to src-openeuler
WAREHOUSE = 'src-openeuler'

# The address of the Redis cache server can be either a published
# domain or an IP address that can be accessed normally
# The link address defaults to 127.0.0.1
# redis_host = 127.0.0.1

REDIS_HOST = '127.0.0.1'

# Redis cache server link port number, default is 6379
REDIS_PORT = 6379

# Maximum number of connections allowed by RedIS server at one time

REDIS_MAX_CONNECTIONS = 10
