"""
tracking job
"""
import logging
import base64
import time
from patch_tracking.util.gitee_api import post_create_branch, post_upload_patch, post_create_issue, \
    post_create_pull_request, get_path_content, put_upload_spec, post_create_spec
from patch_tracking.util.github_api import GitHubApi
from patch_tracking.database.models import Tracking
from patch_tracking.api.business import update_tracking, create_issue
from patch_tracking.task import scheduler
from patch_tracking.util.spec import Spec

logger = logging.getLogger(__name__)


def get_track_from_db():
    """
    query all trackings from database
    """
    all_track = Tracking.query.filter_by(enabled=True)
    return all_track


def upload_patch_to_gitee(track):
    """
    upload a patch file to Gitee
    """
    cur_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    with scheduler.app.app_context():
        patch = get_scm_patch(track)
        if patch:
            issue = upload_patch(patch, cur_time)
            if issue:
                create_issue_db(issue)
            else:
                logger.debug('No issue need to create.')
        else:
            logger.debug('No new commit.')


def get_all_commit_info(scm_repo, db_commit, latest_commit):
    """
    get all commit information between to commits
    """
    commit_list = list()
    github_api = GitHubApi()

    while db_commit != latest_commit:
        status, result = github_api.get_commit_info(scm_repo, latest_commit)
        logger.debug('get_commit_info: %s %s', status, result)
        if status == 'success':
            if 'parent' in result:
                ret = github_api.get_patch(scm_repo, latest_commit, latest_commit)
                logger.debug('get patch api ret: %s', ret)
                if ret['status'] == 'success':
                    result['patch_content'] = ret['api_ret']
                    # inverted insert commit_list
                    commit_list.insert(0, result)
                else:
                    logger.error('Get scm: %s commit: %s patch failed. Result: %s', scm_repo, latest_commit, result)

                latest_commit = result['parent']
            else:
                logger.info('Successful get scm commit from %s to %s ID/message/time/patch.', db_commit, latest_commit)
                break
        else:
            logger.error('Get scm: %s commit: %s ID/message/time failed. Result: %s', scm_repo, latest_commit, result)

    return commit_list


def get_scm_patch(track):
    """
    Traverse the Tracking data table to get the patch file of enabled warehouse.
    Different warehouse has different acquisition methods
    :return:
    """
    scm_dict = dict()
    github_api = GitHubApi()

    scm_dict['scm_repo'] = track.scm_repo
    scm_dict['scm_branch'] = track.scm_branch
    scm_dict['scm_commit'] = track.scm_commit
    scm_dict['enabled'] = track.enabled
    scm_dict['repo'] = track.repo
    scm_dict['branch'] = track.branch
    scm_dict['version_control'] = track.version_control

    status, result = github_api.get_latest_commit(scm_dict['scm_repo'], scm_dict['scm_branch'])
    logger.debug('get_latest_commit: %s %s', status, result)

    if status == 'success':
        commit_id = result['latest_commit']
        if not scm_dict['scm_commit']:
            data = {
                'version_control': scm_dict['version_control'],
                'repo': scm_dict['repo'],
                'branch': scm_dict['branch'],
                'enabled': scm_dict['enabled'],
                'scm_commit': commit_id,
                'scm_branch': scm_dict['scm_branch'],
                'scm_repo': scm_dict['scm_repo']
            }
            update_tracking(data)
        else:
            if commit_id != scm_dict['scm_commit']:
                commit_list = get_all_commit_info(scm_dict['scm_repo'], scm_dict['scm_commit'], commit_id)
                scm_dict['commit_list'] = commit_list
                return scm_dict
            logger.info(
                'Latest commit id not change of scm_repo: %s scm_branch: %s. Nothing need to do.', scm_dict['scm_repo'],
                scm_dict['scm_branch']
            )
    else:
        logger.error(
            'Fail to get latest commit id of scm_repo: %s scm_branch: %s. Return val: %s', scm_dict['scm_repo'],
            scm_dict['scm_branch'], result
        )
    return None


def upload_patch(patch, cur_time):
    """
    Create temporary branches, submit files, and create PR and issue
    :return:
    """
    issue_dict = dict()
    if not patch:
        return None

    issue_dict['repo'] = patch['repo']
    issue_dict['branch'] = patch['branch']
    new_branch = 'patch-tracking/' + cur_time
    result = post_create_branch(patch['repo'], patch['branch'], new_branch)
    if result == 'success':
        logger.info('Successful create branch: %s', new_branch)
    else:
        logger.error('Fail to create branch: %s', new_branch)
    patch_lst = list()
    # 表格格式会导致 Gitee 敏感词，先去掉
    issue_table = ""
    for latest_commit in patch['commit_list']:
        scm_commit_url = '/'.join(['https://github.com', patch['scm_repo'], 'commit', latest_commit['commit_id']])
        issue_table += '[{}]({}) | {} | {}'.format(
            latest_commit['commit_id'][0:7], scm_commit_url, latest_commit['time'], latest_commit['message']
        ) + '\n'
        patch_file_content = latest_commit['patch_content']

        post_data = {
            'repo': patch['repo'],
            'branch': new_branch,
            'latest_commit_id': latest_commit['commit_id'],
            'patch_file_content': str(patch_file_content),
            'cur_time': cur_time,
            'commit_url': scm_commit_url
        }
        result = post_upload_patch(post_data)
        if result == 'success':
            logger.info('Successfully upload patch file of commit: %s', latest_commit['commit_id'])
        else:
            logger.error('Fail to upload patch file of commit: %s', latest_commit['commit_id'])
        patch_lst.append(str(latest_commit['commit_id']))

    logger.debug(issue_table)
    result = post_create_issue(patch['repo'], issue_table, cur_time)
    if result[0] == 'success':
        issue_num = result[1]
        logger.info('Successfully create issue: %s', issue_num)
        ret = post_create_pull_request(patch['repo'], patch['branch'], new_branch, issue_num, cur_time)
        if ret == 'success':
            logger.info('Successfully create PR of issue: %s.', issue_num)
        else:
            logger.error('Fail to create PR of issue: %s. Result: %s', issue_num, ret)
        issue_dict['issue'] = issue_num

        upload_spec(patch, patch_lst, cur_time)

        data = {
            'version_control': patch['version_control'],
            'repo': patch['repo'],
            'branch': patch['branch'],
            'enabled': patch['enabled'],
            'scm_commit': patch['commit_list'][-1]['commit_id'],
            'scm_branch': patch['scm_branch'],
            'scm_repo': patch['scm_repo']
        }
        update_tracking(data)
    else:
        logger.error('Fail to create issue: %s. Result: %s', issue_table, result[1])

    return issue_dict


def upload_spec(patch, patch_lst, cur_time):
    """
    update and upload spec file
    """
    new_branch = 'patch-tracking/' + cur_time

    _, repo_name = patch['repo'].split('/')
    spec_file = repo_name + '.spec'

    patch_file_lst = [patch + '.patch' for patch in patch_lst]

    log_title = "{} patch-tracking".format(cur_time)
    log_content = "append patch file of upstream repository from <{}> to <{}>".format(patch_lst[0], patch_lst[-1])

    ret = get_path_content(patch['repo'], patch['branch'], spec_file)
    if 'content' in ret:
        spec_content = str(base64.b64decode(ret['content']), encoding='utf-8')
        spec_sha = ret['sha']
        new_spec = modify_spec(log_title, log_content, patch_file_lst, spec_content)
        update_spec(patch['repo'], new_branch, cur_time, new_spec, spec_sha)
    else:
        if 'message' in ret and 'File Not Found' in ret['message']:
            spec_content = ''
            new_spec = modify_spec(log_title, log_content, patch_file_lst, spec_content)
            create_spec(patch['repo'], new_branch, cur_time, new_spec)
        else:
            logger.error('Fail to update spec: %s. Result: %s', spec_file, ret)


def modify_spec(log_title, log_content, patch_file_lst, spec_content):
    """
    modify spec file
    """
    spec = Spec(spec_content)
    return spec.update(log_title, log_content, patch_file_lst)


def update_spec(repo, branch, cur_time, spec_content, spec_sha):
    """
    update spec file
    """
    ret = put_upload_spec(repo, branch, cur_time, spec_content, spec_sha)
    if ret == 'success':
        logger.info('Successfully update spec file.')
    else:
        logger.error('Fail to update spec file. Result: %s', ret)


def create_spec(repo, branch, cur_time, spec_content):
    """
    create new spec file
    """
    ret = post_create_spec(repo, branch, spec_content, cur_time)
    if ret == 'success':
        logger.info('Successfully create spec file.')
    else:
        logger.error('Fail to create spec file. Result: %s', ret)


def create_issue_db(issue):
    """
    create issue into database
    """
    issue_num = issue['issue']
    tracking = Tracking.query.filter_by(repo=issue['repo'], branch=issue['branch']).first()
    tracking_repo = tracking.repo
    tracking_branch = tracking.branch
    data = {'issue': issue_num, 'repo': tracking_repo, 'branch': tracking_branch}
    logger.debug('issue data: %s', data)
    create_issue(data)
