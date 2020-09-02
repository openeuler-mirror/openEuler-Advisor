"""
flask app
"""
import logging.config
import os
import sys
from flask import Flask
from patch_tracking.api.issue import issue
from patch_tracking.api.tracking import tracking
from patch_tracking.database import db
from patch_tracking.task import task

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

app = Flask(__name__)
logger = logging.getLogger(__name__)


def check_settings_conf():
    """
    check settings.conf
    """
    setting_error = False
    required_settings = ['LISTEN', 'GITHUB_ACCESS_TOKEN', 'GITEE_ACCESS_TOKEN', 'SCAN_DB_INTERVAL', 'USER', 'PASSWORD']
    for setting in required_settings:
        if setting in app.config:
            if not app.config[setting]:
                logger.error('%s is empty in settings.conf.', setting)
                setting_error = True
            else:
                if setting == "LISTEN" and int(app.config[setting].split(":")[1]) > 65535:
                    logger.error('LISTEN error: illegal port number in /etc/patch-tracking/settings.conf.')
                    setting_error = True
                if setting == "SCAN_DB_INTERVAL" and int(app.config[setting]) <= 0:
                    logger.error(
                        'SCAN_DB_INTERVAL error: must be greater than zero in /etc/patch-tracking/settings.conf.'
                    )
                    setting_error = True
        else:
            logger.error('%s not configured in settings.conf.', setting)
            setting_error = True
    if setting_error:
        sys.exit()


settings_file = os.path.join(os.path.abspath(os.curdir), "settings.conf")
app.config.from_pyfile(settings_file)
check_settings_conf()

GITHUB_ACCESS_TOKEN = app.config['GITHUB_ACCESS_TOKEN']
GITEE_ACCESS_TOKEN = app.config['GITEE_ACCESS_TOKEN']
SCAN_DB_INTERVAL = app.config['SCAN_DB_INTERVAL']

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
app.config['ERROR_404_HELP'] = False
app.config['RESTX_MASK_SWAGGER'] = False
app.config['SCHEDULER_EXECUTORS'] = {'default': {'type': 'threadpool', 'max_workers': 100}}

app.register_blueprint(issue, url_prefix="/issue")
app.register_blueprint(tracking, url_prefix="/tracking")

db.init_app(app)

task.init(app)

if __name__ == "__main__":
    app.run(ssl_context="adhoc")
