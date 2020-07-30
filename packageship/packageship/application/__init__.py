#!/usr/bin/python3
"""
   Initial operation and configuration of the flask project
"""
from flask import Flask
from flask_session import Session
from flask_apscheduler import APScheduler
from packageship.application.settings import Config
from packageship.libs.log import setup_log

OPERATION = None


def init_app(operation):
    """
        Project initialization function
    """
    app = Flask(__name__)

    # log configuration
    setup_log(Config)

    # Load configuration items

    app.config.from_object(Config)

    # Register a scheduled task
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    # Open session function
    Session(app)

    global OPERATION
    OPERATION = operation

    # Register Blueprint
    from packageship.application.apps import blue_point
    for blue, api in blue_point:
        api.init_app(app)
        app.register_blueprint(blue)

    return app
