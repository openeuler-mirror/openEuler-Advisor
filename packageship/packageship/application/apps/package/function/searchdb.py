"""
    A set for all query databases function
"""

import yaml
from flask import current_app

from packageship.libs.exception import ContentNoneException, Error
from packageship.system_config import DATABASE_SUCCESS_FILE


def db_priority():
    """
    return dbprioty
    """
    try:
        with open(DATABASE_SUCCESS_FILE, 'r', encoding='utf-8') as file_context:

            init_database_date = yaml.load(
                file_context.read(), Loader=yaml.FullLoader)
            if init_database_date is None:
                raise ContentNoneException(
                    "The content of the database initialization configuration file cannot be empty")
            init_database_date.sort(key=lambda x: x['priority'], reverse=False)
            db_list = [item.get('database_name')
                       for item in init_database_date]
            return db_list
    except (FileNotFoundError, Error) as file_not_found:
        current_app.logger.error(file_not_found)
        return None
