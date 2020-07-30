#!/usr/bin/python3
"""
General approach to version control tools
"""
import datetime as date
from dateutil.relativedelta import relativedelta
from packageship.libs.log import Log


class Base():
    """
        Public method to get project tags and download yaml file
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) Gecko/20100101 \
                Firefox / 50.0 '}
        self.log = Log(__name__)

    def format_date(self, date_time, month=0, format_str='%Y-%m-%d'):
        """
            Date formatting operations

        """
        _date = date.datetime.strptime(
            date_time, format_str)
        _date = _date + relativedelta(month=month)
        return _date

    def pkg_status(self, end_date):
        """
            Get package status information according to the last validity period of the package

        """
        now_date = date.datetime.now()
        maintainer_status = 'Available'
        if (end_date - now_date).days < 0:
            maintainer_status = "Overdue"
        return maintainer_status
