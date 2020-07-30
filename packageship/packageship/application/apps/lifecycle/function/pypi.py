#!/usr/bin/python3
import json
import requests
from requests.exceptions import HTTPError
from packageship.libs.exception import Error
from .base import Base


class Pypi(Base):
    """
        github version management tool related information acquisition


    """

    def __init__(self, pkg_info, base):
        super(Pypi, self).__init__()
        self._base = base
        self.pkg = pkg_info
        self.url = "https://pypi.org/pypi/{src_repos}/json".format(
            src_repos=self.pkg.src_repo)
        self.response_dict = None

    def _resp_to_json(self, response):
        """
            Parse the response content and get tags
        """
        try:
            self.response_dict = json.loads(response.text)
        except (ValueError, Error) as val_error:
            self.log.logger.error(val_error)

    def _parse_tags_content(self):
        """
            Parse the obtained tags content

        """
        try:
            self.pkg.latest_version = self.response_dict['info']['version']
            self.pkg.latest_version_time = self.response_dict[
                "releases"][self.pkg.latest_version][-1]["upload_time"]
            if self.pkg.latest_version_time:
                _end_date = self.format_date(
                    self.pkg.latest_version_time.split('T')[0], month=6)

            if self.pkg.latest_version != self.pkg.version:
                _end_date = self.format_date(self._get_publish_info(), month=3)

            self.pkg.maintainer_status = self.pkg_status(_end_date)

        except KeyError as key_error:
            self.log.logger.error(key_error)

    def _get_publish_info(self):
        """

        """
        try:
            _publish_date = self.response_dict["releases"][self.pkg.version][-1]["upload_time"]
            if _publish_date:
                _publish_date = _publish_date.split('T')[0]
            return _publish_date
        except KeyError as key_error:
            self.log.logger.error(key_error)

    def update_pkg_info(self):
        """
            Get the yaml file storing the current package information according to the package name

        """
        self._get_tags()

    def _get_tags(self):
        """
            Get information about project release
        """
        try:
            response = requests.get(self.url, headers=self._base.headers)
            if response.status_code == 200:
                self._resp_to_json(response)
            if self.response_dict:
                self._parse_tags_content()
        except HTTPError as error:
            self.log.logger.error(error)
