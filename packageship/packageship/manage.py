#!/usr/bin/python3
"""
Description: Entry for project initialization and service startupc
"""
import os

try:
    from packageship.application import init_app
    if not os.path.exists(os.environ.get('SETTINGS_FILE_PATH')):
        raise RuntimeError(
            'System configuration file:%s' % os.environ.get(
                'SETTINGS_FILE_PATH'),
            'does not exist, software service cannot be started')
    app = init_app("write")
except ImportError as error:
    raise RuntimeError(
        "The package management software service failed to start : %s" % error)
else:
    from packageship.application.app_global import identity_verification
    from packageship.libs.conf import configuration


@app.before_request
def before_request():
    """
    Description: Global request interception
    """
    if not identity_verification():
        return 'No right to perform operation'


if __name__ == "__main__":

    port = configuration.WRITE_PORT
    addr = configuration.WRITE_IP_ADDR
    app.run(port=port, host=addr)
