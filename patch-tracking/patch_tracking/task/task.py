"""
load job/task of tracking
"""
import datetime
import logging
from patch_tracking.task import scheduler
from patch_tracking.database.models import Tracking
from patch_tracking.util.github_api import GitHubApi
from patch_tracking.api.business import update_tracking

logger = logging.getLogger(__name__)


def init(app):
    """
    scheduler jobs init
    """
    scan_db_interval = app.config['SCAN_DB_INTERVAL']
    scheduler.init_app(app)
    scheduler.add_job(
        id='Add Tracking job - Update DB',
        func=patch_tracking_task,
        trigger='interval',
        args=(app, ),
        seconds=int(scan_db_interval),
        next_run_time=datetime.datetime.now()
    )

    scheduler.add_job(
        id=str("Check empty commitID"),
        func=check_empty_commit_id,
        trigger='interval',
        args=(app, ),
        seconds=600,
        next_run_time=datetime.datetime.now(),
        misfire_grace_time=300,
    )

    scheduler.start()


def add_job(job_id, func, args):
    """
    add job
    """
    logger.info("Add Tracking job - %s", job_id)
    scheduler.add_job(
        id=job_id, func=func, args=args, trigger='date', run_date=datetime.datetime.now(), misfire_grace_time=600
    )


def check_empty_commit_id(flask_app):
    """
    check commit ID for empty tracking
    """
    with flask_app.app_context():
        new_track = get_track_from_db()
        github_api = GitHubApi()
        for item in new_track:
            if item.scm_commit:
                continue
            status, result = github_api.get_latest_commit(item.scm_repo, item.scm_branch)
            if status == 'success':
                commit_id = result['latest_commit']
                data = {
                    'version_control': item.version_control,
                    'repo': item.repo,
                    'branch': item.branch,
                    'enabled': item.enabled,
                    'scm_commit': commit_id,
                    'scm_branch': item.scm_branch,
                    'scm_repo': item.scm_repo
                }
                update_tracking(data)
            else:
                logger.error(
                    'Check empty CommitID: Fail to get latest commit id of scm_repo: %s scm_branch: %s. Return val: %s',
                    item.scm_repo, item.scm_branch, result
                )


def get_track_from_db():
    """
    query all trackings from database
    """
    all_track = Tracking.query.filter_by(enabled=True)
    return all_track


def patch_tracking_task(flask_app):
    """
    add patch trackings to jobs
    """
    with flask_app.app_context():
        all_track = get_track_from_db()
        all_job_id = list()
        for item in scheduler.get_jobs():
            all_job_id.append(item.id)
        for track in all_track:
            if track.branch.split('/')[0] != 'patch-tracking':
                job_id = str(track.repo + ":" + track.branch)
                if job_id not in all_job_id:
                    add_job(
                        job_id=job_id,
                        func='patch_tracking.task.task_apscheduler:upload_patch_to_gitee',
                        args=(track, )
                    )
