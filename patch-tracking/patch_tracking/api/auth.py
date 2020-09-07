"""
http basic auth
"""
import logging
from werkzeug.security import check_password_hash
from flask_httpauth import HTTPBasicAuth
from flask import current_app as app

logger = logging.getLogger(__name__)

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    """
    verify password
    """
    try:
        if username == app.config["USER"] and \
                check_password_hash(app.config["PASSWORD"], password):
            return username
    except ValueError as err:
        logger.error(err)
        return None
    logger.error("verify password failed")
    return None


if __name__ == "__main__":
    try:
        print(
            check_password_hash(
                " pbkdf2:sha256:150000$ClAZjafb$ec0718c193c000e70812a0709919596e7523ab581c25ea6883aadba33c2edf0d",
                "Test@123"
            )
        )
    except ValueError as err:
        print(err)
