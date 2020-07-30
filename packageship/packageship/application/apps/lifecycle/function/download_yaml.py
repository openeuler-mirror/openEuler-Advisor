#!/usr/bin/python3
"""
Dynamically obtain the content of the yaml file \
that saves the package information, periodically \
obtain the content and save it in the database
"""
from concurrent.futures import ThreadPoolExecutor
import requests
import yaml
from sqlalchemy.exc import SQLAlchemyError
from requests.exceptions import HTTPError
from packageship.application.models.package import packages
from packageship.application.models.package import packages_issue
from packageship.libs.dbutils import DBHelper
from packageship.libs.exception import Error, ContentNoneException
from .base import Base


class ParseYaml():
    """
    Description: Download the contents of the yaml file

    Attributes:
        base: base class instance
        pkg: Specific package data
        _table_name: The name of the data table to be operated
        _owner: The address of the corporate warehouse
        _repo: The address of the source code repository
        openeuler_advisor_url: Get the warehouse address of the yaml file
        _yaml_content: The content of the yaml file
    """

    def __init__(self, pkg_info, base, table_name):
        self.base = base
        self.pkg = pkg_info
        self._table_name = table_name
        self._owner = "src-openeuler"
        self._repo = self.pkg.name
        self.openeuler_advisor_url = \
            'https://gitee.com/openeuler/openEuler-Advisor/raw/master/upstream-info/{name}.yaml'\
            .format(name=pkg_info.name)
        self._yaml_content = None

    def update_pkg_info(self):
        """
            Download the contents of the yaml file

        """
        if self._openeuler_advisor_exists_yaml():
            self._save_to_database()
        else:
            msg = "The yaml information of the %s package has not been\
                obtained yet" % self.pkg.name
            self.base.log.logger.warning(msg)

    def _read_yaml_content(self, url):
        """

        """
        try:
            response = requests.get(
                url, headers=self.base.headers)
            if response.status_code == 200:
                self._yaml_content = yaml.safe_load(response.content)

        except HTTPError as error:
            self.base.log.logger.error(error)

    def _openeuler_advisor_exists_yaml(self):
        """
            Determine whether there is a yaml file with the current \
                package name under the openeuler-advisor project

        """
        self._read_yaml_content(self.openeuler_advisor_url)
        if self._yaml_content:
            return True
        return False

    def _save_to_database(self):
        """
            Save the acquired yaml file information to the database

            Raises:
                ContentNoneException: The added entity content is empty
                Error: An error occurred during data addition
        """
        self._parse_warehouse_info()
        tags = self._yaml_content.get('git_tag', None)
        self._parse_tags_content(tags)
        # TODO 获取issue列表数据，然后进行保存
        # Save data to the database
        try:
            with DBHelper(db_name="lifecycle") as database:
                database.add(self.pkg)
                database.batch_add([], packages_issue)
        except (Error, ContentNoneException, SQLAlchemyError) as error:
            self.base.log.logger.error(error)

    def _parse_warehouse_info(self):
        """
            Parse the warehouse information in the yaml file

        """
        if self._yaml_content:
            self.pkg.version_control = self._yaml_content.get(
                'version_control')
            self.pkg.src_repo = self._yaml_content.get('src_repo')
            self.pkg.tag_prefix = self._yaml_content.get('tag_prefix')

    def _parse_tags_content(self, tags):
        """
            Parse the obtained tags content

        """
        try:
            # Integrate tags information into key-value pairs
            _tags = [(tag.split()[0], tag.split()[1]) for tag in tags]
            _tags = sorted(_tags, key=lambda x: x[0], reverse=True)
            self.pkg.latest_version = _tags[0][1]
            self.pkg.latest_version_time = _tags[0][0]
            _end_time = self.base.format_date(
                self.pkg.latest_version_time, month=6)
            if self.pkg.latest_version != self.pkg.version:
                _end_time = self.base.format_date(
                    self.pkg.latest_version_time, month=3)
            self.pkg.maintainer_status = self.base.pkg_status(
                _end_time)
            self.pkg.end_time = _end_time.strftime("%Y-%m-%d")

        except (IndexError,) as index_error:
            self.base.log.logger.error(index_error)


def update_pkg_info():
    """
        Update the information of the upstream warehouse in the source package

    """
    try:
        base_control = Base()
        pool = ThreadPoolExecutor(max_workers=10)
        with DBHelper(db_name="lifecycle") as database:
            for table_name in filter(lambda x: x.endswith("_pkg"), database.engine.table_names()):
                cls_model = type("packages", (packages, DBHelper.BASE), {
                    '__tablename__': table_name})
                # Query a specific table
                for package_item in database.session.query(cls_model).all():
                    parse_yaml = ParseYaml(
                        pkg_info=package_item, base=base_control, table_name=table_name)
                    pool.submit(parse_yaml.update_pkg_info)
        pool.shutdown()
    except SQLAlchemyError as error_msg:
        base_control.log.logger.error(error_msg)
