"""
function of invoking Gitee API
"""
import base64
import logging
import requests
from flask import current_app
from requests import exceptions

logger = logging.getLogger(__name__)

ORG_URL = "https://gitee.com/api/v5/orgs"
REPO_URL = "https://gitee.com/api/v5/repos"


def get_request(url, params):
    """
    get request
    """
    logger.debug("Get request, connect url: %s", url)
    try:
        response = requests.get(url, params=params)
        return True, response
    except exceptions.ConnectionError as err:
        logger.error(err)
        return False, 'connection error'
    except IOError as err:
        logger.error(err)
        return False, 'IO error'


def post_request(url, data):
    """
    post request
    """
    logger.debug("Post request, connect url: %s", url)
    try:
        response = requests.post(url, data=data)
        return True, response
    except exceptions.ConnectionError as err:
        logger.error(err)
        return False, 'connection error'
    except IOError as err:
        logger.error(err)
        return False, 'IO error'


def put_request(url, data):
    """
    put request
    """
    logger.debug("Put request, connect url: %s", url)
    try:
        response = requests.put(url, data=data)
        return True, response
    except exceptions.ConnectionError as err:
        logger.error(err)
        return False, 'connection error'
    except IOError as err:
        logger.error(err)
        return False, 'IO error'


def get_user_info(token):
    """
    get user info
    """
    url = "https://gitee.com/api/v5/user"
    gitee_token = token
    param = {'access_token': gitee_token}
    ret, ret_info = get_request(url, params=param)
    if ret:
        if ret_info.status_code == 200:
            return True, ret_info.text
        return False, ret_info.json()

    return False, ret_info


def get_path_content(repo, branch, path):
    """
    get file content
    """
    gitee_token = current_app.config['GITEE_ACCESS_TOKEN']
    url = '/'.join([REPO_URL, repo, 'contents', path])
    param = {'access_token': gitee_token, 'ref': branch}
    _, ret_info = get_request(url, params=param)
    return ret_info.json()


def create_branch(repo, branch, new_branch):
    """
    create branch
    """
    gitee_token = current_app.config['GITEE_ACCESS_TOKEN']
    url = '/'.join([REPO_URL, repo, 'branches'])
    data = {'access_token': gitee_token, 'refs': branch, 'branch_name': new_branch}
    ret, response = post_request(url, data=data)
    if ret:
        if response.status_code == 201:
            return 'success'
        return response.json()

    return response


def upload_patch(data):
    """
    upload patch
    """
    gitee_token = current_app.config['GITEE_ACCESS_TOKEN']
    patch_file_name = data['latest_commit_id'] + '.patch'
    url = '/'.join([REPO_URL, data['repo'], 'contents', patch_file_name])
    content = base64.b64encode(data['patch_file_content'].encode("utf-8"))
    message = '[patch tracking] ' + data['cur_time'] + ' - ' + data['commit_url'] + '\n'
    data = {'access_token': gitee_token, 'content': content, 'message': message, 'branch': data['branch']}
    ret, response = post_request(url, data=data)
    if ret:
        if response.status_code == 201:
            return 'success'
        return response.json()

    return response


def create_spec(repo, branch, spec_content, cur_time):
    """
    create spec
    """
    gitee_token = current_app.config['GITEE_ACCESS_TOKEN']
    owner, repo = repo.split('/')
    spec_file_name = repo + '.spec'
    url = '/'.join([REPO_URL, owner, repo, 'contents', spec_file_name])
    content = base64.b64encode(spec_content.encode("utf-8"))
    message = '[patch tracking] ' + cur_time + ' - ' + 'create spec file' + '\n'
    data = {'access_token': gitee_token, 'content': content, 'message': message, 'branch': branch}
    ret, response = post_request(url, data=data)
    if ret:
        if response.status_code == 201:
            return 'success'
        return response.json()

    return response


def upload_spec(repo, branch, cur_time, spec_content, spec_sha):
    """
    upload spec
    """
    gitee_token = current_app.config['GITEE_ACCESS_TOKEN']
    owner, repo = repo.split('/')
    spec_file_name = repo + '.spec'
    url = '/'.join([REPO_URL, owner, repo, 'contents', spec_file_name])
    content = base64.b64encode(spec_content.encode("utf-8"))
    message = '[patch tracking] ' + cur_time + ' - ' + 'update spec file' + '\n'
    data = {
        'access_token': gitee_token,
        'owner': owner,
        'repo': repo,
        'path': spec_file_name,
        'content': content,
        'message': message,
        'branch': branch,
        'sha': spec_sha
    }
    ret, response = put_request(url, data=data)
    if ret:
        if response.status_code == 200:
            return 'success'
        return response.json()

    return response


def create_gitee_issue(repo, branch, issue_body, cur_time):
    """
    create issue
    """
    gitee_token = current_app.config['GITEE_ACCESS_TOKEN']
    owner, repo = repo.split('/')
    url = '/'.join([REPO_URL, owner, 'issues'])
    data = {
        'access_token': gitee_token,
        'repo': repo,
        'title': '[patch tracking] ' + branch + ' ' + cur_time,
        'body': issue_body
    }
    ret, response = post_request(url, data=data)
    if ret:
        if response.status_code == 201:
            return 'success', response.json()['number']
        return 'error', response.json()

    return 'error', response


def create_pull_request(repo, branch, patch_branch, issue_num, cur_time):
    """
    create pull request
    """
    gitee_token = current_app.config['GITEE_ACCESS_TOKEN']
    owner, repo = repo.split('/')
    url = '/'.join([REPO_URL, owner, repo, 'pulls'])
    data = {
        'access_token': gitee_token,
        'repo': repo,
        'title': '[patch tracking] ' + cur_time,
        'head': patch_branch,
        'base': branch,
        'body': '#' + issue_num,
        "prune_source_branch": "true"
    }
    ret, response = post_request(url, data=data)
    if ret:
        if response.status_code == 201:
            return 'success'
        return response.json()

    return response
