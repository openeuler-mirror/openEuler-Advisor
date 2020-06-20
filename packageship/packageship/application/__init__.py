'''
   Initial operation and configuration of the flask project
'''
from flask import Flask
from flask_session import Session
from packageship.application.settings.dev import DevelopementConfig
from packageship.application.settings.pro import ProductionConfig
from packageship.libs.log import setup_log


# development and production environment configuration

CONFIG = {
    'dev': DevelopementConfig,
    'prop': ProductionConfig
}

OPERATION = None


def init_app(config_name, operation):
    '''
        Project initialization function
    '''
    app = Flask(__name__)

    config = CONFIG[config_name]

    # log configuration
    setup_log(config)

    # Load configuration items

    app.config.from_object(config)

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
