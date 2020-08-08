#!/usr/bin/python3
import os
import json
import shutil
import tarfile
import requests
from multiprocessing.dummy import Pool

from packageship.libs.configutils.readconfig import ReadConfig
from packageship.libs.exception import Error
from .base import Base


class Gitee(Base):
    """
    gitee version management tool related information acquisition

    """

    def __init__(self, pkg_info, table_name, owner, repo):
        self.table_name = table_name
        self.pkg_info = pkg_info
        self.owner = owner
        self.repo = repo
        self._read_config = ReadConfig()
        self.url = "https://gitee.com/"
        self.api_url = "https://gitee.com/api/v5/repos"
        self.enterprise_url = "https://gitee.com/api/v5/enterprise/{}/pull_requests"
        self.pool = None
        self.issue_id = None
        self.patch_files_path = self._read_config.get_system(
            "patch_files_path")

    def query_issues_info(self, issue_id=""):
        """
        Description: View the issue details of the specified package
        Args:
             issue_id: Issue id
        Returns:
             issue_content_list: The issue details of the specified package list
        Raises:

        """
        issue_content_list = []
        issue_url = self.api_url + \
            "/{}/{}/issues/{}".format(self.owner, self.repo, issue_id)
        try:
            response = requests.get(
                issue_url, params={"state": "all", "per_page": 100})
        except Error as error:
            self.log.logger.error(error)
            return None
        if response.status_code != 200:
            self.log.logger.error(response.content.decode("utf-8"))
            return False
        total_page = int(response.headers['total_page'])
        issue_content = self.parse_issue_content(response.json())
        issue_content_list.extend(issue_content)
        if total_page > 1:
            for i in range(2, total_page + 1):
                response = requests.get(
                    issue_url, params={"state": "all", "per_page": 100, "page": i})
                issue_content_list.extend(
                    self.parse_issue_content(response.json()))
        return json.dumps(issue_content_list, ensure_ascii=False)

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
                           "related_release": source["labels"][0]['name'] if source["labels"] else None}
            if source["issue_type"] == "缺陷":
                self.pkg_info.defect = self.pkg_info.defect + 1 if self.pkg_info.defect else 1
            elif source["issue_type"] == "需求":
                self.pkg_info.demand = self.pkg_info.demand + 1 if self.pkg_info.demand else 1
            elif source["issue_type"] == "CVE和安全问题":
                self.pkg_info.cve = self.pkg_info.demand + 1 if self.pkg_info.demand else 1
            else:
                pass
        except KeyError as error:
            self.log.logger.error(error)
            return None
        return result_dict

    def get_url_list_from_operate_logs(self):
        """
        Description: Download patch
        Args:

        Returns:

        """
        link_list = []
        operate_logs_url = self.enterprise_url.format(self.owner)
        try:
            response = requests.get(operate_logs_url,
                                    params={"state": "all", "issue_number": "{}".format(self.issue_id)})
        except Error as error:
            self.log.logger.error(error)
            return None
        if response.status_code != 200:
            self.log.logger.error(response.content.decode("utf-8"))
            return False
        for content in response.json():
            # if "Pull Request" in content["content"]:
            #     issue_content_url = re.search(
            #         'href=\"([^# ]*)\"', content["content"]).group(1)
            link_list.append(content["diff_url"])
        return list(set(link_list))

    def get_issue_files(self, urls):
        """
        Description: Download the files associated with pr
        Args:
            urls: issue associates with pr url
        Returns:

        """
        # full_urls = []
        # for url in urls:
        #     full_urls.append(url)
        self.pool = Pool(5)
        issue_urls = self.pool.map(self.get_files_url, urls)
        dirname = os.path.join(
            self.patch_files_path, self.table_name, self.pkg_info.name, self.issue_id)
        if os.path.exists(dirname):
            shutil.rmtree(dirname, ignore_errors=True)
            os.makedirs(dirname, exist_ok=True)
        os.chdir(dirname)
        try:
            self.pool.map(self.download_issue_file, issue_urls)
        except Error as error:
            self.log.logger.error(error)
            return None
        self.pool.close()
        self.pool.join()
        # Do we need to pack the file?
        # return self.file_to_patch(dirname)
        return dirname

    def get_files_url(self, base_url):
        """
        Description: Download the files associated with pr
        Args:
            base_url: issue associates with pr url

        Returns:Get all file links in a given URL

        """
        try:
            file_content = requests.get(base_url).json()
        except Error as e:
            self.log.logger.error(e)
            return None
        if file_content.status_code != 200:
            self.log.logger.error(file_content.content.decode("utf-8"))
            return False
        urls = [url["raw_url"] for url in file_content]
        return urls

    def download_issue_file(self, url):
        """
        Description: Download issue file
        Args:
            url:

        Returns:

        """
        with open("{}.patch".format(self.issue_id), 'wb') as f:
            f.write(requests.get(url).text)

    def file_to_patch(self, sourcefile):
        """
        Description: Package folder, generate patch
        Args:
            sourcefile:
        Returns:patch_path

        """
        patch_path = os.path.join(
            self.patch_files_path, "{}_{}_{}.tar.gz".format(self.table_name, self.pkg_info.name, self.issue_id))
        if os.path.exists(patch_path):
            os.remove(patch_path)
        try:
            with tarfile.open(patch_path, "w:gz") as tar:
                tar.add(sourcefile, arcname=os.path.basename(
                    sourcefile))
        except IOError as error:
            self.log.logger.error(error)
        return patch_path

    def execute_request_content_save(self):
        """
        Description: Make a request for the url address, extract the issue content, and save the pr files associated
                    with the issue
        Args:

        Returns: issue_content_list

        """
        issue_content_list = []
        issue_contents = self.query_issues_info()
        for issue in issue_contents:
            self.issue_id = issue["issue_id"]
            issue_file_urls = self.get_url_list_from_operate_logs()
            issue_download = self.get_issue_files(issue_file_urls)
            issue["issue_download"] = issue_download
            issue_content_list.append(issue)
        return issue_content_list
