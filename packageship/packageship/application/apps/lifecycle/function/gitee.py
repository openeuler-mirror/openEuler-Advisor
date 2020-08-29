#!/usr/bin/python3
"""
Description:Get issue info from gitee
Class: Gitee
"""
import copy
from json import JSONDecodeError
from retrying import retry
import requests
from requests.exceptions import HTTPError
from sqlalchemy.exc import SQLAlchemyError
from packageship.libs.dbutils import DBHelper
from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.exception import Error, ContentNoneException
from packageship.application.models.package import PackagesIssue
from packageship import system_config
from packageship.libs.log import Log
from .concurrent import ProducerConsumer

LOGGER = Log(__name__)


class Gitee():
    """
    gitee version management tool related information acquisition

    """

    def __init__(self, pkg_info, owner, repo, table_name):
        self.pkg_info = pkg_info
        self.owner = owner
        self.repo = repo
        self._read_config = ReadConfig(system_config.SYS_CONFIG_PATH)
        self.url = "https://gitee.com/"
        self.api_url = "https://gitee.com/api/v5/repos"
        self.pool = None
        self.issue_id = None
        self.defect = 0
        self.feature = 0
        self.cve = 0
        self.patch_files_path = self._read_config.get_system(
            "patch_files_path")
        self.table_name = table_name
        self.producer_consumer = ProducerConsumer()

    def query_issues_info(self, issue_id=""):
        """
        Description: View the issue details of the specified package
        Args:
             issue_id: Issue id
        Returns:
             issue_content_list: The issue details of the specified package list
        Raises:

        """
        issue_url = self.api_url + \
                    "/{}/{}/issues/{}".format(self.owner, self.repo, issue_id)
        try:
            response = requests.get(
                issue_url, params={"state": "all", "per_page": 100})
        except Error as error:
            LOGGER.logger.error(error)
            return None
        if response.status_code != 200:
            return None
        total_page = 1 if issue_id else int(response.headers['total_page'])
        total_count = int(response.headers['total_count'])
        if total_count > 0:
            issue_list = self._query_per_page_issue_info(total_page, issue_url)
            if not issue_list:
                LOGGER.logger.error(
                    "An error occurred while querying {}".format(self.repo))
                return None
            self._save_issues(issue_list)

    def _query_per_page_issue_info(self, total_page, issue_url):
        """
        Description: View the issue details
        Args:
            total_page: total page
            issue_url: issue url

        Returns:

        """
        issue_content_list = []
        for i in range(1, total_page + 1):

            @retry(stop_max_attempt_number=3, stop_max_delay=1000)
            def request_issue(page, issue_url):
                try:
                    response = requests.get(issue_url,
                                            params={"state": "all", "per_page": 100, "page": page})
                except HTTPError:
                    raise HTTPError('Network request error')
                return response

            try:
                response = request_issue(i, issue_url)
                if response.status_code != 200:
                    LOGGER.logger.warning(response.content.decode("utf-8"))
                    continue
                issue_content_list.extend(
                    self.parse_issues_content(response.json()))
            except (JSONDecodeError, Error) as error:
                LOGGER.logger.error(error)
        return issue_content_list

    def _save_issues(self, issue_list):
        """
            Save the obtained issue information

        """
        try:
            issue_ids = [issue['issue_id'] for issue in issue_list]
            with DBHelper(db_name="lifecycle") as database:

                @retry(stop_max_attempt_number=3, stop_max_delay=500)
                def _query_pkgissues():
                    exist_issues = database.session.query(PackagesIssue).filter(
                        PackagesIssue.issue_id.in_(issue_ids)).all()  # pylint: disable=protected-access
                    return exist_issues

                exist_issues = _query_pkgissues()
                # Save the issue
                for issue_item in issue_list:
                    issue_model = [
                        issue for issue in exist_issues if issue.issue_id == issue_item['issue_id']]
                    if issue_model:
                        for key, val in issue_item.items():
                            setattr(issue_model[0], key, val)
                        self.producer_consumer.put(
                            copy.deepcopy(issue_model[0]))
                    else:
                        self.producer_consumer.put(
                            PackagesIssue(**issue_item))

                # The number of various issues in the update package
                self.pkg_info.defect = self.defect
                self.pkg_info.feature = self.feature
                self.pkg_info.cve = self.cve
                self.producer_consumer.put(copy.deepcopy(self.pkg_info))

        except (Error, ContentNoneException, SQLAlchemyError) as error:
            LOGGER.logger.error(
                'An abnormal error occurred while saving related issues:%s' % error if error else '')

    def parse_issues_content(self, sources):
        """
        Description: Parse the response content and get issue content
        Args:Issue list

        Returns:list:issue_id, issue_url, issue_content, issue_status, issue_download
        Raises:
        """
        result_list = []
        if isinstance(sources, list):
            for source in sources:
                issue_content = self.parse_issue_content(source)
                if issue_content:
                    result_list.append(issue_content)
        else:
            issue_content = self.parse_issue_content(sources)
            if issue_content:
                result_list.append(issue_content)
        return result_list

    def parse_issue_content(self, source):
        """
        Description: Parse the response content and get issue content
        Args: Source of issue content

        Returns:list:issue_id, issue_url, issue_content, issue_status, issue_download, issue_status
                issue_type, related_release
        Raises:KeyError
        """
        try:
            result_dict = {"issue_id": source['number'], "issue_url": source['html_url'],
                           "issue_title": source['title'].strip(),
                           "issue_content": source['body'].strip(),
                           "issue_status": source['state'], "issue_download": "",
                           "issue_type": source["issue_type"],
                           "pkg_name": self.repo,
                           "related_release": source["labels"][0]['name'] if source["labels"] else ''}
            if source["issue_type"] == "缺陷":
                self.defect += 1
            elif source["issue_type"] == "需求":
                self.feature += 1
            elif source["issue_type"] == "CVE和安全问题":
                self.cve += 1
            else:
                pass
        except KeyError as error:
            LOGGER.logger.error(error)
            return None
        return result_dict

    def issue_hooks(self, issue_hook_info):
        """
        Description: Hook data triggered by a new task operation
        Args:
             issue_hook_info: Issue info
        Returns:

        Raises:

        """
        if issue_hook_info is None:
            raise ContentNoneException(
                'The content cannot be empty')
        issue_info_list = []
        issue_info = issue_hook_info["issue"]
        issue_content = self.parse_issue_content(issue_info)
        if issue_content:
            issue_info_list.append(issue_content)
        if self.feature != 0:
            self.defect, self.feature, self.cve = self.pkg_info.defect, self.pkg_info.feature + \
                                                  1, self.pkg_info.cve
        if self.defect != 0:
            self.defect, self.feature, self.cve = self.pkg_info.defect + \
                                                  1, self.pkg_info.feature, self.pkg_info.cve
        if self.cve != 0:
            self.defect, self.feature, self.cve = self.pkg_info.defect, self.pkg_info.feature, self.pkg_info.cve + 1
        self._save_issues(issue_info_list)
