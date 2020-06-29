'''
System-level file configuration, mainly configure
the address of the operating environment, commonly used variables, etc.
'''

import os
import sys


# The root directory where the system is running
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
else:
    BASE_PATH = os.path.abspath(os.path.dirname(__file__))

# system configuration file path

SYS_CONFIG_PATH = os.path.join('/', 'etc', 'pkgship', 'package.ini')

# data file after successful data import

# DATABASE_SUCCESS_FILE = os.path.join(
#     BASE_PATH, 'application', 'initsystem', 'import_success_databse.yaml')

DATABASE_SUCCESS_FILE = os.path.join(
    '/', 'var', 'run', 'database_file_info.yaml')

# If the path of the imported database is not specified in the configuration file, the
# configuration in the system is used by default
DATABASE_FOLDER_PATH = os.path.join('/', 'var', 'run', 'pkgship_dbs')


# If the directory of log storage is not configured,
# it will be stored in the following directory specified by the system by default
LOG_FOLDER_PATH = os.path.join('/', 'var', 'log', 'pkgship')
