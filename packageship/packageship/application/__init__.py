#!/usr/bin/python3
"""
   Initial operation and configuration of the flask project
"""
import sys
import threading
from flask import Flask
from flask_session import Session
from flask_apscheduler import APScheduler
from packageship import system_config
from packageship.application.settings import Config
from packageship.libs.log import setup_log
from packageship.libs.configutils.readconfig import ReadConfig

OPERATION = None


def _timed_task(app):
    """
    Timed task function
    """
    from .apps.lifecycle.function.download_yaml import update_pkg_info  # pylint: disable=import-outside-toplevel

    _readconfig = ReadConfig(system_config.SYS_CONFIG_PATH)
    try:
        _hour = int(_readconfig.get_config('TIMEDTASK', 'hour') or 3)
        _minute = int(_readconfig.get_config('TIMEDTASK', 'minute') or 0)
    except ValueError:
        _hour = 3
        _minute = 0
    else:
        if _hour < 0 or _hour > 23:
            _hour = 3
        if _minute < 0 or _minute > 59:
            _minute = 0

    app.apscheduler.add_job(  # pylint: disable=no-member
        func=update_pkg_info, id="update_package_data", trigger="cron", hour=_hour, minute=_minute)
    app.apscheduler.add_job(  # pylint: disable=no-member
        func=update_pkg_info,
        id="issue_catch",
        trigger="cron",
        hour=_hour,
        minute=_minute,
        args=(False,))


def init_app(operation):
    """
        Project initialization function
    """
    app = Flask(__name__)

    # log configuration
    app.logger.addHandler(setup_log(Config))

    # Load configuration items

    app.config.from_object(Config())

    # Register a scheduled task
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    # Open session function
    Session(app)

    global OPERATION  # pylint: disable=global-statement
    OPERATION = operation

    # Register Blueprint
    from packageship.application import apps  # pylint: disable=import-outside-toplevel
    for blue, api in apps.blue_point:
        api.init_app(app)
        app.register_blueprint(blue)

    _timed_task(app)

    return app
