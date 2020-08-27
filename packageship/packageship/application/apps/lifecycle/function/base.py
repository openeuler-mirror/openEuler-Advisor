#!/usr/bin/python3
"""
General approach to version control tools
"""
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
