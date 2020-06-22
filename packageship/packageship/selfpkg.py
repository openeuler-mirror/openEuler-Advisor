'''
    Entry for project initialization and service startupc
'''
import os
from flask_script import Manager
from packageship.libs.exception import Error
from packageship.libs.configutils.readconfig import ReadConfig

try:
    from packageship.system_config import SYS_CONFIG_PATH
    if not os.path.exists(SYS_CONFIG_PATH):
        raise FileNotFoundError(
            'the system configuration file does not exist and the log cannot be started')
except FileNotFoundError as file_not_found:
    from packageship.libs.log.loghelper import Log
    Log(__name__).logger.error(file_not_found)
    raise Exception(
        'the system configuration file does not exist and the log cannot be started')

from packageship.application import init_app
try:
    app = init_app('query')
except Error as error:
    raise Exception('Service failed to start')
else:
    from packageship.application.app_global import identity_verification


@app.before_request
def before_request():
    if not identity_verification():
        return 'No right to perform operation'


if __name__ == "__main__":
    _readconfig = ReadConfig()
    port = _readconfig.get_system('query_port')
    addr = _readconfig.get_system('query_ip_addr')
    app.run(port=port, host=addr)
