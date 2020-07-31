"""
http basic auth
"""
from werkzeug.security import check_password_hash
from flask_httpauth import HTTPBasicAuth
from flask import current_app as app

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    """
    verify password
    """
    if username == app.config["USER"] and \
            check_password_hash(app.config["PASSWORD"], password):
        return username
    return None
