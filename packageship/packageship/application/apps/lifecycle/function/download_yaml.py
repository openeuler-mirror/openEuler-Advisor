#!/usr/bin/python3
"""
Dynamically obtain the content of the yaml file \
that saves the package information, periodically \
obtain the content and save it in the database
"""
import copy
from concurrent.futures import ThreadPoolExecutor
import datetime as date
import requests
import yaml
from retrying import retry
from sqlalchemy.exc import SQLAlchemyError
from requests.exceptions import HTTPError
from packageship import system_config
from packageship.application.models.package import Packages
from packageship.application.models.package import PackagesMaintainer
from packageship.libs.dbutils import DBHelper
from packageship.libs.exception import Error, ContentNoneException
from packageship.libs.configutils.readconfig import ReadConfig
from .base import Base
from .gitee import Gitee
from .concurrent import ProducerConsumer


class ParseYaml():
    """
    Description: Analyze the downloaded remote yaml file, obtain the tags
    and maintainer information in the yaml file, and save the obtained
    relevant information into the database

    Attributes:
        base: base class instance
        pkg: Specific package data
        _table_name: The name of the data table to be operated
        openeuler_advisor_url: Get the warehouse address of the yaml file
        _yaml_content: The content of the yaml file
    """

    def __init__(self, pkg_info, base, table_name):
        self.base = base
        self.pkg = pkg_info
        self._table_name = table_name
        self.openeuler_advisor_url = self._path_stitching(pkg_info.name)
        self._yaml_content = None
        self.timed_task_open = self._timed_task_status()
        self.producer_consumer = ProducerConsumer()

    def _timed_task_status(self):
        """
            The open state of information such as the maintainer in the scheduled task
        """
        _timed_task_status = True
        _readconfig = ReadConfig(system_config.SYS_CONFIG_PATH)
        open_status = _readconfig.get_config('TIMEDTASK', 'open')
        if open_status not in ('True', 'False'):
            self.base.log.logger.error(
                'Wrong setting of the open state value of the scheduled task')
        if open_status == 'False':
            self.timed_task_open = False
        return _timed_task_status

    def _path_stitching(self, pkg_name):
        """
            The path of the remote service call
        """
        _readconfig = ReadConfig(system_config.SYS_CONFIG_PATH)
        _remote_url = _readconfig.get_config('LIFECYCLE', 'warehouse_remote')
        if _remote_url is None:
            _remote_url = 'https://gitee.com/openeuler/openEuler-Advisor/raw/master/upstream-info/'
        return _remote_url + '{pkg_name}.yaml'.format(pkg_name=pkg_name)

    def update_database(self):
        """
            For the current package, determine whether the specific yaml file exists, parse
            the data in it and save it in the database if it exists, and record the relevant
            log if it does not exist

        """
        if self._openeuler_advisor_exists_yaml():
            self._save_to_database()
        else:
            msg = "The yaml information of the %s package has not been\
                obtained yet" % self.pkg.name
            self.base.log.logger.warning(msg)

    def _get_yaml_content(self, url):
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
        self._get_yaml_content(self.openeuler_advisor_url)
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
        if self.timed_task_open:
            _maintainer = self._yaml_content.get('maintainer')
            if _maintainer and isinstance(_maintainer, list):
                self.pkg.maintainer = _maintainer[0]
            self.pkg.maintainlevel = self._yaml_content.get('maintainlevel')
        try:
            self.producer_consumer.put(copy.deepcopy(self.pkg))
            if self.timed_task_open and self.pkg.maintainer:
                @retry(stop_max_attempt_number=3, stop_max_delay=500)
                def _save_maintainer_info():
                    with DBHelper(db_name="lifecycle") as database:
                        _packages_maintainer = database.session.query(
                            PackagesMaintainer).filter(
                                PackagesMaintainer.name == self.pkg.name).first()
                        if _packages_maintainer:
                            _packages_maintainer.name = self.pkg.name
                            _packages_maintainer.maintainer = self.pkg.maintainer
                            _packages_maintainer.maintainlevel = self.pkg.maintainlevel
                        else:
                            _packages_maintainer = PackagesMaintainer(
                                name=self.pkg.name, maintainer=self.pkg.maintainer,
                                maintainlevel=self.pkg.maintainlevel)
                        self.producer_consumer.put(
                            copy.deepcopy(_packages_maintainer))
                _save_maintainer_info()
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
            _end_time = date.datetime.strptime(
                self.pkg.latest_version_time, '%Y-%m-%d')
            if self.pkg.latest_version != self.pkg.version:
                for _version in _tags:
                    if _version[1] == self.pkg.version:
                        _end_time = date.datetime.strptime(
                            _version[0], '%Y-%m-%d')
            self.pkg.used_time = (date.datetime.now() - _end_time).days

        except (IndexError, Error) as index_error:
            self.base.log.logger.error(index_error)


def update_pkg_info(pkg_info_update=True):
    """
        Update the information of the upstream warehouse in the source package

    """
    try:
        base_control = Base()
        _readconfig = ReadConfig(system_config.SYS_CONFIG_PATH)
        pool_workers = _readconfig.get_config('LIFECYCLE', 'pool_workers')
        _warehouse = _readconfig.get_config('LIFECYCLE', 'warehouse')
        if _warehouse is None:
            _warehouse = 'src-openeuler'
        if not isinstance(pool_workers, int):
            pool_workers = 10
        # Open thread pool
        pool = ThreadPoolExecutor(max_workers=pool_workers)
        with DBHelper(db_name="lifecycle") as database:
            for table_name in filter(lambda x: x not in ['packages_issue', 'PackagesMaintainer'],
                                     database.engine.table_names()):

                cls_model = Packages.package_meta(table_name)
                # Query a specific table
                for package_item in database.session.query(cls_model).all():
                    if pkg_info_update:
                        parse_yaml = ParseYaml(
                            pkg_info=copy.deepcopy(package_item),
                            base=base_control,
                            table_name=table_name)
                        pool.submit(parse_yaml.update_database)
                    else:
                        # Get the issue of each warehouse and save it
                        gitee_issue = Gitee(
                            package_item, _warehouse, package_item.name, table_name)
                        pool.submit(gitee_issue.query_issues_info)
        pool.shutdown()
    except SQLAlchemyError as error_msg:
        base_control.log.logger.error(error_msg)
