#!/usr/bin/python3
"""
Registration of timed tasks
"""
from packageship.selfpkg import app
from .download_yaml import update_pkg_info


def start_tasks():
    """
        Start of timing tasks, used to register timing tasks that need to be executed

    """
    app.apscheduler.add_job(  # pylint: disable=no-member
        func=update_pkg_info, id="update_package_data", trigger="interval", seconds=30)
