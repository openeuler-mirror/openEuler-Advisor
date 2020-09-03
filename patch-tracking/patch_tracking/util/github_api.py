"""
functionality of invoking GitHub API
"""
import time
import logging
import requests
from requests.exceptions import ConnectionError as requests_connectionError
from flask import current_app

logger = logging.getLogger(__name__)


def get_user_info(token):
    """
    get user info
    """
    url = "https://api.github.com/user"
    count = 30
    token = 'token ' + token
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Authorization': token,
        'Content-Type': 'application/json',
        'Connection': 'close',
        'method': 'GET',
        'Accept': 'application/json'
    }
    while count > 0:
        try:
            ret = requests.get(url, headers=headers)
            if ret.status_code == 200:
                return 'success', ret.text
            return 'error', ret.json()
        except requests_connectionError as err:
            logger.warning(err)
            time.sleep(10)
            count -= 1
            continue
    if count == 0:
        logger.error('Fail to connnect to github: %s after retry 30 times.', url)
        return 'connect error'


class GitHubApi:
    """
    Encapsulates GitHub functionality
    """
    def __init__(self):
        github_token = current_app.config['GITHUB_ACCESS_TOKEN']
        token = 'token ' + github_token
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Authorization': token,
            'Content-Type': 'application/json',
            'Connection': 'close',
            'method': 'GET',
            'Accept': 'application/json'
        }

    def api_request(self, url):
        """
        request GitHub API
        """
        logger.debug("Connect url: %s", url)
        count = 30
        while count > 0:
            try:
                response = requests.get(url, headers=self.headers)
                return response
            except requests_connectionError as err:
                logger.warning(err)
                time.sleep(10)
                count -= 1
                continue
        if count == 0:
            logger.error('Fail to connnect to github: %s after retry 30 times.', url)
            return 'connect error'

    def get_commit_info(self, repo_url, commit_id):
        """
        get commit info
        """
        res_dict = dict()
        api_url = 'https://api.github.com/repos'
        url = '/'.join([api_url, repo_url, 'commits', commit_id])
        ret = self.api_request(url)
        if ret != 'connect error':
            if ret.status_code == 200:
                res_dict['commit_id'] = commit_id
                res_dict['message'] = ret.json()['commit']['message']
                res_dict['time'] = ret.json()['commit']['author']['date']
                if 'parents' in ret.json() and ret.json()['parents']:
                    res_dict['parent'] = ret.json()['parents'][0]['sha']
                return 'success', res_dict

            logger.error('%s failed. Return val: %s', url, ret)
            return 'error', ret.json()
        return 'error', 'connect error'

    def get_latest_commit(self, repo_url, branch):
        """
        get latest commit_ID, commit_message, commit_date
        :param repo_url:
        :param branch:
        :return: res_dict
        """
        api_url = 'https://api.github.com/repos'
        url = '/'.join([api_url, repo_url, 'branches', branch])
        ret = self.api_request(url)
        res_dict = dict()
        if ret != 'connect error':
            if ret.status_code == 200:
                res_dict['latest_commit'] = ret.json()['commit']['sha']
                res_dict['message'] = ret.json()['commit']['commit']['message']
                res_dict['time'] = ret.json()['commit']['commit']['committer']['date']
                return 'success', res_dict

            logger.error('%s failed. Return val: %s', url, ret)
            return 'error', ret.json()

        return 'error', 'connect error'

    def get_patch(self, repo_url, scm_commit, last_commit):
        """
        get patch
        """
        api_url = 'https://github.com'
        if scm_commit != last_commit:
            commit = scm_commit + '...' + last_commit + '.diff'
        else:
            commit = scm_commit + '^...' + scm_commit + '.diff'
        ret_dict = dict()

        url = '/'.join([api_url, repo_url, 'compare', commit])
        ret = self.api_request(url)
        if ret != 'connect error':
            if ret.status_code == 200:
                patch_content = ret.text
                ret_dict['status'] = 'success'
                ret_dict['api_ret'] = patch_content
            else:
                logger.error('%s failed. Return val: %s', url, ret)
                ret_dict['status'] = 'error'
                ret_dict['api_ret'] = ret.text
        else:
            ret_dict['status'] = 'error'
            ret_dict['api_ret'] = 'fail to connect github by api.'

        return ret_dict
