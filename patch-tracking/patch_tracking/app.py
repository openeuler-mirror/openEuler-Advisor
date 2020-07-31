"""
flask app
"""
import logging.config
import sys
from flask import Flask
from patch_tracking.api.issue import issue
from patch_tracking.api.tracking import tracking
from patch_tracking.database import db
from patch_tracking.task import task

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

app = Flask(__name__)
logger = logging.getLogger(__name__)

app.config.from_pyfile("settings.conf")


def check_settings_conf():
    """
    check settings.conf
    """
    flag = 0
    required_settings = ['LISTEN', 'GITHUB_ACCESS_TOKEN', 'GITEE_ACCESS_TOKEN', 'SCAN_DB_INTERVAL', 'USER', 'PASSWORD']
    for setting in required_settings:
        if setting in app.config:
            if not app.config[setting]:
                logger.error('%s is empty in settings.conf.', setting)
                flag = 1
        else:
            logger.error('%s not configured in settings.conf.', setting)
            flag = 1
    if flag:
        sys.exit()


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

task.job_init(app)

if __name__ == "__main__":
    app.run(ssl_context="adhoc")
