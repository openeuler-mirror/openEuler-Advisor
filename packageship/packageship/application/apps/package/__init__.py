from flask.blueprints import Blueprint
from flask_restful import Api
from packageship.application.apps.package.url import urls
from packageship.application import OPERATION

package = Blueprint('package', __name__)

# init restapi
api = Api()

for view, url, operation in urls:
    if OPERATION and OPERATION in operation.keys():
        api.add_resource(view, url)


__all__ = ['package', 'api']
