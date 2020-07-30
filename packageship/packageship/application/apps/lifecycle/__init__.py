#!/usr/bin/python3
"""

"""
from flask.blueprints import Blueprint
from flask_restful import Api
from packageship.application.apps.lifecycle.url import urls
from packageship import application

lifecycle = Blueprint('lifecycle', __name__)

# init restapi
api = Api()

for view, url, operation in urls:
    if application.OPERATION and application.OPERATION in operation.keys():
        api.add_resource(view, url)


__all__ = ['lifecycle', 'api']
